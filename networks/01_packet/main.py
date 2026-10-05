import sys


def clean_hex(text):
    return bytes.fromhex("".join(text.split()))  # пробелы/переводы строк/регистр не важны


def mac(raw):
    return ":".join("%02x" % b for b in raw)


def ip(raw):
    return "%d.%d.%d.%d" % tuple(raw)


def checksum_ok(header):
    # поле контрольной суммы при подсчете считается нулевым
    words = sum(int.from_bytes(header[i:i + 2], "big") for i in range(0, len(header), 2)) \
        - int.from_bytes(header[10:12], "big")
    while words >> 16:
        words = (words & 0xFFFF) + (words >> 16)
    return (~words & 0xFFFF) == int.from_bytes(header[10:12], "big")


def eth(data, out):
    dst, src = data[0:6], data[6:12]
    ethertype = int.from_bytes(data[12:14], "big")
    out.append("eth.dst %s" % mac(dst))
    out.append("eth.src %s" % mac(src))
    out.append("eth.ethertype 0x%04x" % ethertype)
    return ethertype


def ipv4(packet, out):
    version_ihl = packet[0]
    ihl = (version_ihl & 0x0F) * 4
    total_length = int.from_bytes(packet[2:4], "big")
    ident = int.from_bytes(packet[4:6], "big")
    flags_frag = int.from_bytes(packet[6:8], "big")
    ttl = packet[8]
    protocol = packet[9]
    flags = []
    if flags_frag & 0x4000:
        flags.append("DF")
    if flags_frag & 0x2000:
        flags.append("MF")

    out.append("ip.version %d" % (version_ihl >> 4))
    out.append("ip.ihl_bytes %d" % ihl)
    out.append("ip.total_length %d" % total_length)
    out.append("ip.id 0x%04x" % ident)
    out.append("ip.flags %s" % (",".join(flags) if flags else "none"))
    out.append("ip.frag_offset %d" % ((flags_frag & 0x1FFF) * 8))
    out.append("ip.ttl %d" % ttl)
    out.append("ip.protocol %d" % protocol)
    out.append("ip.src %s" % ip(packet[12:16]))
    out.append("ip.dst %s" % ip(packet[16:20]))
    out.append("ip.checksum_valid %s" % ("true" if checksum_ok(packet[:ihl]) else "false"))
    return ihl, protocol, total_length


TCP_FLAGS = [("FIN", 1), ("SYN", 2), ("RST", 4), ("PSH", 8), ("ACK", 16), ("URG", 32)]


def tcp(segment, out, ip_payload_start, ip_total):
    src, dst = int.from_bytes(segment[0:2], "big"), int.from_bytes(segment[2:4], "big")
    seq = int.from_bytes(segment[4:8], "big")
    ack = int.from_bytes(segment[8:12], "big")
    offset = (segment[12] >> 4) * 4
    flags = segment[13]
    set_flags = [name for name, bit in TCP_FLAGS if flags & bit]

    out.append("tcp.src_port %d" % src)
    out.append("tcp.dst_port %d" % dst)
    out.append("tcp.seq %d" % seq)
    out.append("tcp.ack %d" % ack)
    out.append("tcp.data_offset_bytes %d" % offset)
    out.append("tcp.flags %s" % (",".join(set_flags) if set_flags else "none"))
    out.append("tcp.window %d" % int.from_bytes(segment[14:16], "big"))
    return offset


def udp(segment, out):
    out.append("udp.src_port %d" % int.from_bytes(segment[0:2], "big"))
    out.append("udp.dst_port %d" % int.from_bytes(segment[2:4], "big"))
    out.append("udp.length %d" % int.from_bytes(segment[4:6], "big"))
    return 8


data = clean_hex(sys.stdin.read())
out = []
ethertype = eth(data, out)

if ethertype == 0x0800:
    # дополнение кадра до минимальной длины не проходит в общий счет ориентируемся на total_length
    ihl, protocol, total = ipv4(data[14:], out)
    transport_start = 14 + ihl

    if protocol == 6:
        header_len = tcp(data[transport_start:], out, transport_start, total)
    elif protocol == 17:
        header_len = udp(data[transport_start:], out)
    else:
        header_len = 0
        # payload от конца заголовка IPv4 (без данных вышестоящего)
        out.append("payload.length %d" % max(0, total - ihl - header_len))
        print("\n".join(out))
        sys.exit(0)

    payload_len = total - ihl - header_len
    out.append("payload.length %d" % max(0, payload_len))

print("\n".join(out))
