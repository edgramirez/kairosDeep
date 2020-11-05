import re
import os
import glob
import json
import time
import requests
import threading

from math import sqrt
from random import seed, randint
from datetime import datetime


global first_time_set
global last_time_set
global header
global server_url
global sd_keys
global frame_count
global nfps
global people_counting_enabled
global aforo_enabled
global social_distance_enabled
global aforo_url
global social_distance_url
global people_counting_url


first_time_set = set()
last_time_set = set()


def set_header(token_file):
    global header
    if file_exists(token_file):
        token_handler = open_file(token_file, 'r+')
        header = {'Content-type': 'application/json', 'X-KAIROS-TOKEN': token_handler.read().split('\n')[0]}


def set_aforo_url(srv_url):
    global aforo_url
    aforo_url = srv_url + 'tx/video-people.endpoint'


def set_social_distance_url(srv_url):
    global social_distance_url
    social_distance_url = srv_url + 'tx/video-socialDistancing.endpoint'


def set_service_people_counting_url(srv_url):
    global people_counting_url
    people_counting_url = srv_url + 'SERVICE_NOT_DEFINED_'


def set_frame_counter(value):
    global frame_count
    frame_count = int(value)


def get_frame_counter():
    global frame_count
    if frame_count is None:
        frame_count = 0
    return frame_count


def file_exists(file_name):
    try:
        with open(file_name) as f:
            return file_name
    except OSError as e:
        return False


def open_file(file_name, option='a+'):
    return open(file_name, option)


def create_file(file_name):
    os.remove(file_name)

    if not file_exists(file_name):
        with open(file_name, 'w+') as f:
            f.close()
    else:
        raise Exception('unable to delete file: %s' % file_name)

    return True


def api_get_number_of_frames_per_second():
    '''
    TODO: function not yet defined
    '''
    return None


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


# Return true if line segments AB and CD intersect
def OLD_check_if_object_is_in_area2(object_coordinates, reference_line):
    '''
    returns False if object is in area A1
    returns True if object is in area A2
    '''
    A = (0, 0)
    B = object_coordinates
    C = reference_line[0]
    D = reference_line[1]

    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)


# Return true if line segments AB and CD intersect
def intersect(x, y, w, h, x2, y2, w2, h2, line_coordinates):
    A = (int(x + (w-x)/2), int(y + (h-y)/2))
    B = (int(x2 + (w2-x2)/2), int(y2 + (h2-y2)/2))
    C = line_coordinates[0]
    D = line_coordinates[1]

    return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)


def ccw(A,B,C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])


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


def send_json(payload, action, url = None, **options):
    global header

    if action not in get_supported_actions() or url is None:
        raise Exception('Requested action: ({}) not supported. valid options are:'.format(action, get_supported_actions()))

    retries = options.get('retries', 5)
    sleep_time = options.get('sleep_time', 3)
    expected_response = options.get('expected_response', 200)
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
            return True
        except requests.exceptions.ConnectionError as e:
            time.sleep(1)
            if retry == retries - 1:
                raise Exception("Unable to Connect to the server after {} retries\n. Original exception".format(retry, str(e)))
        except requests.exceptions.HTTPError as e:
            time.sleep(1)
            if retry == retries - 1:
                raise Exception("Invalid HTTP response in {} retries\n. Original exception".format(retry, str(e)))
        except requests.exceptions.Timeout as e:
            time.sleep(1)
            if retry == retries - 1:
                raise Exception("Timeout reach in {} retries\n. Original exception".format(retry, str(e)))
        except requests.exceptions.TooManyRedirects as e:
            time.sleep(1)
            if retry == retries - 1:
                raise Exception("Too many redirection in {} retries\n. Original exception".format(retry, str(e)))


def count_in_and_out_when_object_leaves_the_frame(ids, camera_id, outside_area):
    '''
    The area A1 is the one closer to the point (0,0)
    Area A1 is by default outside 
    Area A2 is by default inside 
    ** This could be modified by setting up the configuration parameter "outside_area" to 2, (by default is 1)
    '''
    global aforo_url
    elements_to_delete = set()
    direction_1_to_2 = outside_area % 2
    direction_2_to_1 = outside_area + 1 % 2

    # se evaluan los elementos en last asi se garantiza que ese ID tiene al menos un registro en el dictionario "initial" y al menos uno en "last"
    for item in last.keys():
        if item not in ids:
            if initial[item] == 1 and last[item] == 2:
                # value #date-end is not needed, just for compatibility we hardcode this value
                # 'id': str(item),
                data = {
                        'direction': direction_1_to_2,
                        'camera-id': camera_id,
                        '#date-start': get_timestamp(),
                        '#date-end': get_timestamp(),
                        }
                print('In sending_json........', item, direction_1_to_2)
                x = threading.Thread(target=send_json, args=(data, 'PUT', aforo_url))
                x.start()
                #send_json(data, 'PUT', srv_url)

            elif initial[item] == 2 and last[item] == 1:
                #        'id': str(item),
                data = {
                        'direction': direction_2_to_1,
                        'camera-id': camera_id,
                        '#date-start': get_timestamp(),
                        '#date-end': get_timestamp(),
                        }
                print('Out sending_json........', item, direction_2_to_1)
                x = threading.Thread(target=send_json, args=(data, 'PUT', aforo_url,))
                x.start()

            initial.pop(item)
            elements_to_delete.add(item)

    for item in elements_to_delete:
        last.pop(item)


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


def people_counting_last_time_detected(ids, camera_id):
    global first_time_set

    srv_url = get_service_people_counting_url()

    if first_time_set:
        ids_set = set(ids)
        for item in first_time_set.difference(ids_set):
            if item not in last_time_set:
                data = {
                        'camera-id': camera_id,
                        '#date': get_timestamp(),
                        'object_id': item,
                        }
                print('People_counting last time.. PUT', data)
                x = threading.Thread(target=send_json, args=(data, 'PUT', srv_url))
                x.start()
                #send_json(data, 'PUT', srv_url)
                last_time_set.add(item)
        first_time_set = first_time_set.intersection(ids_set)


def counting_in_and_out_first_detection(box, object_id):
    '''
    A1 is the closest to the origin (0,0) and A2 is the area after the reference line
    A1 is by default the outside
    A2 is by default the inside
    This can be changed by modifying the configuration variable "outside_area" to 2 (by default 1)
    x = box[0]
    y = box[1]
    '''
    # returns True if object is in area A2
    if check_if_object_is_in_area2(box):
        if object_id not in initial:
            initial.update({object_id: 2})
        else:
            last.update({object_id: 2})
    else:
        if object_id not in initial:
            initial.update({object_id: 1})
        else:
            last.update({object_id: 1})


#def aforo(box, object_id, ids, camera_id, outside_area, referece_line, initial, last, entradas, salidas, m, b):
def aforo(box, object_id, ids, camera_id, initial, last, entradas, salidas, outside_area=None, reference_line=None, m=None, b=None, rectangle=None):
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
    #print(object_id, initial, last)
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


def social_distance(boxes, ids, boxes_length, camera_id, nfps, risk_value, tolerated_distance, dict_of_ids):
    # distance_plus_factor = 'tolerated_distance' * 1.42
    # nfps
    global social_distance_url
    distance_plus_factor = tolerated_distance * 1.42
    frame_count = get_frame_counter()

    # This is the cleanup segment and 

    # if dictionary has no elements, there is no need to check anything
    if len(dict_of_ids) > 0:
        # get the subset of ids that disappear: the ones that are in the current detected ids but no in the dictionary list
        ids_in_dict_not_in_ids = set(dict_of_ids.keys()) - set(ids)
        dict_of_ids_subset = {key_: value for key_, value in dict_of_ids.items() if key_ in ids_in_dict_not_in_ids}

        for key in dict_of_ids_subset:
            if dict_of_ids_subset[key]['consecutive_absence'] == nfps:
                for inner_id in dict_of_ids_subset[key]['inner_ids']:
                    if dict_of_ids_subset[key]['inner_ids'][str(inner_id)]['reported_in_frame'] and (dict_of_ids_subset[key]['inner_ids'][str(inner_id)]['visible'] / risk_value) > 1: 
                        alert_id = dict_of_ids_subset[key]['inner_ids'][str(inner_id)]['alert_id']
                        #        'id_pivot': key,
                        #        'alert_id': alert_id,
                        #        'related_id': inner_id,
                        data = {
                                'id': alert_id,
                                'camera-id': camera_id,
                                '#date': get_timestamp(),
                                }
                        print('cleaning:', data, 'PUT', social_distance_url)
                        #send_json(data, 'PUT', social_distance_url)
                        x = threading.Thread(target=send_json, args=(data, 'PUT', social_distance_url,))
                        x.start()

                # Now delete the id cause is no longer in sight
                dict_of_ids.pop(key)
            else:
                if dict_of_ids_subset[key]['reported_in_frame'] and (dict_of_ids_subset[key]['reported_in_frame'] + 1 == frame_count):
                    dict_of_ids_subset[key]['consecutive_absence'] += 1
                else:
                    dict_of_ids_subset[key]['consecutive_absence'] = 1
    '''
    takes one element and compares it with the others in front of it, to avoid repetition of combinations
    (A, B, C, D)
       AB AC AD
          BC CD

    We are going to start compararing the first element (index=0 or i=0)
    '''
    i = 1
    for box in boxes:
        # add element if not exist in the dictonary
        if str(ids[i-1]) in dict_of_ids.keys():
            dict_of_ids[str(ids[i-1])]['visible'] += 1
        else:
            dict_of_ids.update(
                        {
                        str(ids[i-1]): {
                            'visible': 1,
                            'consecutive_absence': 0, 
                            'inner_ids': {},
                            'reported_in_frame': False,
                            }
                        }
                    )

        j = 0
        for inner_box in boxes[i:]:
            '''
            distance_per_factor = tolerated_distance * sqt(2)
            If the addition of the sides of a triangle is greater thant the "distance_per_factor" that element is far from the radio or hypotenous
            and so is not close enough to break the rule
            In the contrary we check if lower and then make a full analysis of the distances
            '''
            if distance_plus_factor > (abs(box[0] - inner_box[0]) + abs(box[1] - inner_box[1])): 
                x2 = inner_box[0]
                y2 = inner_box[1]
                #w2 = inner_box[2]
                #h2 = inner_box[3]

                x1 = box[0]
                y1 = box[1]
                #w1 = box[2]
                #h1 = box[3]

                distance = sqrt( ((x2 - x1) * (x2 - x1)) + ((y2 - y1) * (y2 - y1)) )

                # if distance is lower than the tolerated value we add the ID and treat it   
                if distance < tolerated_distance:

                    # before use the inner dictionary, check if there are ids we need to delete, so that we loop with less elements
                    if len(dict_of_ids) > 0:
                        ids_in_dict_not_in_ids = set(dict_of_ids.keys()) - set(ids)
                        dict_of_ids_subset = {key_: value for key_, value in dict_of_ids[str(ids[i-1])]['inner_ids'].items() if key_ in ids_in_dict_not_in_ids}
                        for inner_subset_keys in dict_of_ids_subset:
                            if dict_of_ids_subset[inner_subset_keys]['consecutive_absence'] == nfps:
                                dict_of_ids[str(ids[i-1])]['inner_ids'].pop(inner_subset_keys)
                                dict_of_ids_subset.pop(inner_subset_keys)
                            else:
                                if dict_of_ids_subset[inner_subset_keys]['reported_in_frame'] and (dict_of_ids_subset[inner_subset_keys]['reported_in_frame'] + 1) == frame_count:
                                    dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])]['consecutive_absence'] += 1
                                    dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])]['reported_in_frame'] = frame_count
                                else:
                                    dict_of_ids[str(ids[i-1])]['inner_ids'][inner_subset_keys]['consecutive_absence'] = 1

                    if str(ids[i+j]) in dict_of_ids[str(ids[i-1])]['inner_ids'].keys():
                        dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])]['visible'] += 1

                        # report social distance alarm if inner_id has been visibled n times = to risk_value and no previous alert
                        if dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])]['visible'] >= risk_value:
                            if not dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])]['alert_id']:
                                alert_id = str(int((datetime.now() - datetime(1970,1,1)).total_seconds())) + '_' + str(ids[i-1]) + '_' + str(ids[i+j])
                                dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])].update({'alert_id': alert_id})

                                #    'distance': distance,
                                #    'id_pivot': ids[i-1],
                                #    'related_id': ids[i+j],
                                #    'alert_id': alert_id,
                                data = {
                                    'id': alert_id,
                                    'camera-id': camera_id,
                                    '#date': get_timestamp(),
                                    }
                                #data = {'id': camera_id}
                                #social_distance_url = 'https://mit.kairosconnect.app/tx/device.getConfigByProcessDevice'
                                #send_json(data, 'PUT', social_distance_url)
                                x = threading.Thread(target=send_json, args=(data, 'PUT', social_distance_url,))
                                x.start()
                    else:
                        # add element if not exist on the dictonary
                        dict_of_ids[str(ids[i-1])]['inner_ids'].update(
                                {
                                str(ids[i+j]): {
                                    'visible': 1,
                                    'consecutive_absence': 0,
                                    'reported_in_frame': False,
                                    'alert_id': False,
                                    }
                                }
                            )
            j += 1

        if i == (boxes_length - 2):
            break
        i += 1

