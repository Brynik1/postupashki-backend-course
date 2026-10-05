import re
import sys

CRLF = b"\r\n"
TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")


def fail(reason):
    print("error %s" % reason)
    sys.exit(1)


def next_crlf(data, pos, reason):
    idx = data.find(CRLF, pos)
    if idx == -1:
        fail(reason)
    return idx


def parse_start(line):
    tokens = line.split(" ")
    if len(tokens) == 3 and tokens[2] == "HTTP/1.1":
        return "request", tokens[0], tokens[1], None, None
    if tokens[0] == "HTTP/1.1" and len(tokens) >= 2 and tokens[1].isdigit() and len(tokens[1]) == 3:
        return "response", None, None, tokens[1], " ".join(tokens[2:])
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
        if not TOKEN_RE.match(name):
            fail("bad_header")
        value = line[colon + 1:].strip(" \t")
        if name.lower() == "content-length" and not value.isdigit():
            fail("bad_header")
        headers.append((name.lower(), value))


def read_chunked(data, pos):
    """Собирает тело, переданное по частям; возвращает (тело, смещение за концевиками)"""
    body = b""
    while True:
        end = next_crlf(data, pos, "bad_chunk")
        size_field = data[pos:end].decode("latin-1").split(";")[0].strip()
        pos = end + 2
        if size_field == "" or any(c not in "0123456789abcdefABCDEF" for c in size_field):
            fail("bad_chunk")
        size = int(size_field, 16)
        if size == 0:
            # после нулевой части могут идти поля концевика - читаем строки до пустой
            while True:
                end = next_crlf(data, pos, "bad_chunk")
                line = data[pos:end].decode("latin-1")
                pos = end + 2
                if line == "":
                    break
            return body, pos
        if pos + size > len(data):
            fail("bad_chunk")
        body += data[pos:pos + size]
        pos += size
        if data[pos:pos + 2] != CRLF:
            fail("bad_chunk")
        pos += 2


def read_body(data, pos, headers):
    names = [name for name, _ in headers]
    chunked = False
    for name, value in headers:
        if name == "transfer-encoding" and value == "chunked":
            chunked = True

    if chunked:
        body, _ = read_chunked(data, pos)
        return body

    length = 0
    for name, value in headers:
        if name == "content-length":
            length = int(value)
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


main()
