import os
import fcntl
import struct
import socket
import sys



def log_debug(msg):
    print("\n------- %s -------" % msg)


def log_warning(msg):
    print("\n WARNING ------- %s -------" % msg)


def log_error(msg, _quit = True):
    print("\n")
    print("-- PARAMETER ERROR --\n"*2)
    print(" %s " % msg)
    print("\n")
    print("-- PARAMETER ERROR --\n"*2)
    print("\n")
    if _quit:
        quit()
    else:
        return False


def get_machine_macaddresses():
    try:
        default_iface = os.environ['ID_IFACE']
    except KeyError:
        default_iface = False

    list_of_interfaces = [item for item in os.listdir('/sys/class/net/') if item != 'lo']
    macaddress_list = []
    for iface_name in list_of_interfaces:
        if default_iface:
            macaddress_list.append(getHwAddr(default_iface))
            return macaddress_list
        macaddress_list.append(getHwAddr(iface_name))
    return macaddress_list


def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    return ':'.join('%02x' % b for b in info[18:24])


