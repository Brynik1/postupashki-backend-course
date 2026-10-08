import re
import sys

OCTETS = re.compile(r"^(0|[1-9][0-9]?[0-9]?)$")
ADDR_RE = re.compile(r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$")


def dotted(n):
    return "%d.%d.%d.%d" % ((n >> 24) & 255, (n >> 16) & 255, (n >> 8) & 255, n & 255)


def parse_ip(text):
    """Строгий разбор адреса: ровно четыре октета, каждый 0..255"""
    if not ADDR_RE.match(text):
        sys.exit("bad address: %r" % text)
    return sum(int(o) << shift for o, shift in zip(text.split("."), (24, 16, 8, 0)))


def parse_prefix(text):
    if not OCTETS.match(text) or not (0 <= int(text) <= 32):
        sys.exit("bad prefix: %r" % text)
    return int(text)


def mask_of(prefix):
    return 0 if prefix == 0 else (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF


def print_subnet(arg):
    if arg.count("/") != 1:
        sys.exit("bad subnet: %r, нужен вид адрес/префикс" % arg)
    addr_text, prefix_text = arg.split("/")
    addr, prefix = parse_ip(addr_text), parse_prefix(prefix_text)
    mask = mask_of(prefix)
    network = addr & mask

    bits = 32 - prefix
    if bits >= 2:
        hosts = (1 << bits) - 2
        first, last = network + 1, network + (1 << bits) - 2
        broadcast = dotted(network + (1 << bits) - 1)
    elif bits == 1:  # /31 - оба адреса назначаются узлам (RFC 3021)
        hosts, first, last, broadcast = 2, network, network + 1, None
    else:  # /32
        hosts, first, last, broadcast = 1, network, network, None

    print("network %s" % dotted(network))
    print("broadcast %s" % (broadcast if broadcast is not None else "none"))
    print("netmask %s" % dotted(mask))
    print("prefix %d" % prefix)
    print("first %s" % dotted(first))
    print("last %s" % dotted(last))
    print("hosts %d" % hosts)


def print_route(path, target_text):
    dest = parse_ip(target_text)
    best = None
    with open(path) as table:
        for line in table:
            line = line.split("#")[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2 or "/" not in parts[0]:
                sys.exit("bad route line: %r" % line)
            net, prefix_text = parts[0].split("/")
            prefix = parse_prefix(prefix_text)
            mask = mask_of(prefix)
            if dest & mask == parse_ip(net) & mask and (best is None or prefix > best[0]):
                best = (prefix, parts[1])
    if best is None:
        print("unreachable true")
        sys.exit(1)
    print("via %s" % best[1])
    print("prefix %d" % best[0])


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: run.sh subnet адрес/префикс | run.sh route файл_таблицы адрес")
    mode = sys.argv[1]
    if mode == "subnet" and len(sys.argv) == 3:
        print_subnet(sys.argv[2])
    elif mode == "route" and len(sys.argv) == 4:
        print_route(sys.argv[2], sys.argv[3])
    else:
        sys.exit("unknown mode: %r" % (sys.argv[1] if sys.argv[1:] else None))


if __name__ == "__main__":
    main()
