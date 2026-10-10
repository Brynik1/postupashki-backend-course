import re
import sys

CRLF = b"\r\n"
TOKEN_RE = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
DIGITS_RE = re.compile(r"[0-9]+")


class HTTPParseError(ValueError):
    pass


def fail(reason):
    raise HTTPParseError(reason)


def valid_field_value(value):
    return all((ord(c) >= 32 and ord(c) != 127) or c == "\t" for c in value)


def next_crlf(data, pos, reason):
    idx = data.find(CRLF, pos)
    if idx == -1:
        fail(reason)
    return idx


def parse_start(line):
    tokens = line.split(" ")
    if tokens[0] == "HTTP/1.1":
        if len(tokens) < 2 or not re.fullmatch(r"[0-9]{3}", tokens[1]):
            fail("bad_start_line")
        reason = " ".join(tokens[2:])
        if not valid_field_value(reason):
            fail("bad_start_line")
        return "response", None, None, tokens[1], reason
    if len(tokens) == 3 and tokens[2] == "HTTP/1.1":
        if not TOKEN_RE.fullmatch(tokens[0]) or not tokens[1] \
                or any(ord(c) <= 32 or ord(c) == 127 for c in tokens[1]):
            fail("bad_start_line")
        return "request", tokens[0], tokens[1], None, None
    fail("bad_start_line")


def parse_headers(data, pos):
    """Читает поля заголовка до пустой строки; возвращает (пары, смещение тела)"""
    headers = []
    while True:
        end = next_crlf(data, pos, "bad_header")
        line = data[pos:end].decode("latin-1")
        pos = end + 2
        if line == "":
            return headers, pos
        colon = line.find(":")
        if colon <= 0:
            fail("bad_header")
        name = line[:colon]
        if not TOKEN_RE.fullmatch(name):
            fail("bad_header")
        value = line[colon + 1:].strip(" \t")
        if name.lower() == "content-length" and not DIGITS_RE.fullmatch(value):
            fail("bad_header")
        if not valid_field_value(value):
            fail("bad_header")
        headers.append((name.lower(), value))


def chunk_size(line):
    size, separator, _ = line.partition(";")
    if separator:
        size = size.rstrip(" \t")
    if not re.fullmatch(r"[0-9A-Fa-f]+", size):
        fail("bad_chunk")
    return int(size, 16)


def read_chunked(data, pos):
    """Собирает тело, переданное по частям; возвращает тело"""
    body = bytearray()
    while True:
        end = next_crlf(data, pos, "bad_chunk")
        size = chunk_size(data[pos:end].decode("latin-1"))
        pos = end + 2
        if size == 0:
            # после нулевой части могут идти поля концевика - читаем строки до пустой
            while True:
                end = next_crlf(data, pos, "bad_chunk")
                line = data[pos:end].decode("latin-1")
                pos = end + 2
                if line == "":
                    break
            return bytes(body)
        if pos + size > len(data):
            fail("bad_chunk")
        body.extend(data[pos:pos + size])
        pos += size
        if data[pos:pos + 2] != CRLF:
            fail("bad_chunk")
        pos += 2


def is_chunked(headers):
    values = [value for name, value in headers if name == "transfer-encoding"]
    return bool(values) and ",".join(values).lower().split(",")[-1].strip(" \t") == "chunked"


def content_length(headers):
    seen = None
    for name, value in headers:
        if name != "content-length":
            continue
        # Сравниваем десятичные значения, включая записи с ведущими нулями.
        number = 0
        for digit in value:
            number = number * 10 + ord(digit) - ord("0")
        if seen is not None and seen != number:
            fail("bad_header")
        seen = number
    return seen


def read_body(data, pos, headers):
    length = content_length(headers)
    if is_chunked(headers):
        return read_chunked(data, pos)
    if length is None:
        return b""
    if len(data) - pos < length:
        fail("incomplete_body")
    return data[pos:pos + length]


def printable(text):
    return all(0x20 <= b <= 0x7E for b in text)


def main():
    data = sys.stdin.buffer.read()
    start_end = next_crlf(data, 0, "bad_start_line")
    start_line = data[:start_end].decode("latin-1")
    kind, method, target, status, reason = parse_start(start_line)

    headers, pos = parse_headers(data, start_end + 2)
    body = read_body(data, pos, headers)

    out = ["type %s" % kind]
    if kind == "request":
        out.append("method %s" % method)
        out.append("target %s" % target)
    else:
        out.append("status %s" % status)
        if reason:
            out.append("reason %s" % reason)
        else:
            out.append("reason")
    out.append("version HTTP/1.1")
    for name, value in headers:
        out.append("header %s %s" % (name, value))
    out.append("body.length %d" % len(body))
    if body and printable(body):
        out.append("body.text %s" % body.decode("latin-1"))
    print("\n".join(out))


if __name__ == "__main__":
    try:
        main()
    except HTTPParseError as err:
        print("error %s" % err)
        sys.exit(1)
