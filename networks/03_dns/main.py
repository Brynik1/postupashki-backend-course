import socket
import struct
import sys
import time

RCODE = {0: "NOERROR", 1: "FORMERR", 2: "SERVFAIL", 3: "NXDOMAIN", 5: "REFUSED"}
QTYPE = {"A": 1, "NS": 2, "CNAME": 5, "MX": 15, "TXT": 16, "AAAA": 28}
TYPE_NAME = {v: k for k, v in QTYPE.items()}
WAIT_SECONDS = 5.0


def encode_name(name):
    data = b""
    for label in name.rstrip(".").split("."):
        data += bytes([len(label)]) + label.encode("idna" if False else "utf-8")
    return data + b"\x00"


def build_query(query_id, name, qtype):
    header = struct.pack("!HHHHHH", query_id, 0x0100, 1, 0, 0, 0)  # две рекурсии три - 0x0100 значит бит рекурсии
    return header + encode_name(name) + struct.pack("!HH", qtype, 1)


def read_name(message, offset):
    """Читает имя с раскрытием сжатых указателей; возвращает (имя, смещение после имени)"""
    labels = []
    jump_end = None
    for _ in range(128):
        length = message[offset]
        if length & 0xC0 == 0xC0:
            if jump_end is None:
                jump_end = offset + 2
            offset = struct.unpack("!H", message[offset:offset + 2])[0] & 0x3FFF
            continue
        offset += 1
        if length == 0:
            break
        labels.append(message[offset:offset + length].decode("utf-8", "replace"))
        offset += length
    if labels:
        name = ".".join(labels) + "."
    else:
        name = "."
    return name, (offset if jump_end is None else jump_end)


def answer_value(rtype, rdata, message, data_start):
    """Текстовое значение записи; None - запись не входит в поддерживаемый перечень"""
    if rtype == 1 and len(rdata) == 4:
        return "%d.%d.%d.%d" % tuple(rdata)
    if rtype == 28 and len(rdata) == 16:
        return socket.inet_ntop(socket.AF_INET6, rdata)
    if rtype in (2, 5):
        name, _ = read_name(message, data_start)
        return name
    if rtype == 15 and len(rdata) >= 3:
        pref = struct.unpack("!H", rdata[:2])[0]
        name, _ = read_name(message, data_start + 2)
        return "%d %s" % (pref, name)
    if rtype == 16:
        parts = []
        pos = 0
        while pos < len(rdata):
            chunk_len = rdata[pos]
            parts.append(rdata[pos + 1:pos + 1 + chunk_len].decode("utf-8", "replace"))
            pos += 1 + chunk_len
        return "".join(parts)
    return None


def parse_answer(message, offset):
    name, offset = read_name(message, offset)
    rtype, _rclass, ttl, rdlength = struct.unpack("!HHIH", message[offset:offset + 10])
    offset += 10
    rdata = message[offset:offset + rdlength]
    value = answer_value(rtype, rdata, message, offset)
    if value is None or rtype not in TYPE_NAME:
        return None, offset + rdlength
    return "%s %s %d" % (TYPE_NAME[rtype], value, ttl), offset + rdlength


def ask_once(server, name, qtype):
    """Отправляет один запрос и ждет подходящий ответ; None - таймаут"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(WAIT_SECONDS)
    try:
        query_id = int.from_bytes(bytearray(2), "big")  # стартуем с нуля для стабильности
        sent = build_query(query_id, name, qtype)
        sock.sendto(sent, server)
        for _ in range(64):
            try:
                packet, _ = sock.recvfrom(65535)
            except socket.timeout:
                return None
            if struct.unpack("!H", packet[:2])[0] != query_id:
                continue  # чужой идентификатор - ожидание продолжается
            return packet
    finally:
        sock.close()


def parse_response(packet):
    header = struct.unpack("!HHHHHH", packet[:12])
    rcode = header[1] & 0x0F
    status = RCODE.get(rcode, "RCODE%d" % rcode)
    qd, an = header[2], header[3]
    offset = 12
    for _ in range(qd):
        _, offset = read_name(packet, offset)
    offset += 4
    answers = []
    for _ in range(an):
        entry, offset = parse_answer(packet, offset)
        if entry is not None:
            answers.append(entry)
    return status, answers


def min_ttl(answers):
    return min((int(line.rsplit(" ", 1)[1]) for line in answers), default=0)


def process(server, cache, line, out):
    out.append("query %s" % line)
    name, _, type_name = line.partition(" ")
    qtype = QTYPE.get(type_name, 0)
    key = name.lower(), qtype

    now = time.monotonic()
    cached = cache.get(key)
    if cached and cached[0] > now:
        out.append("status NOERROR")
        for entry in cached[1]:
            out.append("answer %s" % entry)
        out.append("end")
        return False

    packet = ask_once(server, name, qtype)
    if packet is None:
        out.append("status TIMEOUT")
        out.append("end")
        return True  # таймаут - ненулевой код возврата
    status, answers = parse_response(packet)
    out.append("status %s" % status)
    for entry in answers:
        out.append("answer %s" % entry)
    ttl = min_ttl(answers)
    if status == "NOERROR" and answers and ttl > 0:
        cache[key] = (now + ttl, list(answers))
    out.append("end")
    return False


def main():
    server = (sys.argv[1], int(sys.argv[2]))
    cache = {}
    out = []
    timed_out = False
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if process(server, cache, line, out):
            timed_out = True
    print("\n".join(out))
    sys.exit(1 if timed_out else 0)


main()
