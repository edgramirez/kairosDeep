import re
import os
import glob
import json
import time
import requests
import threading

import fcntl
import socket
import struct

import mycommon as com

from math import sqrt
from random import seed, randint
from datetime import datetime



global first_time_set
global last_time_set
global header
global server_url
global sd_keys
global nfps
global people_counting_enabled
global aforo_enabled
global social_distance_enabled
global social_distance_url
global people_counting_url
global plate_detection_url

header = None

first_time_set = set()
last_time_set = set()


##### GENERIC FUNCTIONS


def log_error(msg, _quit = True):
    print("-- PARAMETER ERROR --\n"*5)
    print(" %s \n" % msg)
    print("-- PARAMETER ERROR --\n"*5)
    if _quit:
        quit()
    else:
        return False


def api_get_number_of_frames_per_second():
    '''
    TODO: function not yet defined
    '''
    return None


def file_exists(file_name):
    try:
        with open(file_name) as f:
            return file_name
    except OSError as e:
        return False


def open_file(file_name, option='a+'):
    if file_exists(file_name):
        return open(file_name, option)
    return False


def create_file(file_name, content = None):

    if file_exists(file_name):
        os.remove(file_name)
        if file_exists(file_name):
            raise Exception('unable to delete file: %s' % file_name)

    if content:
        with open(file_name, 'w+') as f:
            f.write(content)
    else:
        with open(file_name, 'w+') as f:
            f.close()

    return True


def get_number_of_frames_per_second():
    global nfps

    nfps = api_get_number_of_frames_per_second()

    if nfps is None:
        return 16

    return nfps


def get_supported_actions():
    return ('GET', 'POST', 'PUT', 'DELETE')


def get_timestamp():
    return int(time.time() * 1000)


def set_header(token_file = None):
    if token_file is None:
        token_file = '.token'

    global header

    if header is None:
        if isinstance(token_file, str):
            token_handler = open_file(token_file, 'r+')
            if token_handler:
                header = {'Content-type': 'application/json', 'X-KAIROS-TOKEN': token_handler.read().split('\n')[0]}
                print('Header correctly set')
                return True

    return False

def getHwAddr(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    return ':'.join('%02x' % b for b in info[18:24])


def get_ip_address(ifname):
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]


def get_machine_macaddresses():
    list_of_interfaces = [item for item in os.listdir('/sys/class/net/') if item != 'lo']
    macaddress_list = []

    for iface_name in list_of_interfaces:
        ip = get_ip_address(iface_name)
        if ip:
            macaddress_list.append(getHwAddr(iface_name))
            return macaddress_list


def get_server_info(server_url, abort_if_exception = True, _quit = True):
    url = server_url + 'tx/device.getConfigByProcessDevice'

    for machine_id in get_machine_macaddresses():
        # HARDCODED MACHINE ID
        #machine_id = '00:04:4b:eb:f6:dd'
        data = {"id": machine_id}
        
        if abort_if_exception:
            response = send_json(data, 'POST', url)
        else:
            options = {'abort_if_exception': False}
            response = send_json(data, 'POST', url, **options)
    if response:
        return json.loads(response.text)
    else:
        return log_error("Unable to retrieve the device configuration from the server. Server response".format(response), _quit)


def get_server_info_from_local_file(filename, _quit = True):
    if file_exists(filename):
        with open(filename) as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return log_error("data unknow error, data is not a dictionary: {}")
    else:
        return log_error("Unable to read the device configuration from local file: {}".format(filename), _quit)


def parse_parameters_and_values_from_config(config_data):
    # filter config and get only data for this server using the mac to match
    config_data = get_config_filtered_by_local_mac(config_data)

    # filter config and get only data of active services
    return get_config_filtered_by_active_service(config_data)


def get_config_filtered_by_local_mac(config_data):
    '''
    By now we only support one nano server and one interface
    but it can be a big server with multiple interfaces so I
    leave the logic with to handle this option
    '''
    services_data = {}
    for key in config_data.keys():
        if mac_address_in_config(key):
            services_data[key] = config_data[key]
    if services_data:
        return services_data

    log_error("The provided configuration does not match any of server interfaces mac address")


def get_config_filtered_by_active_service(config_data):
    if not isinstance(config_data, dict):
        log_error("Configuration error - Config data must be a dictionary - type: {} / content: {}".format(type(config_data), config_data))
    active_services = {}

    # at this point there should be only one server mac but we still loop in case we have many multiple network interfaces 
    for server_mac in config_data.keys():
        #  we loop over all the different cameras attach to this server
        for camera_mac in config_data[server_mac]:
            # we loop over all the services assigned to the camera
            for service in config_data[server_mac][camera_mac]:
                # if the service is enable we add it to the active services
                if 'enabled' in config_data[server_mac][camera_mac][service] and config_data[server_mac][camera_mac][service]['enabled'] is True:
                    if 'source' not in config_data[server_mac][camera_mac][service]:
                        log_error("Service {} must have a source (video or live streaming)".format(service))

                    # Create new key only for each of the active services
                    new_key_name = 'srv_' + server_mac + "_camera_" + camera_mac + '_' + service
                    active_services[new_key_name] = {service: config_data[server_mac][camera_mac][service]}

    if len(active_services) < 1:
        com.log_error("\nConfiguration does not contain any active service for this server: \n\n{}".format(config_data))

    return active_services


def mac_address_in_config(mac_config):
    for machine_id in com.get_machine_macaddresses():
        if mac_config == machine_id:
            return True
    return False


def send_json(payload, action, url = None, **options):
    set_header()
    global header

    if action not in get_supported_actions() or url is None:
        raise Exception('Requested action: ({}) not supported. valid options are:'.format(action, get_supported_actions()))

    retries = options.get('retries', 2)
    sleep_time = options.get('sleep_time', 1)
    expected_response = options.get('expected_response', 200)
    abort_if_exception = options.get('abort_if_exception', True)

    data = json.dumps(payload)

    # emilio comenta esto para insertar en MongoDB
    # return True

    for retry in range(retries):
        try:
            if action == 'GET':
                r = requests.get(url, data=data, headers=header)
            elif action == 'POST':
                r = requests.post(url, data=data, headers=header)
            elif action == 'PUT':
                r = requests.put(url, data=data, headers=header)
            else:
                r = requests.delete(url, data=data, headers=header)
            return r
        except requests.exceptions.ConnectionError as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Unable to Connect to the server after {} retries\n. Original exception: {}".format(retry, str(e)))
        except requests.exceptions.HTTPError as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Invalid HTTP response in {} retries\n. Original exception: {}".format(retry, str(e)))
        except requests.exceptions.Timeout as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Timeout reach in {} retries\n. Original exception: {}".format(retry, str(e)))
        except requests.exceptions.TooManyRedirects as e:
            time.sleep(sleep_time)
            if retry == retries - 1 and abort_if_exception:
                raise Exception("Too many redirection in {} retries\n. Original exception: {}".format(retry, str(e)))


def check_if_object_is_in_area2(object_coordinates, reference_line, m, b):
    '''
    # returns True if object is in Area2
    # returns False if object is in Area1
    '''
    if m is None:
        # object_coordinates[0] -  x
        # reference_line[0][0]  -  x1
        # if x > x1 then is in Area2, else in Area1
        if object_coordinates[0] > reference_line[0][0]:
            return True
        return False
    elif m == 0:
        # object_coordinates[1] -  y
        # reference_line[0][1]  -  y1
        # if y > y1 then is in Area2, else in Area1
        if object_coordinates[1] > reference_line[0][1]:
            return True
        return False
    else:
        #x1 = reference_line[0][0]
        #y1 = reference_line[0][1]
        #x = object_coordinates[0]
        #m = ((y2 - y1) * 1.0) / (x2 -x1)
        #y_overtheline = (m * (x - x1)) + y1
        y_overtheline = (m * object_coordinates[0]) + b
        #y_overtheline = (m * (object_coordinates[0] - reference_line[0][0])) + reference_line[0][1]

        #if y > y_overtheline:
        if object_coordinates[1] > y_overtheline:
            return True
        else:
            return False


def is_point_insde_polygon(x, y, polygon_length, polygon):

    p1x,p1y = polygon[0]
    for i in range(polygon_length+1):
        p2x,p2y = polygon[i % polygon_length]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        # returns True if x,y are inside
                        return True
        p1x,p1y = p2x,p2y

    # returns False if x,y are not inside
    return False


##### PEOPLE COUNTING

def set_service_people_counting_url(server_url):
    global people_counting_url
    people_counting_url = server_url + 'SERVICE_NOT_DEFINED_'


def people_counting(camera_id, total_objects):
    '''
    Sending only the total of detected objects
    '''
    global people_counting_url
    
    date = get_timestamp()
    alert_id = str(date) + '_' + str(camera_id) + '_' + str(date)
    data = {
            'id': alert_id,
            'camera-id': camera_id,
            '#total_updated_at': date,
            'object_id': total_objects,
            }
    #print('People_counting first time..POST', data, people_counting_url)
    #x = threading.Thread(target=send_json, args=(data, 'POST', srv_url))
    #x.start()


##### AFORO

#def set_aforo_url():
#    global aforo_url, srv_url
#aforo_url = srv_url + 'tx/video-people.endpoint'


def aforo(aforo_url, box, object_id, ids, camera_id, initial, last, entradas, salidas, outside_area=None, reference_line=None, m=None, b=None, rectangle=None):
    '''
    A1 is the closest to the origin (0,0) and A2 is the area after the reference line
    A1 is by default the outside
    A2 is by default the inside
    This can be changed by modifying the configuration variable "outside_area" to 2 (by default 1)
    x = box[0]
    y = box[1]

    initial -  must be a dictionary, and will be used to store the first position (area 1 or area2) of a given ID
    last -     must be a dictionary, and will be used to store the last position (area 1 or area2) of a given ID
    '''

    if rectangle:
        # si el punto esta afuera del area de interes no evaluamos
        if box[0] < rectangle[0] or box[0] > rectangle[4] or box[1] > rectangle[5] and box[1] < rectangle[1]:
            if reference_line:
                return entradas, salidas
            else:
                outside_area = 1
                area = 1

    if reference_line:
        if check_if_object_is_in_area2(box, reference_line, m, b):
            area = 2
        else:
            area = 1
    else:
        outside_area = 1
        area = 2

    if outside_area == 1:
        direction_1_to_2 = 1
        direction_2_to_1 = 0
    else:
        direction_1_to_2 = 0
        direction_2_to_1 = 1

    if object_id not in initial:
        initial.update({object_id: area})
        if object_id not in last:
            return entradas, salidas
    else:
        last.update({object_id: area})

    # De igual forma si los elementos continen las misma areas en el estado 
    # actual que en el previo, entonces no tiene caso evaluar mas
    if initial[object_id] == last[object_id]:
        return entradas, salidas

    for item in last.keys():
        if initial[item] == 1 and last[item] == 2:
            time_in_epoc = get_timestamp()
            data_id = str(time_in_epoc) + '_' + str(object_id)
            data = {
                    'id': data_id,
                    'direction': direction_1_to_2,
                    'camera-id': camera_id,
                    '#date-start': time_in_epoc,
                    '#date-end': time_in_epoc,
                }
            initial.update({item: 2})

            print('Sending Json of camera_id: ', camera_id, 'ID: ',item, 'Sal:0,Ent:1 = ', direction_1_to_2, "tiempo =",time_in_epoc)
            x = threading.Thread(target=send_json, args=(data, 'PUT', aforo_url,))
            x.start()

            if direction_1_to_2 == 1:
                entradas += 1
            else:
                salidas += 1

        elif initial[item] == 2 and last[item] == 1:
            time_in_epoc = get_timestamp()
            data_id = str(time_in_epoc) + '_' + str(object_id)
            data = {
                    'id': data_id,
                    'direction': direction_2_to_1,
                    'camera-id': camera_id,
                    '#date-start': time_in_epoc,
                    '#date-end': time_in_epoc,
                }
            initial.update({item: 1})

            print('Sending Json of camera_id: ', camera_id, 'ID: ',item, 'Sal:0,Ent:1 = ', direction_2_to_1, "tiempo =",time_in_epoc)
            x = threading.Thread(target=send_json, args=(data, 'PUT', aforo_url,))
            x.start()

            if direction_2_to_1 == 1:
                entradas += 1
            else:
                salidas += 1

    return entradas, salidas


##### SOCIAL DISTANCE

def set_social_distance_url(server_url):
    global social_distance_url
    social_distance_url = srv_url + 'tx/video-socialDistancing.endpoint'


def social_distance2(camera_id, ids_and_boxes, tolerated_distance, persistence_time, max_side_plus_side, detected_ids):
    '''
    social distance is perform in pairs of not repeated pairs
    Being (A, B, C, D, E, F) the set of detected objects

    The possible permutation are:

       AB AC AD AE AF
          BC BD BE BF
             CD CE CF
                DE DF
                   Ef

    We are going to start compararing the first element (index=0 or i=0)
    '''
    # TODO: diccionario puede crecer mucho depurarlo comparando los elementos que dejen de existir o no sean detectados despues de 5seg')

    # sorting elements to always have the same evaluation order 
    ids = [ item for item in ids_and_boxes.keys() ]
    ids.sort()
    # creating the list 
    i = 1
    for pivot in ids[:-1]:
        for inner in ids[i:]:
            if pivot not in detected_ids:
                Ax = ids_and_boxes[pivot][0]
                x = ids_and_boxes[inner][0]
    
                if Ax > x:
                    dx = Ax -x
                else:
                    dx = x - Ax
    
                if dx < tolerated_distance:
                    Ay = ids_and_boxes[pivot][1]
                    y = ids_and_boxes[inner][1]

                    if Ay > y:
                        dy = Ay - y
                    else:
                        dy = y - Ay

                    if (dx + dy) < max_side_plus_side and sqrt((dx*dx) + (dy*dy)) < tolerated_distance:
                        # first time detection for pivot A and associated B
                        pivot_time = get_timestamp()
                        detected_ids.update({
                            pivot: {
                                inner:{
                                    '#detected_at': pivot_time,
                                    '#reported_at': None,
                                    'reported': False,
                                    }
                                }
                            })
            else:
                if inner not in detected_ids[pivot]:
                    Ax = ids_and_boxes[pivot][0]
                    x = ids_and_boxes[inner][0]
        
                    if Ax > x:
                        dx = Ax -x
                    else:
                        dx = x - Ax
        
                    if dx < tolerated_distance:
                        Ay = ids_and_boxes[pivot][1]
                        y = ids_and_boxes[inner][1]

                        if Ay > y:
                            dy = Ay - y
                        else:
                            dy = y - Ay

                        if (dx + dy) < max_side_plus_side and sqrt((dx*dx) + (dy*dy)) < tolerated_distance:
                            # firt time detection for associated C is registered
                            detected_at_inner = get_timestamp()
                            detected_ids[pivot].update({
                                inner:{
                                    '#detected_at': detected_at_inner,
                                    '#reported_at': None,
                                    'reported': False,
                                    }
                                })
                else:
                    Ax = ids_and_boxes[pivot][0]
                    x = ids_and_boxes[inner][0]
        
                    if Ax > x:
                        dx = Ax -x
                    else:
                        dx = x - Ax

                    if dx > tolerated_distance:
                        if not detected_ids[pivot][inner]['reported']:
                            del detected_ids[pivot][inner]
                    else:
                        Ay = ids_and_boxes[pivot][1]
                        y = ids_and_boxes[inner][1]

                        if Ay > y:
                            dy = Ay - y
                        else:
                            dy = y - Ay

                        if (dx + dy) >= max_side_plus_side or sqrt((dx*dx) + (dy*dy)) >= tolerated_distance:
                            del detected_ids[pivot][inner]
                        else:
                            current_time = get_timestamp()
                            initial_time = detected_ids[pivot][inner]['#detected_at']
                            if not detected_ids[pivot][inner]['reported'] and (current_time - initial_time) >= persistence_time:
                                detected_ids[pivot][inner].update({'#reported_at': current_time})
                                detected_ids[pivot][inner].update({'reported': True})
                                alert_id = str(current_time) + '_' +  str(pivot) + '_and_'+ str(inner)
                                data = {
                                    'id': alert_id,
                                    'camera-id': camera_id,
                                    '#date': current_time,
                                    }
                                print('Social distance', data, social_distance_url, 'PUT', 'distance=', sqrt((dx*dx) + (dy*dy)), 'tolerada:', tolerated_distance)
                                x = threading.Thread(target=send_json, args=(data, 'PUT', social_distance_url,))
                                x.start()
            i += 1


#### MASK DETECTION

def set_mask_detection_url(server_url):
    global mask_detection_url
    mask_detection_url = server_url + 'tx/video-maskDetection.endpoint'


def mask_detection(mask_id, no_mask_ids, camera_id, reported_class = 0):
    time_in_epoc = get_timestamp()
    data_id = str(time_in_epoc) + '_' + str(mask_id)
    data = {
        'id': data_id,
        'mask': reported_class,
        'camera-id': camera_id,
        '#date-start': time_in_epoc,
        '#date-end': time_in_epoc
        }

    print('Mask detection', data, mask_detection_url, 'PUT')
    x = threading.Thread(target=send_json, args=(data, 'PUT', mask_detection_url,))
    x.start()


#### PLATE DETECTION

def set_plate_detection_url(server_url):
    global plate_detection_url
    plate_detection_url = server_url + 'TO_BE_SETUP______tx/video-plateDetection.endpoint'


