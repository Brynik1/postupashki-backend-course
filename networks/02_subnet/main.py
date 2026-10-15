import re
import sys

OCTETS = re.compile(r"^(0|[1-9][0-9]?[0-9]?)$")
ADDR_RE = re.compile(r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$")


def dotted(n):
    return "%d.%d.%d.%d" % ((n >> 24) & 255, (n >> 16) & 255, (n >> 8) & 255, n & 255)


def parse_ip(text):
    """Строгий разбор адреса: ровно четыре октета, каждый 0..255"""
    if not ADDR_RE.fullmatch(text):
        sys.exit("bad address: %r" % text)
    return sum(int(o) << shift for o, shift in zip(text.split("."), (24, 16, 8, 0)))


def parse_prefix(text):
    if not OCTETS.fullmatch(text) or not (0 <= int(text) <= 32):
        sys.exit("bad prefix: %r" % text)
    return int(text)


def mask_of(prefix):
    return 0 if prefix == 0 else (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF


def parse_subnet(arg):
    if arg.count("/") != 1:
        sys.exit("bad subnet: %r, нужен вид адрес/префикс" % arg)
    addr_text, prefix_text = arg.split("/")
    return parse_ip(addr_text), parse_prefix(prefix_text)


def print_subnet(arg):
    addr, prefix = parse_subnet(arg)
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
    routes = {}
    try:
        with open(path, encoding="utf-8") as table:
            for line in table:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 2:
                    sys.exit("bad route line: %r" % line)
                net, prefix = parse_subnet(parts[0])
                mask = mask_of(prefix)
                key = net & mask, prefix
                if key in routes and routes[key] != parts[1]:
                    sys.exit("conflicting routes for %s/%d" % (dotted(key[0]), prefix))
                routes[key] = parts[1]
                if dest & mask == key[0] and (best is None or prefix > best[0]):
                    best = (prefix, parts[1])
    except (OSError, UnicodeDecodeError) as err:
        sys.exit("cannot read route table %r: %s" % (path, err))
    if best is None:
        print("unreachable true")
        sys.exit(1)
    print("via %s" % best[1])
    print("prefix %d" % best[0])


def main():
    usage = "usage: run.sh subnet адрес/префикс | run.sh route файл_таблицы адрес"
    if len(sys.argv) < 2:
        sys.exit(usage)
    mode = sys.argv[1]
    if mode not in ("subnet", "route"):
        sys.exit("unknown mode: %r; %s" % (mode, usage))
    expected = 3 if mode == "subnet" else 4
    if len(sys.argv) != expected:
        sys.exit("wrong number of arguments for %s; %s" % (mode, usage))
    if mode == "subnet":
        print_subnet(sys.argv[2])
    else:
        print_route(sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
