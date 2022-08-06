import os
import time
import fcntl
import struct
import socket
import shutil
import pickle
from pathlib import Path
from os import walk

import lib.definitions as sd


SOURCE_PATTERNS = ('file:///', 'rtsp://')
SERVICES = {}
SERVICE_DEFINITION = [sd.source]


try:
    USER_SERVER_ENDPOINT = os.environ['USER_SERVER_ENDPOINT']
except KeyError:
    log_error('\nUnable to read environment variable "USER_SERVER_ENDPOINT"  -- Set the variable in $HOME/.bashrc')

try:
    FACE_RECOGNITION_TOKEN = os.environ['FACE_RECOGNITION_TOKEN']
except KeyError:
    log_error('\nUnable to read environment variable "FACE_RECOGNITION_TOKEN"  -- Set the variable in $HOME/.bashrc')


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


def log_debug(msg):
    print("\n------- %s -------\n" % msg)


def log_warning(msg):
    print("\n WARNING ------- %s -------" % msg)


def dir_exists(path_str):
    path = Path(path_str)
    return path.exists()


def create_data_dir(path_str):
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)
    return True


def delete_tree(path_str, match_pattern = None):
    if dir_exists(path_str):
        if match_pattern is not None and path_str[0:len(match_pattern)] != match_pattern:
            log_error("Unable to delete directory: {}, path must start with: {}".format(path_str, match_pattern))
        try:
            shutil.rmtree(match_pattern)
            return True
        except OSError as e:
            log_error("Error: {} - {}. (Unable to delete path '{}')".format(e.filename, e.strerror, path_str))
    else:
        log_debug("Directory path '{}' does not exist, nothing to do".format(path_str))


def file_exists(file_name):
    try:
        with open(file_name) as f:
            return file_name
    except OSError as e:
        return False


def file_exists_and_not_empty(file_name):
    if file_exists(file_name) and os.stat(file_name).st_size > 0:
        return True
    return False


def file_exists_and_empty(file_name):
    if file_exists(file_name) and os.stat(file_name).st_size == 0:
        return True
    return False


def read_images_in_dir(path_to_read):
    dir_name, subdir_name, file_names = next(walk(path_to_read))
    images = [item for item in file_names if '.jpeg' in item[-5:] or '.jpg' in item[-4:] or 'png' in item[-4:]]
    return images, dir_name


def open_file(file_name, option='a+'):
    if file_exists(file_name):
        return open(file_name, option)
    return False


def get_timestamp():
    return int(time.time() * 1000)


def get_hw_addr(interface_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(interface_name, 'utf-8')[:15]))
    return ':'.join('%02x' % b for b in info[18:24])


def get_ip_address(interface_name):
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]


def get_machine_mac_addresses():
    try:
        default_iface = os.environ['ID_IFACE']
    except KeyError:
        default_iface = False

    list_of_interfaces = [item for item in os.listdir('/sys/class/net/') if item != 'lo']
    macaddress_list = []
    for iface_name in list_of_interfaces:
        if default_iface:
            macaddress_list.append(get_hw_addr(default_iface))
            return macaddress_list
        macaddress_list.append(get_hw_addr(iface_name))
    return macaddress_list


def get_local_interfaces_and_ips():
    """ Returns a dictionary of name:ip key value pairs. """
    MAX_BYTES = 4096
    FILL_CHAR = b'\0'
    SIOCGIFCONF = 0x8912
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array('B', MAX_BYTES * FILL_CHAR)
    names_address, names_length = names.buffer_info()
    mutable_byte_buffer = struct.pack('iL', MAX_BYTES, names_address)
    mutated_byte_buffer = fcntl.ioctl(sock.fileno(), SIOCGIFCONF, mutable_byte_buffer)
    max_bytes_out, names_address_out = struct.unpack('iL', mutated_byte_buffer)
    namestr = names.tobytes()
    namestr[:max_bytes_out]
    bytes_out = namestr[:max_bytes_out]
    ip_dict = {}
    for i in range(0, max_bytes_out, 40):
        name = namestr[ i: i+16 ].split(FILL_CHAR, 1)[0]
        name = name.decode('utf-8')
        ip_bytes = namestr[i+20:i+24]
        full_addr = []
        for netaddr in ip_bytes:
            if isinstance(netaddr, int):
                full_addr.append(str(netaddr))
            elif isinstance(netaddr, str):
                full_addr.append(str(ord(netaddr)))
        # ignoring 127.0.0.1
        if '.'.join(full_addr) != '127.0.0.1':
            ip_dict[name] = '.'.join(full_addr)

    return ip_dict


def write_to_pickle(known_face_encodings, known_face_metadata, data_file):
    with open(data_file, mode='wb') as f:
        face_data = [known_face_encodings, known_face_metadata]
        pickle.dump(face_data, f)


def read_pickle(pickle_file, exception_if_fail=True):
    try:
        with open(pickle_file, 'rb') as f:
            known_face_encodings, known_face_metadata = pickle.load(f)
            return known_face_encodings, known_face_metadata
    except OSError as e:
        if exception_if_fail:
            log_error("Unable to open pickle_file: {}, original exception {}".format(pickle_file, str(e)))
        else:
            return [], []


def delete_pickle(data_file):
    os.remove(data_file)
    if file_exists(data_file):
        raise Exception('unable to delete file: %s' % data_file)
