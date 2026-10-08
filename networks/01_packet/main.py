import sys


def clean_hex(text):
    return bytes.fromhex("".join(text.split()))  # пробелы, переводы строк, двоеточия игнорируем


def mac(raw):
    return ":".join("%02x" % b for b in raw)


def dotted(raw):
    return "%d.%d.%d.%d" % tuple(raw)


def checksum_valid(header):
    # RFC 1071: складываем все слова вместе с полем checksum; после свертки переносов
    # у целого заголовка получается 0xFFFF
    words = sum(int.from_bytes(header[i:i + 2], "big") for i in range(0, len(header), 2))
    while words >> 16:
        words = (words & 0xFFFF) + (words >> 16)
    return words == 0xFFFF


def eth(data, out):
    ethertype = int.from_bytes(data[12:14], "big")
    out.append("eth.dst %s" % mac(data[0:6]))
    out.append("eth.src %s" % mac(data[6:12]))
    out.append("eth.ethertype 0x%04x" % ethertype)
    return ethertype


def ipv4(packet, out):
    version_ihl = packet[0]
    ihl = (version_ihl & 0x0F) * 4
    if version_ihl >> 4 != 4 or (version_ihl & 0x0F) < 5:
        die("битый заголовок IPv4: версия не 4 или поле IHL меньше 5")
    if len(packet) < ihl:
        fail("обрезанный дамп: заголовок IPv4 требует %d байт" % ihl, 1)
    total = int.from_bytes(packet[2:4], "big")
    flags_frag = int.from_bytes(packet[6:8], "big")
    flags = []
    if flags_frag & 0x4000:
        flags.append("DF")
    if flags_frag & 0x2000:
        flags.append("MF")

    out.append("ip.version %d" % (version_ihl >> 4))
    out.append("ip.ihl_bytes %d" % ihl)
    out.append("ip.total_length %d" % total)
    out.append("ip.id 0x%04x" % int.from_bytes(packet[4:6], "big"))
    out.append("ip.flags %s" % (",".join(flags) if flags else "none"))
    out.append("ip.frag_offset %d" % ((flags_frag & 0x1FFF) * 8))
    out.append("ip.ttl %d" % packet[8])
    out.append("ip.protocol %d" % packet[9])
    out.append("ip.src %s" % dotted(packet[12:16]))
    out.append("ip.dst %s" % dotted(packet[16:20]))
    out.append('ip.checksum_valid %s' % ("true" if checksum_valid(packet[:ihl]) else "false"))
    return ihl, packet[9], total


TCP_FLAGS = [("FIN", 1), ("SYN", 2), ("RST", 4), ("PSH", 8), ("ACK", 16), ("URG", 32)]


def tcp(segment, out):
    offset = (segment[12] >> 4) * 4
    flags = segment[13]
    set_flags = [name for name, bit in TCP_FLAGS if flags & bit]

    out.append("tcp.src_port %d" % int.from_bytes(segment[0:2], "big"))
    out.append("tcp.dst_port %d" % int.from_bytes(segment[2:4], "big"))
    out.append("tcp.seq %d" % int.from_bytes(segment[4:8], "big"))
    out.append("tcp.ack %d" % int.from_bytes(segment[8:12], "big"))
    out.append("tcp.data_offset_bytes %d" % offset)
    out.append("tcp.flags %s" % (",".join(set_flags) if set_flags else "none"))
    out.append("tcp.window %d" % int.from_bytes(segment[14:16], "big"))
    return offset


def udp(segment, out):
    out.append("udp.src_port %d" % int.from_bytes(segment[0:2], "big"))
    out.append("udp.dst_port %d" % int.from_bytes(segment[2:4], "big"))
    out.append("udp.length %d" % int.from_bytes(segment[4:6], "big"))
    return 8


def die(message, code=1):
    print(message, file=sys.stderr)
    sys.exit(code)


def main():
    data = clean_hex(sys.stdin.read())
    out = []
    ethertype = eth(data, out)

    if ethertype != 0x0800:
        print("\n".join(out))
        return

    packet = data[14:]
    ihl, protocol, total = ipv4(packet, out)
    transport_start = ihl

    header_len = 0
    if protocol == 6:
        if len(packet) < transport_start + 20:
            die("обрезанный дамп: заголовку TCP не хватает байт")
        header_len = tcp(packet[transport_start:], out)
    elif protocol == 17:
        if len(packet) < transport_start + 8:
            die("обрезанный дамп: заголовку UDP не хватает байт")
        header_len = udp(packet[transport_start:], out)

    payload_len = total - ihl - header_len
    out.append("payload.length %d" % max(0, payload_len))
    print("\n".join(out))


if __name__ == "__main__":
    main()
