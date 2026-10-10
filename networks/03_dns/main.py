import ipaddress
import secrets
import socket
import struct
import sys
import time

RCODE = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN", 5: "REFUSED"}
QTYPE = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "TXT": 16, "AAAA": 28}
TYPE_NAME = {v: k for k, v in QTYPE.items()}
WAIT_SECONDS = 5.0


def encode_name(name):
    if name == ".":
        return b"\x00"
    text = name[:-1] if name.endswith(".") else name
    labels = []
    for label in text.split("."):
        encoded = label.encode("idna")
        if not encoded or len(encoded) > 63 or b"." in encoded:
            raise ValueError("пустая или длинная метка имени")
        labels.append(bytes([len(encoded)]) + encoded)
    data = b"".join(labels) + b"\x00"
    if len(data) > 255:
        raise ValueError("имя длиннее 255 байт")
    return data


def question_bytes(name, qtype):
    return encode_name(name) + struct.pack("!HH", qtype, 1)


def build_query(query_id, name, qtype):
    return struct.pack("!HHHHHH", query_id, 0x0100, 1, 0, 0, 0) + question_bytes(name, qtype)


def read_name(message, offset, limit=None):
    """До первого указателя читаем только исходное поле; после — весь пакет."""
    bound = len(message) if limit is None else min(limit, len(message))
    labels = []
    jump_end = None
    visited = set()
    wire_length = 1
    for _ in range(128):
        if offset in visited:
            raise ValueError("петля указателей DNS")
        visited.add(offset)
        if not 0 <= offset < bound:
            raise ValueError("имя обрывается внутри пакета")
        length = message[offset]
        if length & 0xC0 == 0xC0:
            if offset + 2 > bound:
                raise ValueError("обрезанный указатель DNS")
            if jump_end is None:
                jump_end = offset + 2
            offset = struct.unpack_from("!H", message, offset)[0] & 0x3FFF
            bound = len(message)
            continue
        if length & 0xC0:
            raise ValueError("зарезервированный тип метки DNS")
        offset += 1
        if length == 0:
            return (".".join(labels) + "." if labels else "."), (jump_end or offset)
        if offset + length > bound:
            raise ValueError("обрезанная метка DNS")
        wire_length += length + 1
        if wire_length > 255:
            raise ValueError("имя длиннее 255 байт")
        labels.append(message[offset:offset + length].decode("ascii", "backslashreplace"))
        offset += length
    raise ValueError("слишком много указателей DNS")


def answer_value(rtype, rdata, message, data_start):
    end = data_start + len(rdata)
    if rtype in (1, 28):
        required = 4 if rtype == 1 else 16
        if len(rdata) != required:
            raise ValueError("неверная длина адреса DNS")
        return socket.inet_ntop(socket.AF_INET if rtype == 1 else socket.AF_INET6, rdata)
    if rtype in (2, 5, 15):
        start = data_start
        if rtype == 15:
            if len(rdata) < 3:
                raise ValueError("обрезанная запись MX")
            start += 2
        name, consumed = read_name(message, start, end)
        if consumed != end:
            raise ValueError("длина имени не совпадает с RDLENGTH")
        return "%d %s" % (struct.unpack("!H", rdata[:2])[0], name) if rtype == 15 else name
    if rtype == 16:
        parts = []
        pos = 0
        while pos < len(rdata):
            chunk_len = rdata[pos]
            pos += 1
            if pos + chunk_len > len(rdata):
                raise ValueError("обрезанная строка TXT")
            parts.append(rdata[pos:pos + chunk_len].decode("utf-8", "replace"))
            pos += chunk_len
        return "".join(parts)
    return None


def parse_answer(message, offset):
    _, offset = read_name(message, offset)
    rtype, _, ttl, rdlength = struct.unpack_from("!HHIH", message, offset)
    offset += 10
    end = offset + rdlength
    if end > len(message):
        raise ValueError("обрезанные данные записи DNS")
    value = answer_value(rtype, message[offset:end], message, offset)
    entry = "%s %s %d" % (TYPE_NAME[rtype], value, ttl) if value is not None else None
    return entry, end, ttl


def parse_response(packet):
    # Статус сервера сохраняется даже при ошибке разбора его записей.
    flags = struct.unpack_from("!H", packet, 2)[0]
    rcode = flags & 0x0F
    status = RCODE.get(rcode, "RCODE%d" % rcode)
    try:
        header = struct.unpack("!HHHHHH", packet[:12])
        offset = 12
        for _ in range(header[2]):
            _, offset = read_name(packet, offset)
            struct.unpack_from("!HH", packet, offset)
            offset += 4
        answers, ttls = [], []
        for _ in range(header[3]):
            entry, offset, ttl = parse_answer(packet, offset)
            ttls.append(ttl)
            if entry is not None:
                answers.append(entry)
        return status, answers, min(ttls, default=0), None
    except (ValueError, struct.error) as err:
        return status, [], 0, "bad DNS response: %s" % err


def same_question(packet, name, qtype):
    count = struct.unpack_from("!H", packet, 4)[0]
    if count == 0:
        return True
    if count != 1:
        return False
    received, offset = read_name(packet, 12)
    sent, _ = read_name(encode_name(name), 0)
    received_type, received_class = struct.unpack_from("!HH", packet, offset)
    return received.lower() == sent.lower() and (received_type, received_class) == (qtype, 1)


def ask_once(server, name, qtype):
    query_id = secrets.randbits(16)
    sent = build_query(query_id, name, qtype)
    deadline = time.monotonic() + WAIT_SECONDS
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(max(0.001, deadline - time.monotonic()))
        sock.sendto(sent, server)
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                return None
            sock.settimeout(left)
            try:
                packet, sender = sock.recvfrom(65535)
            except socket.timeout:
                return None
            if sender != server or len(packet) < 4:
                continue
            if struct.unpack_from("!H", packet)[0] != query_id or not packet[2] & 0x80:
                continue
            try:
                if not same_question(packet, name, qtype):
                    continue
            except (ValueError, struct.error):
                # Подходящий ответ с повреждённым вопросом диагностирует parse_response.
                pass
            return packet


def process(server, cache, line):
    out = ["query %s" % line]
    try:
        parts = line.split()
        if len(parts) != 2:
            raise ValueError("нужны имя и тип")
        name, type_name = parts
        if type_name not in QTYPE:
            raise ValueError("unknown type %r" % type_name)
        qtype = QTYPE[type_name]
        wire = encode_name(name)
        key = wire.lower(), qtype
        now = time.monotonic()
        cached = cache.get(key)
        if cached and cached[0] > now:
            out.append("status NOERROR")
            out.extend("answer %s" % entry for entry in cached[1])
        else:
            packet = ask_once(server, name, qtype)
            if packet is None:
                out.extend(["status TIMEOUT", "end"])
                print("\n".join(out), flush=True)
                return True
            status, answers, ttl, error = parse_response(packet)
            out.append("status %s" % status)
            if error:
                out.append("error %s" % error)
            out.extend("answer %s" % entry for entry in answers)
            if status == "NOERROR" and ttl > 0 and error is None:
                cache[key] = (time.monotonic() + ttl, list(answers))
    except (ValueError, OSError) as err:
        out.append("error %s" % err)
    out.append("end")
    print("\n".join(out), flush=True)
    return False


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: run.sh <IPv4 сервера> <порт>")
    try:
        address = str(ipaddress.IPv4Address(sys.argv[1]))
        port = int(sys.argv[2])
        if not 1 <= port <= 65535:
            raise ValueError("порт должен быть в диапазоне 1..65535")
    except ValueError as err:
        sys.exit("bad server address or port: %s" % err)
    cache = {}
    for line in sys.stdin:
        line = line.strip()
        if line and process((address, port), cache, line):
            sys.exit(1)


if __name__ == "__main__":
    main()
