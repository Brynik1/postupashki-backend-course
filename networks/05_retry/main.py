import argparse
import http.client
import random
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


def pause_ms(attempt_number, retry_after):
    """Пауза перед следующей попыткой; Retry-After перекрывает расчет и разброс"""
    if retry_after is not None:
        try:
            seconds = int(str(retry_after).strip())
        except ValueError:
            seconds = None  # форма с датой не разбирается
        if seconds is not None:
            return max(0, seconds * 1000)
    ceiling = min(CAP_MS, BASE_MS * FACTOR ** (attempt_number - 1))
    return random.randint(0, ceiling)


class Attempt:
    """Одна попытка запроса: статус-код и значение Retry-After, либо ошибка соединения"""

    def __init__(self, url, method, headers):
        parts = urlsplit(url)
        self.host = parts.hostname or ""
        self.port = parts.port or 80
        self.path = parts.path or "/"
        if parts.query:
            self.path += "?" + parts.query
        self.method, self.headers = method, headers

    def run(self):
        conn = http.client.HTTPConnection(self.host, self.port, timeout=ATTEMPT_TIMEOUT_S)
        try:
            conn.request(self.method, self.path, headers=self.headers)
            response = conn.getresponse()
            response.read()  # читаем тело полностью, иначе сервер может счесть соединение оборванным
            return response.status, response.getheader("Retry-After"), None
        except socket.timeout:
            return None, None, "timed out waiting for response"
        except (ConnectionError, http.client.HTTPException) as err:
            return None, None, "connection error: %s" % err
        finally:
            conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--method", default="GET")
    parser.add_argument("--max-attempts", type=int, default=5)
    parser.add_argument("--idempotency-key", default=None)
    args = parser.parse_args()

    headers = {}
    if args.idempotency_key is not None:
        headers["Idempotency-Key"] = args.idempotency_key

    # POST не идемпотентен: повторяется только с заданным ключом
    may_retry = args.method.upper() in IDEMPOTENT or args.idempotency_key is not None

    code = 1
    attempts_done = 0
    for number in range(1, args.max_attempts + 1):
        status, retry_after, error = Attempt(args.url, args.method, headers).run()
        attempts_done = number

        if status is None:
            print("attempt %d error %s" % (number, error))
        else:
            print("attempt %d status %d" % (number, status))

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
        print("sleep_ms %d" % pause)
        time.sleep(pause / 1000.0)

    print("result %s attempts %d" % ("success" if code == 0 else "failure", attempts_done))
    sys.exit(code)


main()
