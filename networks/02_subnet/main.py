import sys


def dotted(n):
    return "%d.%d.%d.%d" % ((n >> 24) & 255, (n >> 16) & 255, (n >> 8) & 255, n & 255)


def int_of(ip):
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def mask_of(prefix):
    return 0 if prefix == 0 else (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF


def print_subnet(arg):
    ip, prefix = arg.split("/")
    prefix = int(prefix)
    mask = mask_of(prefix)
    addr = int_of(ip)
    network = addr & mask

    bits = 32 - prefix
    if bits >= 3:
        hosts = (1 << bits) - 2
        first, last = network + 1, network + (1 << bits) - 2
        broadcast = dotted(network + (1 << bits) - 1)
    elif bits == 2:  # /30
        hosts = 2
        first, last = network + 1, network + 2
        broadcast = dotted(network + 3)
    elif bits == 1:  # /31 - обе адреса узлам (RFC 3021)
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


def print_route(path, target):
    dest = int_of(target)
    best = None
    with open(path) as table:
        for line in table:
            line = line.split("#")[0].strip()
            if not line:
                continue
            net, iface = line.split()
            net_ip, prefix = net.split("/")
            prefix = int(prefix)
            mask = mask_of(prefix)
            if dest & mask == int_of(net_ip) & mask and (best is None or prefix > best[0]):
                best = (prefix, iface)
    if best is None:
        print("unreachable true")
        sys.exit(1)
    print("via %s" % best[1])
    print("prefix %d" % best[0])


mode = sys.argv[1]
if mode == "subnet":
    print_subnet(sys.argv[2])
elif mode == "route":
    print_route(sys.argv[2], sys.argv[3])
else:
    sys.exit(2)
