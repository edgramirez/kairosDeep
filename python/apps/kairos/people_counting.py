import time
import os
import glob
import json
import requests

from math import sqrt
#from sort import *
from random import seed, randint
from datetime import datetime

from configs import config as cfg


files = glob.glob('output/*.png')
for f in files:
    os.remove(f)

global mac_address
global outside_area
global server_url
global total_frames_counter
global sd_keys
global NFPS 
global previous
global first_time_set
global last_time_set
global frame_count

previous = False
first_time_set = set()
last_time_set = set()


def get_previous():
    global previous
    return previous


def set_previous(value):
    global previous
    previous = value


def file_exists(file_name):
    try:
        with open(file_name) as f:
            return file_name
    except OSError as e:
        return False


def open_file(file_name, option='a+'):
    return open(file_name, option)


def api_get_number_of_frames_per_second():
    '''
    function not yet defined
    '''
    return None


def get_number_of_frames_per_second():
    global nfps

    nfps = api_get_number_of_frames_per_second()

    if nfps is None:
        return 16

    return nfps


def set_camera_mac_address(camera_mac_address = None):
    global mac_address
    mac_address = camera_mac_address


def get_camera_mac_address():
    return mac_address


def set_outside_area(value):
    global outside_area
    outside_area = value


def get_outside_area():
    return outside_area


def get_supported_actions():
    return ('GET', 'POST', 'PUT', 'DELETE')


def set_supported_sd_keys(sd_dict):
    global sd_keys
    sd_keys = tuple(sd_dict.keys())


def get_supported_sd_keys():
    global sd_keys
    return sd_keys


def get_server_url():
    global server_url
    return server_url


def get_service_people_counting_url():
    return get_server_url() + '/people_counting'


def get_service_count_in_and_out_url():
    return get_server_url() + 'tx/video-people.endpoint'


def get_service_count_intersecting_in_any_direction_url():
    return get_server_url() + '/counting_intersecting_in_any_direction'


def get_service_social_distance_url():
    return get_server_url() + '/social_distance_alert'


def get_timestamp():
    return int(time.time() * 1000)


def set_server_url(url = None):
    global server_url

    if url is None:
        server_url = cfg['server']['url']
    else:
        server_url = url


def set_total_frame_from_video_file(total = 0):
    global total_frames_counter
    total_frames_counter = total


def get_total_frames_from_video_file():
    global total_frames_counter
    return total_frames_counter


def create_file(file_name):
    os.remove(file_name)

    if not file_exists(file_name):
        with open(file_name, 'w+') as f:
            f.close()
    else:
        raise Exception('unable to delete file: %s' % file_name)

    return True


def load_classes():
    # load the COCO class labels our YOLO model was trained on
    labelsPath = cfg['parameters']['classes']
    return open(labelsPath).read().strip().split("\n")


def load_yolo():
    # load our YOLO object detector trained on COCO dataset (80 classes)
    # and determine only the *output* layer names that we need from YOLO
    print("[INFO] loading YOLO from disk...")
    return cv2.dnn.readNetFromDarknet(cfg['parameters']['configs'], cfg['parameters']['weights'])


def adjust_gamma(image, gamma=1.0):
    # build a lookup table mapping the pixel values [0, 255] to
    # their adjusted gamma values
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
 
    # apply gamma correction using the lookup table
    return cv2.LUT(image, table)


# Return true if line segments AB and CD intersect
def check_if_object_in_area2(object_coordinates, reference_line):
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


def id_colors():
    # initialize a list of colors to represent the different detected IDs
    np.random.seed(42)
    return np.random.randint(0, 255, size=(10000, 3), dtype="uint8")


def total_frames(vs):
    # try to determine the total number of frames in the video file
    try:
        prop = cv2.cv.CV_CAP_PROP_FRAME_COUNT if imutils.is_cv2() else cv2.CAP_PROP_FRAME_COUNT
        total = int(vs.get(prop))
        print("[INFO] {} total frames in video".format(total))
        return total
    except:
        print("[INFO] could not determine # of frames in video")
        print("[INFO] no approx. completion time can be provided")
        return -1


def layer_detection(frame, net):
    # construct a blob from the input frame and then perform a forward pass of the 
    # YOLO object detector, giving us our bounding boxes and associated probabilities
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (256, 256), swapRB=True, crop=False)
    net.setInput(blob)
    return net.forward(ln)


def generate_tracks(layerOutputs, LABELS):
    # initialize our lists of detected bounding boxes, confidences, and class IDs, respectively
    boxes = []
    center = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of the current object detection
            #scores = detection[5:] no se porque elige los valores con menos probabilidade desde el elemento 5 hasta el ultimo en lugar de los primeros 5
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = float(scores[classID])

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if LABELS[classID] == cfg['parameters']['class'] and confidence > cfg['parameters']['confidence']:
                # scale the bounding box coordinates back relative to the size of the image, keeping in mind that YOLO
                # actually returns the center (x, y)-coordinates of the bounding box followed by the boxes' width and height
                box = detection[0:4] * np.array([Width, Height, Width, Height])
                (centerX, centerY, width, height) = box.astype("int")
                
                # use the center (x, y)-coordinates to derive the top and and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences, and class IDs
                center.append(int(centerY))
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)
                
    # apply non-maxima suppression to suppress weak, overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, cfg['parameters']['confidence'], cfg['parameters']['threshold'])
    
    dets = []
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            dets.append([x, y, x+w, y+h, confidences[i]])

    np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})
    dets = np.asarray(dets)
    return tracker.update(dets)
    

def current_tracked_values(tracks, enable_trace = False, frequency = 40, file_handler = None):
    memory = {}
    boxes = []
    indexIDs = []
    origin = (0, 0)

    for track in tracks:
        xy3 = (int((track[0] + track[2]) / 2), int((track[1] + track[3]) / 2))
        current_id = int(track[4])
        x = int((track[0] + track[2]) / 2)
        y = int((track[1] + track[3]) / 2)
        boxes.append([track[0], track[1], track[2], track[3]])
        indexIDs.append(current_id)
        memory[indexIDs[-1]] = boxes[-1]

        if enable_trace and frame_count % frequency == 0:
            content = "%s,%s,%s,%s\n" % (frame_count, current_id, x, y)
            file_handler.write(content)

    return memory, boxes, indexIDs 


def display_speed_calculation(frame, object_id, x, y, w, h, x2, y2, w2, h2, color, object_speed):
    y_pix_dist = int(y + (h - y) / 2) - int(y2 + (h2 - y2) / 2)
    text_y = "{} y".format(y_pix_dist)
    x_pix_dist = int(x + (w - x) / 2) - int(x2 + (w2 - x2) / 2)
    text_x = "{} x".format(x_pix_dist)
    final_pix_dist = sqrt((y_pix_dist * y_pix_dist) + (x_pix_dist * x_pix_dist))
    speed = np.round(1.5 * y_pix_dist, 2)
    # text_speed = "{} km/h".format(speed)
    text_speed = "{}".format(object_id)

    width = object_speed['text_width']
    x_offset = object_speed['text_x_offset']
    y_offset = object_speed['text_y_offset']

    cv2.putText(frame, text_speed, (x + x_offset, h + y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, width)
                

def write_result_to_disk(frame, writer):
    # check if the video writer is None
    if writer is None:
        # initialize our video writer
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(cfg['video']['output']['file'], fourcc, 15, (frame.shape[1], frame.shape[0]), True)

        # some information on processing single frame
        if get_total_frames_from_video_file() > 0:
            elap = (end - start)
            print("[INFO] single frame took {:.4f} seconds".format(elap))
            print("[INFO] estimated total time to finish: {:.4f}".format(elap * get_total_frames_from_video_file()))

    # write the output frame to disk
    writer.write(frame)
    return writer


def display_counter_results(frame, frame_counter, intersection_counter = 0, counter2 = 0):
    if cfg['counting_results']['show'] and intersection_counter is not None and frame is not None:
        counter_text = ''
        if cfg['counting_results']['frame_counting']:
            counter_text = "Frame: {}, ".format(frame_counter) 

        counter_text += "{}: {} - {}: {}".format(cfg['counting_results']['text1'], intersection_counter, cfg['counting_results']['text2'], counter2)
        text_coordinates = cfg['counting_results']['coordinates']
        text_color = cfg['counting_results']['color']
        text_width = cfg['counting_results']['width']
        text_size = cfg['counting_results']['size']

        cv2.putText(frame, counter_text, text_coordinates, cv2.FONT_HERSHEY_DUPLEX, text_size, text_color, text_width)


def read_camera_mac_address():
    '''
    ideally this should be an independent process execute only one time at application startup time. 
    Then save the camera infomation in a variable go till the system is power off and again on, and 
    the process will repeat again
    '''
    set_camera_mac_address(cfg['video']['input']['camera_id'])


def get_headers():
    token_handler = open_file(file_exists(os.getenv("HOME") + '/' + cfg['server']['token_file']), 'r+')
    #print(token_handler.read().split('\n')[0])
    return {'Content-type': 'application/json', 'X-KAIROS-TOKEN': token_handler.read().split('\n')[0]}


def send_json(payload, action, url = None, **options):
    retries = options.get('retries', 5)
    sleep_time = options.get('sleep_time', 3)
    expected_response = options.get('expected_response', 200)

    if action not in get_supported_actions() or url is None:
        raise Exception('Requested action: ({}) not supported. valid options are:'.format(action, get_supported_actions()))

    for retry in range(retries):
        try:
            if action == 'GET':
                r = requests.get(url, data=json.dumps(payload), headers=get_headers())
            elif action == 'POST':
                r = requests.post(url, data=json.dumps(payload), headers=get_headers())
            elif action == 'PUT':
                r = requests.put(url, data=json.dumps(payload), headers=get_headers())
            else:
                r = requests.delete(url, data=json.dumps(data), headers=get_headers())
        except requests.exceptions.ConnectionError as e:
            if retry == retries - 1:
                raise Exception("Unable to Connect to the server after {} retries\n. Original exception".format(retry, str(e)))
        except requests.exceptions.HTTPError as e:
            if retry == retries - 1:
                raise Exception("Invalid HTTP response in {} retries\n. Original exception".format(retry, str(e)))
        except requests.exceptions.Timeout as e:
            if retry == retries - 1:
                raise Exception("Timeout reach in {} retries\n. Original exception".format(retry, str(e)))
        except requests.exceptions.TooManyRedirects as e:
            if retry == retries - 1:
                raise Exception("Too many redirection in {} retries\n. Original exception".format(retry, str(e)))

        #if r.status_code != expected_response:
        #    time.sleep(sleep_time)
        #    print('Not the expected return code {}, expecting {}'.format(r.status_code, expected_response))

    # print(action, url, json.dumps(payload))
    return True


def get_file_name(suffix = '', delete_if_created = False):
    file_name = cfg['parameters']['output_file_path']
    file_name += cfg['business']['id'] + '_'
    file_name += cfg['business']['country_id'] + '_'
    file_name += cfg['business']['state_id'] + '_'
    file_name += cfg['business']['store_id'] + '_'

    if suffix != '':
        file_name += suffix + '_'

    file_name += datetime.now().strftime("%y") + '_'
    file_name += datetime.now().strftime("%m") + '_'
    file_name += datetime.now().strftime("%d") + '_'
    file_name += str(time.time())

    if delete_if_created and file_exists(file_name):
        create_file(file_name)

    return file_name


def count_in_and_out_when_object_leaves_the_frame(ids):
    '''
    The area A1 is the one closer to the point (0,0)
    Area A1 is by default outside 
    Area A2 is by default inside 
    ** This could be modified by setting up the configuration parameter "outside_area" to 2, (by default is 1)
    '''
    if counting_in_and_out['enabled']:
        if frameIndex % counting_in_and_out['report_frequency'] == 0:
            elements_to_delete = set()
            camera_id = get_camera_mac_address()
       
            for item in last.keys():
                if item not in ids:
                    #print('id', item, 'is not int:', ids)
                    if initial[item] == 1 and last[item] == 2:
                        # value #date-end is not needed, just for compatibility we hardcode this value
                        #        'id': str(item),
                        data = {
                                'direction': get_outside_area() % 2,
                                'camera-id': camera_id,
                                '#date-start': get_timestamp(),
                                '#date-end': 1595907644469,
                                }
                        print('in sending_json........', item, get_outside_area() % 2)
                        #send_json(data, 'PUT', get_service_count_in_and_out_url())
                    elif initial[item] == 2 and last[item] == 1:
                        #        'id': str(item),
                        data = {
                                'direction': (get_outside_area() + 1) % 2,
                                'camera-id': camera_id,
                                '#date-start': get_timestamp(),
                                '#date-end': 1595907644469,
                                }
                        print('out sending_json........', item, (get_outside_area() + 1) % 2)
                        #send_json(data, 'PUT', get_service_count_in_and_out_url())
                    initial.pop(item)
                    elements_to_delete.add(item)
                    #print('elements to delete', elements_to_delete)
       
            for item in elements_to_delete:
                last.pop(item)
       
            #content = f"{str(frameIndex)} in:{str(counter_1_to_2)} out:{counter_2_to_1}\n"
            #file_handler2.write(content)
       
            #return counter_1_to_2, counter_2_to_1


def people_counting_storing_fist_time(object_id):
    '''
    Storing only the first time the ID appears
    '''
    global first_time_set

    if people_counting['enabled'] and object_id not in first_time_set:
        data = {
                'camera_id': get_camera_mac_address(),
                'date_time': get_timestamp(),
                'object_id': object_id,
                }
        send_json(data, 'POST', get_service_people_counting_url())
        first_time_set.add(object_id)


def people_counting_last_time_detected(ids):
    global first_time_set

    if people_counting['enabled'] and first_time_set:
        ids_set = set(ids)
        for item in first_time_set.difference(ids_set):
            if item not in last_time_set:
                data = {
                        'camera_id': get_camera_mac_address(),
                        'date_time': get_timestamp(),
                        'object_id': item,
                        }
                send_json(data, 'PUT', get_service_people_counting_url())
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
    if not counting_in_and_out['enabled']:
        return

    # returns True if object is in area A2
    if check_if_object_in_area2(box, line1):
        if object_id not in initial:
            initial.update({object_id: 2})
        else:
            last.update({object_id: 2})
    else:
        if object_id not in initial:
            initial.update({object_id: 1})
        else:
            last.update({object_id: 1})


def counting_in_and_out_when_changing_area(box, object_id, ids, previous):
    '''
    A1 is the closest to the origin (0,0) and A2 is the area after the reference line
    A1 is by default the outside
    A2 is by default the inside
    This can be changed by modifying the configuration variable "outside_area" to 2 (by default 1)
    x = box[0]
    y = box[1]
    '''
    if counting_in_and_out['enabled']:
        # returns True if object is in area A2
        if check_if_object_in_area2(box, line1):
            area = 2
        else:
            area = 1

        if object_id not in initial:
            initial.update({object_id: area})
        else:
            last.update({object_id: area})

        if previous and (frameIndex % counting_in_and_out['report_frequency']) == 0:
            elements_to_delete = set()
            camera_id = get_camera_mac_address()

            for item in last.keys():
                if initial[item] == 1 and last[item] == 2:
                    data = {
                            'direction': (get_outside_area() + 1) % 2,
                            'camera-id': camera_id,
                            '#date-start': get_timestamp(),
                            '#date-end': 1595907644469,
                            }
                    print('out if area 1 is inside sending_json........', item, (get_outside_area() + 1) % 2)

                    # deleting elements that are no longer present in the list of ids
                    if item not in ids:
                        elements_to_delete.add(item)
                        initial.pop(item)
                    else:
                        initial.update({item: 2})

                elif initial[item] == 2 and last[item] == 1:
                    data = {
                            'direction': get_outside_area() % 2,
                            'camera-id': camera_id,
                            '#date-start': get_timestamp(),
                            '#date-end': 1595907644469,
                            }
                    print('in if area 1 is inside sending_json........', item, get_outside_area() % 2)

                    # deleting elements that are no longer present in the list of ids
                    if item not in ids:
                        elements_to_delete.add(item)
                        initial.pop(item)
                    else:
                        initial.update({item: 1})

            # deleting elements that are no longer present in the list of ids
            for item in elements_to_delete:
                last.pop(item)



def get_social_distance_parameter_value(value = None):

    if value in get_supported_sd_keys():
        return cfg['service']['social_distance'][value]


def check_inner_distance_relations(pivot_element_dict, rest_of_elements_dict):
    return None


def get_frame_counter():
    global frame_count
    if frame_count is None:
        frame_count = 0
    return frame_count


def set_frame_counter(value):
    global frame_count
    frame_count = int(value)


#def get_distances_between_detected_elements_from_centroid(frame, boxes, ids, dict_of_ids, distance_plus_factor, nfps, risk_value, frame_count):
def get_distances_between_detected_elements_from_centroid(boxes, ids):
    global dict_of_ids, distance_plus_factor, nfps

    frame_count = get_frame_counter()
    if not social_distance['enabled']:
        return

    # if we just detected 1 element, there is no need to calculate distances
    length = len(boxes)
    if length > 1:
        # if dictionary has no elements, there is no need to check anything
        if len(dict_of_ids) > 0:
            # get the subset of ids that desapear: the ones that are in the current detected ids but no in the dictionary list
            ids_in_dict_not_in_ids = set(dict_of_ids.keys()) - set(ids)
            dict_of_ids_subset = {key_: value for key_, value in dict_of_ids.items() if key_ in ids_in_dict_not_in_ids}

            for key in dict_of_ids_subset:
                if dict_of_ids_subset[key]['consecutive_absence'] == nfps:
                    for inner_id in dict_of_ids_subset[key]['inner_ids']:
                        if dict_of_ids_subset[key]['inner_ids'][str(inner_id)]['reported_in_frame'] and (dict_of_ids_subset[key]['inner_ids'][str(inner_id)]['visible'] / risk_value) > 1: 
                            alert_id = dict_of_ids_subset[key]['inner_ids'][str(inner_id)]['alert_id']
                            data = {
                                    'camera_id': get_camera_mac_address(),
                                    'date_time': get_timestamp(),
                                    'id_pivot': key,
                                    'related_id': inner_id,
                                    'alert_id': alert_id,
                                    }
                            send_json(data, 'PUT', get_service_social_distance_url())

                    # Now delete the id cause is no longer in sight
                    dict_of_ids.pop(key)
                else:
                    if dict_of_ids_subset[key]['reported_in_frame'] and (dict_of_ids_subset[key]['reported_in_frame'] + 1 == frame_count):
                        dict_of_ids_subset[key]['consecutive_absence'] += 1
                    else:
                        dict_of_ids_subset[key]['consecutive_absence'] = 1
        '''
        take un element and compares it with the ones in front of it, to avoid repetition of convinations
        (A, B, C, D)
           AB AC AD
              BC CD
        '''
        i = 1
        for box in boxes:
            # add element if not exist on the dictonary
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
                If the addition of the sides of a triangle is greater thant the "distance_per_factor" that element is far from the radio or hipotenous
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
                    if distance < get_social_distance_parameter_value('tolerated_distance'):

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

                                #if social_distance['enabled_draw_rectangle']:
                                #    cv2.rectangle(frame, (int(x1), int(y1)), (int(w1), int(h1)), (0,0,255), 3)
                                #    cv2.rectangle(frame, (int(x2), int(y2)), (int(w2), int(h2)), (0,0,255), 3)

                                if not dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])]['alert_id']:

                                    alert_id = str(int((datetime.now() - datetime(1970,1,1)).total_seconds())) + '_' + str(ids[i-1]) + '_' + str(ids[i+j])
                                    dict_of_ids[str(ids[i-1])]['inner_ids'][str(ids[i+j])].update({'alert_id': alert_id})

                                    data = {
                                        'camera_id': get_camera_mac_address(),
                                        'date_time': get_timestamp(),
                                        'distance': distance,
                                        'id_pivot': ids[i-1],
                                        'related_id': ids[i+j],
                                        'alert_id': alert_id,
                                        }
                                    send_json(data, 'POST', get_service_social_distance_url())
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

            if i == (length - 2):
                break
            i += 1


def draw_line(frame, **kwargs):

    xy = kwargs.get('xy', None)
    percentage = kwargs.get('percentage', 2)
    line_width = kwargs.get('line_width', 2)
    color = kwargs.get('color', (0, 255, 255))

    cv2.line(frame, (xy[0][0], xy[0][1]), (xy[1][0], xy[1][1]), color, line_width)


def load_video(input_type, input_video):
    if input_type == 'rtsp':
        print("[INFO] starting video stream...")
        video_stream = cv2.VideoCapture(input_video)
        time.sleep(2.0)
    else:
        print("[INFO] opening video file...")
        video_stream = cv2.VideoCapture(file_exists(input_video))
        set_total_frame_from_video_file(total_frames(video_stream))

    return video_stream


'''
services
'''

trace_objects = cfg['service']['trace_objects']
counting_in_and_out = cfg['service']['counting_in_and_out']
object_intersection = cfg['service']['object_intersection']
object_speed = cfg['service']['object_speed']
people_counting = cfg['service']['people_counting']
social_distance = cfg['service']['social_distance']

read_camera_mac_address()
set_outside_area(counting_in_and_out['outside_area'])
set_server_url()
set_supported_sd_keys(social_distance)

base_url = get_server_url()

#tracker = Sort()
line1 = cfg['intersection_line']['coordinates']


# initialize the video stream, pointer to output video file, and frame dimensions
(Width, Height) = (None, None)
frameIndex = 0
memory = {}

#COLORS = id_colors()
#LABELS = load_classes()
#net = load_yolo()

if cfg['video']['input']['input_type'] == 'video':
    video_source = file_exists(cfg['video']['input']['source'])
else:
    video_source = cfg['video']['input']['source']

#vs = load_video(cfg['video']['input']['input_type'], video_source)

#ln = net.getLayerNames()
#ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# loop over frames from the video file stream
writer = None

get_file_name('trace', delete_if_created=True)
get_file_name('people_counting', delete_if_created=True)


initial = {}
last = {}

counter_1_to_2 = 0
counter_2_to_1 = 0
intersection_counter = 0

dict_of_ids = {}
distance_plus_factor = social_distance['tolerated_distance'] * 1.42  # raiz cuadrada de 2, maxima distancia de la suma de sus lados
nfps = get_number_of_frames_per_second()
risk_value = nfps * social_distance['persistence_time']

variable = None
#while True:
while variable == 'EXECUTE_ME':
    file_handler1 = open_file(get_file_name('trace'))
    file_handler2 = open_file(get_file_name('people_counting'))
    frame_count += 1

    # read the next frame from the file
    (grabbed, frame) = vs.read()

    # if the frame was not grabbed, then we have reached the end of the stream
    if not grabbed:
        break

    # if the frame dimensions are empty, grab them
    if Width is None or Height is None:
        (Height, Width) = frame.shape[:2]

    frame = adjust_gamma(frame, gamma=1.5)

    start = time.time()
    layerOutputs = layer_detection(frame, net)
    end = time.time()

    tracks = generate_tracks(layerOutputs, LABELS)
    previous = memory.copy()
    memory, boxes, indexIDs = current_tracked_values(tracks, trace_objects['enabled'], trace_objects['frequency'], file_handler1)

    # Features of tracking
    if len(boxes) > 0:

        if counting_in_and_out['enabled']:
            if frameIndex % counting_in_and_out['report_frequency'] == 0:
                counter_1_to_2, counter_2_to_1 = count_in_and_out_when_object_leaves_the_frame(counter_1_to_2, counter_2_to_1, initial, last, indexIDs, file_handler2)

        if social_distance['enabled']:
            get_distances_between_detected_elements_from_centroid(frame, boxes, indexIDs, dict_of_ids, tolerated_distance_plus_factor, nfps, risk_value, frame_count)

        i = 0
        for box in boxes:
            # extract the bounding box coordinates
            (x, y) = (int(box[0]), int(box[1]))
            (w, h) = (int(box[2]), int(box[3]))

            color = [int(grb_color) for grb_color in COLORS[indexIDs[i]]]
    
            # Service display object rectangle
            if cfg['rectangle']['show']:
                cv2.rectangle(frame, (x, y), (w, h), color, cfg['rectangle']['width'])

            if indexIDs[i] in previous:
                previous_box = previous[indexIDs[i]]
                (x2, y2) = (int(previous_box[0]), int(previous_box[1]))
                (w2, h2) = (int(previous_box[2]), int(previous_box[3]))

                # Service Speed 
                if object_speed['show']:
                    display_speed_calculation(frame, indexIDs[i], x, y, w, h, x2, y2, w2, h2, color, object_speed)

                # Service counting people on sight
                if people_counting['enabled']:
                    people_counting_last_time_detected(first_time_set, last_time_set, indexIDs)
                    people_counting_storing_fist_time(indexIDs[i], first_time_set)

                # Service counting in and out / aforo
                if counting_in_and_out['enabled']:
                    counting_in_and_out_first_detection(box, indexIDs[i])
                    #counting_in_and_out_first_detection(box, line1, indexIDs[i], initial, last)
                    #associate_areas_to_objects(box, line1, indexIDs[i], initial, last)

                # Service counting by intersecting in any direction
                if object_intersection['enabled'] and intersect(x, y, w, h, x2, y2, w2, h2, line1):
                    intersection_counter += 1
                    data = {
                            'camera_id': get_camera_mac_address(),
                            'date_time': get_timestamp(),
                            'object_id': indexIDs[i],
                            }
                    send_json(data, 'POST', get_service_count_intersecting_in_any_direction_url())
            i += 1

    # Draw single line
    if cfg['intersection_line']['show']:
        cv2.line(frame, line1[0], line1[1], cfg['intersection_line']['color'], cfg['intersection_line']['width'])

    # Draw counter
    display_counter_results(frame, frameIndex, counter_1_to_2, counter_2_to_1)

    if cfg['video']['output']['enable'] and cfg['video']['input']['input_type'] == 'video':
        writer = write_result_to_disk(frame, writer)

    # increase frame index
    frameIndex += 1

if variable == 'EXECUTE_ME':
    # release the file pointers
    print("[INFO] cleaning up...")
    if cfg['video']['output']['enable'] and cfg['video']['input']['input_type'] == 'video':
        writer.release()
    vs.release()
    file_handler1.close()
    file_handler2.close()
