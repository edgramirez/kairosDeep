import services as service


import fcntl
import socket
import struct
import os
import json
import requests


global srv_url
global number_of_resources
global no_mask_ids_dict
global camera_list
global source_list


no_mask_ids_dict = {}
camera_list = []
source_list = []


def set_server_url(url):
    if isinstance(url, str):
        global srv_url
        srv_url = url
        return True
    log_error("'url' parameter, most be a valid string")


def set_no_mask_ids_dict(camera_id, dictionary = None):
    global no_mask_ids_dict

    if camera_id in no_mask_ids_dict:
        no_mask_ids_dict.update({camera_id: dictionary})
        #print(no_mask_ids_dict)
    else:
        no_mask_ids_dict.update({camera_id: {}})
        #print('initialized', no_mask_ids_dict)


def get_no_mask_ids_dict(camera_id):
    global no_mask_ids_dict

    if camera_id in no_mask_ids_dict:
        return no_mask_ids_dict[camera_id]


def set_camera(value):
    global camera_list

    if value not in camera_list and value: 
        camera_list.append(value)


def set_sources(value):
    global source_list

    if value not in source_list and value:
        source_list.append(value)






def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    return ':'.join('%02x' % b for b in info[18:24])


def get_machine_macaddress(index = 0):
    list_of_interfaces = []
    list_of_interfaces = [item for item in os.listdir('/sys/class/net/') if item != 'lo']
    #return getHwAddr(list_of_interfaces[index])
    return getHwAddr('ens33')


def read_server_info():
    global srv_url

    machine_id = get_machine_macaddress()
    print(machine_id)
    machine_id = '00:04:4b:eb:f6:dd'  # HARDCODED MACHINE ID
    data = {"id": machine_id}
    url = srv_url + 'tx/device.getConfigByProcessDevice'
    response = service.send_json(data, 'POST', url)

    return json.loads(response.text)


def reading_server_config():
    if not service.set_header('.token'):
        log_error("Unable to set the 'Token' from file .token: ")

    set_server_url('https://mit.kairosconnect.app/')

    # get server infomation based on the nano mac_address
    scfg = read_server_info()

    print(scfg)

    for key in scfg:
        if key == 'OK':
            continue
        print(key, scfg[key])
        print('\n')
        for item in scfg[key]:
            print("...", item)
    quit()

    for camera in scfg.keys():
        if camera == 'OK':
            continue

        activate_service = False
        source = None

        for key in scfg[camera].keys():
            if key == 'video-socialDistancing' and scfg[camera][key]['enabled'] == "True":
                global srv_url
                source = scfg[camera][key]['source']
                set_no_mask_ids_dict(camera)
                service.set_mask_detection_url(srv_url)
                activate_service = True

        if activate_service:
            set_camera(camera)
            set_sources(source)


reading_server_config()


















