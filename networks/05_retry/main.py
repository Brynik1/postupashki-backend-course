import argparse
import queue
import threading
import random
import re
import socket
import sys
import time
from urllib.parse import urlsplit

BASE_MS = 200
FACTOR = 2
CAP_MS = 2000
ATTEMPT_TIMEOUT_S = 5.0

RETRYABLE = {429, 500, 502, 503, 504}
IDEMPOTENT = set("GET HEAD PUT DELETE OPTIONS TRACE".split())


TOKEN_RE = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
DIGITS_RE = re.compile(r"[0-9]+")


class HTTPParseError(ValueError):
    pass


def valid_field_value(value):
    return all((ord(c) >= 32 and ord(c) != 127) or c == "\t" for c in value)


def content_length(headers):
    values = [value.lstrip("0") or "0" for name, value in headers if name == "content-length"]
    if not values:
        return None
    if any(value != values[0] for value in values):
        raise HTTPParseError("conflicting Content-Length")
    number = 0
    for digit in values[0]:
        number = number * 10 + ord(digit) - ord("0")
    return number


def is_chunked(headers):
    values = [value for name, value in headers if name == "transfer-encoding"]
    return bool(values) and ",".join(values).lower().split(",")[-1].strip(" \t") == "chunked"


def chunk_size(line):
    size, separator, _ = line.partition(";")
    if separator:
        size = size.rstrip(" \t")
    if not re.fullmatch(r"[0-9A-Fa-f]+", size):
        raise HTTPParseError("bad_chunk")
    return int(size, 16)


def parse_url(raw):
    try:
        if any(ord(c) <= 32 or ord(c) == 127 for c in raw):
            raise ValueError("URL содержит пробелы или управляющие символы")
        parts = urlsplit(raw)
        if parts.scheme.lower() != "http":
            raise ValueError("поддерживается только http")
        host = parts.hostname
        port = 80 if parts.port is None else parts.port
        if not host or not 1 <= port <= 65535:
            raise ValueError("нужны непустой хост и порт 1..65535")
        if parts.username is not None or parts.password is not None:
            raise ValueError("данные авторизации в URL не поддерживаются")
        host = host.encode("idna").decode("ascii")
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        path.encode("ascii")
        return host, port, path
    except ValueError as err:
        sys.exit("bad url %r: %s" % (raw, err))


def remaining(deadline):
    left = deadline - time.monotonic()
    if left <= 0:
        raise socket.timeout("attempt deadline exceeded")
    return left


def connect(host, port, deadline):
    # Системное разрешение имени не имеет socket timeout: ограничиваем и его.
    resolved = queue.Queue(maxsize=1)

    def resolve():
        try:
            resolved.put(socket.getaddrinfo(host, port, type=socket.SOCK_STREAM))
        except OSError as err:
            resolved.put(err)

    threading.Thread(target=resolve, daemon=True).start()
    try:
        addresses = resolved.get(timeout=remaining(deadline))
    except queue.Empty:
        raise socket.timeout("name resolution deadline exceeded") from None
    if isinstance(addresses, OSError):
        raise addresses
    error = OSError("no addresses for host")
    for family, socktype, protocol, _, address in addresses:
        sock = socket.socket(family, socktype, protocol)
        try:
            sock.settimeout(remaining(deadline))
            sock.connect(address)
            return sock
        except OSError as err:
            error = err
            sock.close()
    raise error


class ResponseReader:
    """Читает ответ по границам HTTP с единым дедлайном на всю попытку."""

    def __init__(self, sock, deadline):
        self.sock = sock
        self.deadline = deadline
        self.buffer = bytearray()

    def receive(self):
        self.sock.settimeout(remaining(self.deadline))
        data = self.sock.recv(65536)
        self.buffer.extend(data)
        return bool(data)

    def line(self):
        start = 0
        while True:
            remaining(self.deadline)
            end = self.buffer.find(b"\r\n", start)
            if end >= 0:
                line = bytes(self.buffer[:end])
                del self.buffer[:end + 2]
                return line
            start = max(0, len(self.buffer) - 1)
            if not self.receive():
                raise OSError("connection closed inside HTTP line")

    def discard(self, length):
        while length:
            remaining(self.deadline)
            if not self.buffer and not self.receive():
                raise OSError("connection closed inside HTTP body")
            count = min(length, len(self.buffer))
            del self.buffer[:count]
            length -= count

    def body(self, headers, method, status):
        length = content_length(headers)
        if method == "HEAD" or status in (204, 304):
            return
        if is_chunked(headers):
            while True:
                size = chunk_size(self.line().decode("latin-1"))
                if size == 0:
                    while self.line():
                        pass  # концевики не влияют на статус ответа
                    return
                self.discard(size)
                # После байтов части должна идти ровно одна последовательность CRLF.
                if self.line() != b"":
                    raise HTTPParseError("bad_chunk")
        elif length is not None:
            self.discard(length)
        else:
            # В сетевом ответе без framing тело заканчивается закрытием соединения.
            self.buffer.clear()
            while self.receive():
                self.buffer.clear()

    def response(self, method):
        while True:
            tokens = self.line().decode("latin-1").split(" ", 2)
            if len(tokens) < 2 or tokens[0] not in ("HTTP/1.0", "HTTP/1.1") \
                    or not re.fullmatch(r"[0-9]{3}", tokens[1]) \
                    or len(tokens) == 3 and not valid_field_value(tokens[2]):
                raise HTTPParseError("bad_start_line")
            status = int(tokens[1])
            headers = []
            while True:
                line = self.line().decode("latin-1")
                if not line:
                    break
                name, separator, value = line.partition(":")
                value = value.strip(" \t")
                if not separator or not TOKEN_RE.fullmatch(name) or not valid_field_value(value):
                    raise HTTPParseError("bad_header")
                if name.lower() == "content-length" and not DIGITS_RE.fullmatch(value):
                    raise HTTPParseError("bad_header")
                headers.append((name.lower(), value))
            if 100 <= status < 200:
                if status == 101:
                    raise HTTPParseError("unsupported protocol upgrade")
                continue
            self.body(headers, method, status)
            remaining(self.deadline)
            retry_after = next((value for name, value in headers if name == "retry-after"), None)
            return status, retry_after


def pause_ms(attempt_number, retry_after):
    """Пауза перед следующей попыткой; Retry-After перекрывает расчет и разброс"""
    if retry_after is not None:
        try:
            text = str(retry_after).strip(" \t")
            seconds = int(text) if DIGITS_RE.fullmatch(text) else None
        except ValueError:
            seconds = None  # форма с датой не разбирается
        if seconds is not None:
            return max(0, seconds * 1000)
    ceiling = min(CAP_MS, BASE_MS * FACTOR ** min(attempt_number - 1, 4))
    return random.randint(0, ceiling)


class Attempt:
    """Одна попытка запроса: статус-код и значение Retry-After, либо ошибка соединения"""

    def __init__(self, host, port, path, method, headers):
        self.host, self.port, self.path = host, port, path
        self.method, self.headers = method, headers

    def run(self):
        deadline = time.monotonic() + ATTEMPT_TIMEOUT_S
        try:
            with connect(self.host, self.port, deadline) as sock:
                host_header = "[%s]" % self.host if ":" in self.host else self.host
                if self.port != 80:
                    host_header += ":%d" % self.port
                lines = ["%s %s HTTP/1.1" % (self.method, self.path),
                         "Host: %s" % host_header, "Connection: close", "Content-Length: 0"]
                lines.extend("%s: %s" % pair for pair in self.headers.items())
                request = ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")
                sock.settimeout(remaining(deadline))
                sock.sendall(request)
                status, retry_after = ResponseReader(sock, deadline).response(self.method)
                return status, retry_after, None
        except socket.timeout:
            return None, None, "timed out waiting for response"
        except HTTPParseError as err:
            return None, None, "http error: %s" % err
        except OSError as err:
            return None, None, "connection error: %s" % err


def main():
    def at_least_one(text):
        n = int(text)
        if n < 1:
            raise argparse.ArgumentTypeError("нужно целое >= 1, получено %r" % text)
        return n

    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--max-attempts", type=at_least_one, default=5)
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    method = args.method.upper()  # методы в HTTP регистрозависимы, нормализуем один раз
    if not TOKEN_RE.fullmatch(method):
        parser.error("неверный метод HTTP")
    if args.idempotency_key is not None:
        if any(ord(c) < 32 or 127 <= ord(c) <= 159 or ord(c) > 255 for c in args.idempotency_key):
            parser.error("ключ идемпотентности содержит управляющие или непередаваемые символы")
    host, port, path = parse_url(args.url)

    headers = {}
    if args.idempotency_key is not None:
        headers["Idempotency-Key"] = args.idempotency_key

    # POST не идемпотентен: повторяется только с заданным ключом
    may_retry = method in IDEMPOTENT or args.idempotency_key is not None

    code = 1
    attempts_done = 0
    for number in range(1, args.max_attempts + 1):
        status, retry_after, error = Attempt(host, port, path, method, headers).run()
        attempts_done = number

        if status is None:
            print("attempt %d error %s" % (number, error), flush=True)
        else:
            print("attempt %d status %d" % (number, status), flush=True)

        if status is not None and 200 <= status <= 399:
            code = 0
            break
        if status is not None and status not in RETRYABLE:
            code = 1
            break
        if not may_retry:
            code = 1
            break
        if attempts_done >= args.max_attempts:
            code = 1
            break

        pause = pause_ms(number + 1, retry_after)
        print("sleep_ms %d" % pause, flush=True)
        time.sleep(pause / 1000.0)

    print("result %s attempts %d" % ("success" if code == 0 else "failure", attempts_done))
    sys.exit(code)


if __name__ == "__main__":
    main()
