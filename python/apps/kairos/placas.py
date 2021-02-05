#!/usr/bin/env python3

#rm ${HOME}/.cache/gstreamer-1.0/registry.aarch64.bin    borrar cache
################################################################################
# Copyright (c) 2020, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################
#
#   version 2.1 solo identificara personas y carros sin ninguna caracteristica 
#   adicional,se realiza eliminando las clases de carro, bicicleta y senal de 
#   transito con el parametro filter-out-class-ids=0;1;3 en el archivo dstest2_pgie_config.txt
#
################################################################################

import sys
sys.path.append('../')
import gi
import configparser
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from gi.repository import GLib
from ctypes import *
import time
import sys
import math
import platform
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import GETFPS
import numpy as np
import pyds
import cv2
import os
import os.path
from os import path

import re
import pyds
import services as service
import datetime


frame_count={}
saved_count={}

PGIE_CLASS_ID_FACE = 0
PGIE_CLASS_ID_PLATES = 1

# Variables adicionales para el manejo de la funcionalidad de Tiler
# independientemente como venga los parametros del video se ajusta 
# a los parametros del muxer
#

MAX_DISPLAY_LEN = 64
MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_TIMEOUT_USEC = 4000000
TILED_OUTPUT_WIDTH = 1920
TILED_OUTPUT_HEIGHT = 1080
GST_CAPS_FEATURES_NVMM = "memory:NVMM"

pgie_classes_str = ["Carita", "Placa", "Modelo", "Marca"]

# directorio actual
CURRENT_DIR = os.getcwd()

# Matriz de frames per second, Se utiliza en tiler
fps_streams = {}

global social_distance_list
global people_distance_list
global people_counting_counters
global camera_list
global source_list
global srv_url
global token_file
global entradas_salidas
global initial_last_disappeared
global social_distance_ids
global plates_dict

initial_last_disappeared = {}
source_list = []
#people_distance_list = {}
#people_counting_counters = {}
camera_list = []
#social_distance_list = {}
#entradas_salidas = {}
#social_distance_ids = {}
plates_dict = {}


def set_plate_ids_dict(camera_id, dictionary = None):
    global plates_dict

    if camera_id in plates_dict:
        plates_dict.update({camera_id: dictionary})
    else:
        plates_dict.update({camera_id: {}})


def get_plate_ids_dict(camera_id):
    global plates_dict

    if camera_id in plates_dict:
        return plates_dict[camera_id]


def get_plates_info(key_id, key = None, second_key = None):
    global plates_dict

    if key_id not in plates_dict.keys():
        return {'enabled': False}

    if key is None:
        return plates_dict[key_id]
    else:
        if second_key is None:
            return plates_dict[key_id][key]
        else:
            return plates_dict[key_id][key][second_key]


def set_reference_line_and_area_of_interest(camera_id, data):
    # use plates_dict for plates script 
    global plates_dict

    if 'reference_line_coordinates' in data and 'area_of_interest' in data and data['area_of_interest_type'] in ['horizontal', 'parallel']:
        if data['area_of_interest_type'] == 'horizontal':
            # generating left_top_xy, width and height
            x1 = data['reference_line_coordinates'][0][0]
            y1 = data['reference_line_coordinates'][0][1]
            x2 = data['reference_line_coordinates'][1][0]
            y2 = data['reference_line_coordinates'][1][1]

            left = data['area_of_interest']['left']
            right = data['area_of_interest']['right']
            up = data['area_of_interest']['up']
            down = data['area_of_interest']['down']

            if x1 < x2:
                topx = x1 - left
            else:
                topx = x2 - left

            # adjusting if value is negative
            if topx < 0:
                topx = 0

            if y1 < y2:
                topy = y1 - up
            else:
                topy = y2 - up

            # adjusting if value is negative
            if topy < 0:
                topy = 0

            width = left + right + abs(x1 - x2)
            height = up + down + abs(y1 - y2)

            if (x2 - x1) == 0:
                m = None
                b = None
            elif (y2 - y1) == 0:
                m = 0
                b = 0
            else:
                m = ((y2 - y1) * 1.0) / (x2 -x1)
                b = y1 - (m * x1)

            plates_dict.update(
                {
                    camera_id: {
                        'enabled': data['enabled'],
                        'outside_area': data['reference_line_outside_area'],
                        'coordinates': data['reference_line_coordinates'],
                        'width': data['reference_line_width'],
                        'color': data['reference_line_color'],
                        'line_m_b': [m, b],
                        'area_of_interest': {'type': data['area_of_interest_type'], 'values': [topx, topy, width, height]},
                        }
                    }
                )
        else:
            log_error("Parallel area logic not yet defined")
    elif 'reference_line_coordinates' not in data and 'area_of_interest' in data and data['area_of_interest_type'] in ['fixed']:
        topx = data['area_of_interest']['topx']
        topy = data['area_of_interest']['topy']
        width = data['area_of_interest']['width']
        height = data['area_of_interest']['height']

        plates_dict.update(
            {
                camera_id: {
                    'enabled': data['enabled'],
                    'coordinates': None,
                    'area_of_interest': {'type': data['area_of_interest_type'], 'values': [topx, topy, width, height]},
                    }
                }
            )

    elif 'reference_line_coordinates' in data and 'area_of_interest' not in data:
        x1 = data['reference_line_coordinates'][0][0]
        y1 = data['reference_line_coordinates'][0][1]
        x2 = data['reference_line_coordinates'][1][0]
        y2 = data['reference_line_coordinates'][1][1]

        if (x2 - x1) == 0:
            m = None
            b = None
        elif (y2 - y1) == 0:
            m = 0
            b = 0
        else:
            m = ((y2 - y1) * 1.0) / (x2 -x1)
            b = y1 - (m * x1)

        plates_dict.update(
                {
                    camera_id: {
                        'enabled': data['enabled'],
                        'outside_area': data['reference_line_outside_area'],
                        'coordinates': data['reference_line_coordinates'],
                        'width': data['reference_line_width'],
                        'color': data['reference_line_color'],
                        'line_m_b': [m, b],
                        'area_of_interest': {'type': data['area_of_interest_type'], 'values': None},
                        }
                    }
                )
    else:
        log_error("Missing configuration parameters for 'aforo' service")


def set_sources(value):
    global source_list

    if value:
        source_list.append(value)


def get_sources():
    global source_list
    return source_list


def set_camera(value):
    global camera_list

    if value:
        camera_list.append(value)


def get_camera_id(key_id):
    global camera_list
    return camera_list[key_id]


def set_server_url(url):
    if isinstance(url, str):
        global srv_url
        srv_url = url
        return True
    log_error("'url' parameter, most be a valid string")


def set_token(token_file_name):
    if isinstance(token_file_name, str) and service.file_exists(token_file_name):
        global token_file
        token_file = token_file_name
        return True
    log_error("'token_file_name={}' parameter, most be a valid string".format(token_file_name))


def set_number_of_resources(num):
    if isinstance(num, int):
        global number_of_resources
        number_of_resources = num
        return True
    log_error("'num={}' parameter, most be integer".format(num))


def validate_plate_values(data):

    if 'enabled' not in data.keys():
        log_error('validate_plate_values() - Key element enabled does not exists in the data provided:\n\n {}'.format(data))
    else:
        if not isinstance(data['enabled'], str):
            log_error("'aforo_data' parameter, most be True or False, current value: {}".format(data['enabled']))

    # For plates we will use the reference line and then the area of interest if there is one defined
    if 'reference_line_coordinates' in data.keys() and 'area_of_interest' in data.keys() and data['reference_line_coordinates'] != '' and data['area_of_interest'] != '':
        reference_line_coordinates = data['reference_line_coordinates']
        reference_line_coordinates = reference_line_coordinates.replace('(', '')
        reference_line_coordinates = reference_line_coordinates.replace(')', '')
        reference_line_coordinates = reference_line_coordinates.replace(' ', '')
        reference_line_coordinates = reference_line_coordinates.split(',')
        try:
            reference_line_coordinates = [(int(reference_line_coordinates[0]), int(reference_line_coordinates[1])), (int(reference_line_coordinates[2]), int(reference_line_coordinates[3]))]
            data.update({'reference_line_coordinates': reference_line_coordinates})
        except Exception as e:
            log_error("Exception: Unable to create reference_line_coordinates".format(str(e)))

        if not isinstance(data['reference_line_coordinates'], list):
            log_error("reference_line_coordinate, most be a list. Undefining variable")

        if len(data['reference_line_coordinates']) != 2:
            log_error("coordinates, most be a pair of values.")

        for coordinate in data['reference_line_coordinates']:
            if not isinstance(coordinate[0], int) or not isinstance(coordinate[1], int):
                log_error("coordinates elements, most be integers")

        if 'reference_line_width' not in data.keys():
            data.update({'reference_line_width': 2})
        else:
            new_value = float(data['reference_line_width'])
            new_value = int(new_value)
            data.update({'reference_line_width': new_value})

        if 'reference_line_color' not in data.keys():
            data.update({'reference_line_color': [1, 1, 1, 1]})
        else:
            reference_line_color = reference_line_color.replace('(', '')
            reference_line_color = reference_line_color.replace(')', '')
            reference_line_color = reference_line_color.replace(' ', '')
            reference_line_color = reference_line_color.split(',')
            try:
                reference_line_color = [int(reference_line_color[0]), int(reference_line_color[1]), int(reference_line_color[2]), int(reference_line_color[3])]
                data.update({'reference_line_color': reference_line_color})
            except Exception as e:
                log_error("Exception: Unable to create reference_line_color".format(str(e)))

        if not isinstance(data['reference_line_color'], list):
            log_error("coordinates color elements, most be a list of integers")

        for color in data['reference_line_color']:
            if not isinstance(color, int) or color < 0 or color > 255:
                log_error("color values should be integers and within 0-255")

        if 'reference_line_outside_area' not in data.keys():
            log_error("If reference line is define 'outside_area' must also be defined")
        else:
            reference_line_outside_area = float(data['reference_line_outside_area'])
            reference_line_outside_area = int(reference_line_outside_area)
            if reference_line_outside_area not in [1, 2]:
                log_error("outside_area, most be an integer 1 or 2")
            data.update({'reference_line_outside_area': reference_line_outside_area})

        ####### if area of interest is defined
        if 'area_of_interest_type' not in data.keys():
            log_error("Missing 'type' in 'area_of_interest' object")

        if data['area_of_interest_type'] not in ['horizontal', 'parallel', 'fixed']:
            log_error("'type' object value must be 'horizontal', 'parallel' or 'fixed'")

        UpDownLeftRight = data['area_of_interest'].replace(' ', '')
        UpDownLeftRight = UpDownLeftRight.split(',')
        try:
            data.update({'area_of_interest': {'up': int(UpDownLeftRight[0]), 'down': int(UpDownLeftRight[1]), 'left': int(UpDownLeftRight[2]), 'right': int(UpDownLeftRight[3])} })
        except Exception as e:
            log_error("Exception: Unable to create reference_line_color".format(str(e)))

        if data['area_of_interest_type'] == 'horizontal':
            horizontal_keys = ['up', 'down', 'left', 'right']
            for param in horizontal_keys:
                if param not in data['area_of_interest'].keys():
                    log_error("Missing '{}' parameter in 'area_of_interest' object".format(param))

                if not isinstance(data['area_of_interest'][param], int) or data['area_of_interest'][param] < 0:
                    log_error("{} value should be integer and positive".format(params))
        elif data['area_of_interest_type'] == 'parallel':
            print('type parallel not defined')
        elif data['area_of_interest_type'] == 'fixed':
            inner_keys = ['topx', 'topy', 'height', 'width']
            for param in inner_keys:
                if param not in data['area_of_interest'].keys():
                    log_error("Missing '{}' parameter in 'area_of_interest' object".format(param))
                if not isinstance(data['area_of_interest'][param], int) or data['area_of_interest'][param] < 0:
                    log_error("{} value should be integer and positive".format(params))

    else:
        log_error("Reference line and Area of interest not defined")

    return True


def log_error(msg):
    print("-- PARAMETER ERROR --\n"*5)
    print(" %s \n" % msg)
    print("-- PARAMETER ERROR --\n"*5)
    quit()


def reading_server_config():
    #scfg = service.get_server_info()
    scfg = {
        'CajaLosAndes-ac:17:c8:62:08:5b': 
            {
            'video-plateDetection': 
                {
                'reference_line_coordinates': '(500, 720), (1100, 720)', 
                'reference_line_outside_area': '1.0', 
                'source': 'file:///home/aaeon/video2.mp4',
                'area_of_interest': '90,90,0,0', 
                'area_of_interest_type': 'horizontal',
                'enabled': 'True'
                },
            'video-maskDetection': 
                {
                'source': 'rtsp://192.168.127.2:9000/live', 
                'enabled': 'False'
                }, 
            'video-socialDistancing': 
                {
                'tolerated_distance': '150.0', 
                'source': 'rtsp://192.168.127.2:9000/live', 
                'persistence_time': '2.0', 
                'enabled': 'False'
                }, 
            'video-people': 
                {
                'reference_line_coordinates': '(500, 720), (1100, 720)', 
                'MaxAforo': '', 
                'reference_line_outside_area': '1.0', 
                'source': 'rtsp://192.168.127.2:9000/live', 
                'area_of_interest': '', 
                'enabled': 'False', 
                'area_of_interest_type': ''
                }
            }, 
        'DTevar-culhuacan-34:56:fe:a3:99:de': 
            {
            'video-socialDistancing': 
                {
                'tolerated_distance': '100.0', 
                'source': 'rtsp://192.168.128.3:9000/live', 
                'persistence_time': '2.0', 
                'enabled': 'False'
                }, 
            'video-people': 
                {
                'reference_line_coordinates': '(500, 720), (1100, 720)', 
                'MaxAforo': '20.0', 
                'reference_line_outside_area': '1.0', 
                'source': 'rtsp://192.168.128.3:9000/live', 
                'area_of_interest': '90,90,0,0', 
                'enabled': 'False', 
                'area_of_interest_type': 'horizontal'
                }
            }, 
        'OK': True
    }

    for camera in scfg.keys():
        if camera == 'OK':
            continue

        activate_service = False
        source = None

        for key in scfg[camera].keys():
            if key == 'video-plateDetection' and validate_plate_values(scfg[camera][key]) and scfg[camera][key]['enabled']:
                source = scfg[camera][key]['source']
                set_plate_ids_dict(camera)
                service.set_plate_detection_url()
                set_reference_line_and_area_of_interest(camera, scfg[camera][key])
                activate_service = True

        if activate_service:
            set_camera(camera)
            set_sources(source)


def tiler_src_pad_buffer_probe(pad, info, u_data):
    # Intiallizing object counter with 0.
    # version mask detection solo reconoce mascarillas y sin mascarilla
    obj_counter = {
            PGIE_CLASS_ID_FACE: 0,
            PGIE_CLASS_ID_PLATES: 0,
            }

    frame_number = 0
    num_rects = 0                      # numero de objetos en el frame
    gst_buffer = info.get_buffer()

    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list

    #====================== Definicion de valores de mensajes a pantalla
    display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
    current_pad_index = pyds.NvDsFrameMeta.cast(l_frame.data).pad_index

    camera_id = get_camera_id(current_pad_index)

    plates_info = get_plates_info(camera_id) 
    #print('information edgar')
    #print(plates_info)
    #quit()
    #is_aforo_enabled = aforo_info['enabled']

    #social_distance_info = get_social_distance(camera_id)
    #is_social_distance_enabled = social_distance_info['enabled']

    #people_counting_info = get_people_counting(camera_id)
    #is_people_counting_enabled = people_counting_info['enabled']

    #print( "entro al  tiler_src_pad_buffer_probe")
    # Todos los servicios requieren impresion de texto solo para Aforo se requiere una linea y un rectangulo
    display_meta.num_labels = 1                            # numero de textos
    py_nvosd_text_params = display_meta.text_params[0]

    # Setup del label de impresion en pantalla
    py_nvosd_text_params.x_offset = 100
    py_nvosd_text_params.y_offset = 120
    py_nvosd_text_params.font_params.font_name = "Arial"
    py_nvosd_text_params.font_params.font_size = 10
    py_nvosd_text_params.font_params.font_color.red = 1.0
    py_nvosd_text_params.font_params.font_color.green = 1.0
    py_nvosd_text_params.font_params.font_color.blue = 1.0
    py_nvosd_text_params.font_params.font_color.alpha = 1.0
    py_nvosd_text_params.set_bg_clr = 1
    py_nvosd_text_params.text_bg_clr.red = 0.0
    py_nvosd_text_params.text_bg_clr.green = 0.0
    py_nvosd_text_params.text_bg_clr.blue = 0.0
    py_nvosd_text_params.text_bg_clr.alpha = 1.0

    plate_ids = get_plate_ids_dict(camera_id)
    # por que ponerlo en 1 ????
    #frame_number = 1 # to avoid not definition issue

    #client=boto3.client('rekognition')

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break
        frame_number = frame_meta.frame_num
        
        l_obj = frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        
        save_image = False

        #print(num_rects) ID numero de stream
        #ids = set()
  
        # fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()
        
        # Ciclo interno donde se evaluan los objetos dentro del frame
        while l_obj is not None: 
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)         
            except StopIteration:
                break           
            
            obj_counter[obj_meta.class_id] += 1
            
            # if class is 1 (plate) and only every other frame
            # TODO hay que utilizar la informacion en plates_info para determinar si esta dentro del area de interes y si esta entrando o saliendo y solo tomar las imagenes de cuando este entrando
            print(plates_info)
            #if obj_meta.class_id == 1 and frame_number % 2 == 0:
            if obj_meta.class_id == 1:
                #save_image = True

                if obj_meta.object_id not in plate_ids:
                    counter = 1
                    items = []
                else:
                    counter = plate_ids[obj_meta.object_id]['counter']
                    items = plate_ids[obj_meta.object_id]['items']
                    counter += 1

                print('X..............', int(obj_meta.rect_params.width + obj_meta.rect_params.left/2))
                print('Y..............', int(obj_meta.rect_params.height + obj_meta.rect_params.top))
            
                # Getting Image data using nvbufsurface
                # the input should be address of buffer and batch_id
                n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)

                # convert python array into numy array format.
                frame_image = np.array(n_frame,copy=True,order='C')

                # convert the array into cv2 default color format
                frame_image = cv2.cvtColor(frame_image, cv2.COLOR_RGBA2BGRA)

                # crop image
                frame_image = draw_bounding_boxes(frame_image, obj_meta, obj_meta.confidence)
                items.append(frame_image)

                plate_ids.update({obj_meta.object_id: {'counter': counter, 'items': items}})
                #print('edgar...', plate_ids)
                set_plate_ids_dict(camera_id, plate_ids)
                for elemento in plate_ids.keys():
                    #print('11111111111', elemento)
                    #print('22222222222', type(elemento))
                    #print('33333333333', plate_ids)
                    #print('44444444444', plate_ids[elemento])
                    #print('55555555555', plate_ids[obj_meta.object_id]['counter'])
                    if plate_ids[obj_meta.object_id]['counter'] > 1:
                        print('................', frame_number, elemento, 'photo:', len(plate_ids[obj_meta.object_id]['items']))
                        cv2.imwrite(folder_name + "/stream_" + str(frame_meta.pad_index) + "/" + str(service.get_timestamp()) + "_" + str(obj_meta.object_id) + ".jpg", frame_image)
                 
            #py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Mask={} NoMaks={}".format(frame_number, num_rects, obj_counter[PGIE_CLASS_ID_FACE], obj_counter[PGIE_CLASS_ID_PLATES])

            try: 
                l_obj = l_obj.next
            except StopIteration:
                break
        

        #pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()
        #fps_streams["stream{0}".format(frame_meta.pad_index)].print_data()
        #print("stream{0}".format(frame_meta.pad_index))

        if save_image:
            #print("Entre a guardar imagen")
            #print(obj_meta.class_id)
            
            # El nombre del archivo debe estar formado por date+id
 
            #cv2.imwrite(folder_name+"/stream_"+str(frame_meta.pad_index)+"/frame_"+str(frame_number)+".jpg",frame_image)
            #print(str(service.get_timestamp()))
            #print(str(service.get_timestamp()/1000))
            a = 1
            cv2.imwrite(folder_name+"/stream_" + str(frame_meta.pad_index) + "/" + str(service.get_timestamp()) + "_" + str(obj_meta.object_id) + ".jpg", frame_image)

        saved_count["stream_"+str(frame_meta.pad_index)]+=1
      
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    '''
    if frame_number % 43 == 0:
        new_dict = {}
        no_mask_ids = get_plate_ids_dict(camera_id)

        for item in ids:
            if item in no_mask_ids:
                value = no_mask_ids[item]
                new_dict.update({item: value})

        set_plates_dict(camera_id, new_dict)

        # Lo manda a directo streaming
    '''

    return Gst.PadProbeReturn.OK	


def draw_bounding_boxes(image, obj_meta, confidence):
    confidence='{0:.2f}'.format(confidence)
    rect_params=obj_meta.rect_params
   
    # Cuando se hace el tracking se modifican las coordenadas 
    # conforme al archivo dtest2_tracker_config.txt
    
    #top=int(rect_params.top)
    #left=int(rect_params.left)
    #width=int(rect_params.width)
    #height=int(rect_params.height)
    #print("Top :"+str(top))
    #print("Left :"+str(left))
    #print("Widht :"+str(width))
    #print("Height :"+str(height))

    top=int(rect_params.height)
    left=int(rect_params.width)
    width=int(rect_params.left)
    height=int(rect_params.top)


    obj_name = pgie_classes_str[obj_meta.class_id]
    #image=cv2.rectangle(image,(left,top),(left+width,top+height),(0,0,255,0),2)
    #image=cv2.line(image, (left,top),(left+width,top+height), (0,255,0), 9)
    # Note that on some systems cv2.putText erroneously draws horizontal lines across the image
    #image=cv2.putText(image,obj_name+',C='+str(confidence),(left+10,top+10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255,0),2)
    #crop_image = image[top-10:top+height+20,left-10:left+width+20]
    crop_image = image[top:top+height, left:left+width]
    return crop_image

def cb_newpad(decodebin, decoder_src_pad, data):
    print("In cb_newpad\n")
    caps = decoder_src_pad.get_current_caps()
    gststruct = caps.get_structure(0)
    gstname = gststruct.get_name()
    source_bin = data
    features = caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not audio.
    print("gstname=", gstname)
    if gstname.find("video") != -1:
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        print("features=", features)
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad = source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")


def decodebin_child_added(child_proxy, Object, name, user_data):
    print("Decodebin child added:", name, "\n")
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)
    if is_aarch64() and name.find("nvv4l2decoder") != -1:
        print("Seting bufapi_version\n")
        Object.set_property("bufapi-version", True)


def create_source_bin(index, uri):
    print("Creating source bin")

    # Create a source GstBin to abstract this bin's content from the rest of the pipeline
    bin_name = "source-bin-%02d" % index
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")

    # Source element for reading from the uri.
    # We will use decodebin and let it figure out the container format of the
    # stream and the codec and plug the appropriate demux and decode plugins.
    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri", uri)
    uri_decode_bin.connect("pad-added", cb_newpad, nbin)
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)

    Gst.Bin.add(nbin, uri_decode_bin)
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin


def main():
    # Check input arguments
    # Permite introducir un numero x de fuentes, en nuestro caso streamings delas camaras Meraki        
    reading_server_config()    

    number_sources = len(get_sources()) 

    if number_sources < 1:
        log_error("No source to analyze or not service associated to the source. check configuration file")

    # Variable para verificar si al menos un video esta vivo
    is_live = False

    for i in range(0, number_sources):
        fps_streams["stream{0}".format(i)] = GETFPS(i)
        #print(fps_streams["stream{0}".format(i)])
 
    
    global folder_name
    #folder_name=args[-1]
    folder_name = "frames"
    folder_name = "placas_encontrada"
    if not path.exists(folder_name):
        os.mkdir(folder_name)
    #    sys.stderr.write("The output folder %s already exists. Please remove it first.\n" % folder_name)
    #    sys.exit(1)

    
    print("Frames will be saved in ",folder_name)    
   
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create gstreamer elements
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    is_live = False

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")

    # Source element for reading from the file
    print("Creating Source \n ")
    
    # Create nvstreammux instance to form batches from one or more sources.
    
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")

    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")
    pipeline.add(streammux)
    
    # Se crea elemento que acepta todo tipo de video o RTSP
    i = 0
    for source in get_sources():
   
        if not path.exists(folder_name+"/stream_"+str(i)):
            os.mkdir(folder_name+"/stream_"+str(i))
        frame_count["stream_"+str(i)]=0
        saved_count["stream_"+str(i)]=0

        print("Creating source_bin...........", i, '.-', source, " \n ")
        uri_name = source

        if uri_name.find("rtsp://") == 0:
            print('is_alive_TRUE')
            is_live = True

        source_bin = create_source_bin(i, uri_name)

        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")

        pipeline.add(source_bin)
        padname = "sink_%u" % i
        sinkpad = streammux.get_request_pad(padname)

        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")

        srcpad = source_bin.get_static_pad("src")

        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")

        srcpad.link(sinkpad)
        i += 1
    
    # el video con RTSP para Meraki viene optimizado a H264, por lo que no debe ser necesario crear un elemento h264parser stream
    # print("Creating H264Parser \n")
    h264parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    if not h264parser:
        sys.stderr.write(" Unable to create h264 parser \n")

    print("Creating Decoder \n")
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    if not decoder:
        sys.stderr.write(" Unable to create Nvv4l2 Decoder \n")

    # Use nvinfer to run inferencing on decoder's output,
    # behaviour of inferencing is set through config file
    
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")


    # Add nvvidconv1 and filter1 to convert the frames to RGBA
    # which is easier to work with in Python.
    print("Creating nvvidconv1 \n ")
    nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "convertor1")
    if not nvvidconv1:
        sys.stderr.write(" Unable to create nvvidconv1 \n")
    print("Creating filter1 \n ")
    caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
    filter1 = Gst.ElementFactory.make("capsfilter", "filter1")
    if not filter1:
        sys.stderr.write(" Unable to get the caps filter1 \n")
    filter1.set_property("caps", caps1)

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")

    #
    #  version 2.1 no realizara inferencias secundarias.
    #  por lo que sgie1, sgie2 y sgie3 no estaran habilitados
    #
    
    #sgie1 = Gst.ElementFactory.make("nvinfer", "secondary1-nvinference-engine")
    #if not sgie1:
    #    sys.stderr.write(" Unable to make sgie1 \n")

    #sgie2 = Gst.ElementFactory.make("nvinfer", "secondary2-nvinference-engine")
    #if not sgie1:
    #    sys.stderr.write(" Unable to make sgie2 \n")

    #sgie3 = Gst.ElementFactory.make("nvinfer", "secondary3-nvinference-engine")
    #if not sgie3:
    #    sys.stderr.write(" Unable to make sgie3 \n")
        
    #
    #   La misma version 2.1 debe permitir opcionalmente mandar a pantalla o no
    #

    print("Creating tiler \n ")
    tiler = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
    if not tiler:
        sys.stderr.write(" Unable to create tiler \n")
    
   
         
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")
    

    # Create OSD to draw on the converted RGBA buffer
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")

    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")

    # Finally render the osd output
    if is_aarch64():
        transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")

    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")
    sink.set_property('sync', 0)


    if is_live:
        print("At least one of the sources is live")
        streammux.set_property('live-source', 1)
        #streammux.set_property('live-source', 1)
        
    # Tamano del streammux, si el video viene a 720, se ajusta automaticamente

    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    #
    # Configuracion de modelo
    # dstest2_pgie_config contiene modelo estandar, para  yoloV3, yoloV3_tiny y fasterRCNN
    #

    #pgie.set_property('config-file-path', CURRENT_DIR + "/configs/dstest2_pgie_config.txt")
    #pgie.set_property('config-file-path', CURRENT_DIR + "/configs/config_infer_primary_nano.txt") 
    #pgie.set_property('config-file-path', CURRENT_DIR + "/configs/deepstream_app_source1_video_masknet_gpu.txt")
    #pgie.set_property('config-file-path', CURRENT_DIR + "/configs/config_infer_primary_yoloV3.txt")
    #pgie.set_property('config-file-path', CURRENT_DIR + "/configs/kairos_peoplenet_pgie_config.txt")
    # pgie.set_property('config-file-path', CURRENT_DIR + "/configs/config_infer_primary_yoloV3_tiny.txt")
    # pgie.set_property('config-file-path', CURRENT_DIR + "/configs/config_infer_primary_fasterRCNN.txt")
    # Falta añadir la ruta completa del archivo de configuracion


    pgie.set_property('config-file-path', CURRENT_DIR + "/configs/pgie_config_fd_lpd.txt")    # modelo para caras, placas, modelo y marca
    pgie_batch_size = pgie.get_property("batch-size")
    print(pgie_batch_size)
    if pgie_batch_size != number_sources:
        print("WARNING: Overriding infer-config batch-size", pgie_batch_size,
              " with number of sources ", number_sources, " \n")
        pgie.set_property("batch-size", number_sources)
    
    # Set properties of pgie and sgiae
    # version 2.1 no configura inferencias secundarias
    #

    #sgie1.set_property('config-file-path', CURRENT_DIR + "/configs/dstest2_sgie1_config.txt")
    #sgie2.set_property('config-file-path', CURRENT_DIR + "/configs/dstest2_sgie2_config.txt")
    #sgie3.set_property('config-file-path', CURRENT_DIR + "/configs/dstest2_sgie3_config.txt")
    
    # Set properties of tracker
    config = configparser.ConfigParser()
    config.read('configs/Plate_tracker_config.txt')
    #config.read('configs/kairos_peoplenet_tracker_config.txt')
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width':
            tracker_width = config.getint('tracker', key)
            print(tracker_width)
            tracker.set_property('tracker-width', tracker_width)
        elif key == 'tracker-height':
            tracker_height = config.getint('tracker', key)
            print(tracker_height)
            tracker.set_property('tracker-height', tracker_height)
        elif key == 'gpu-id':
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        elif key == 'll-lib-file':
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        elif key == 'll-config-file':
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        elif key == 'enable-batch-process':
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)
            
    # Creacion del marco de tiler 
    tiler_rows = int(math.sqrt(number_sources))                           # Example 3 = 1 renglones 
    tiler_columns = int(math.ceil((1.0 * number_sources)/tiler_rows))     # Example 3 = 3 columnas 
    tiler.set_property("rows", tiler_rows)
    tiler.set_property("columns", tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)
    tiler.set_property("height", TILED_OUTPUT_HEIGHT)
            
    print("Adding elements to Pipeline \n")
    
    #
    #  version 2.1 no requiere inferencias secundarias
    #
    pipeline.add(h264parser)    # agrego h264
    pipeline.add(decoder)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(tiler)
    pipeline.add(nvvidconv1)      # Se anaden para un mejor manejo de la imagen
    pipeline.add(filter1)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
    if is_aarch64():
        pipeline.add(transform)

    # we link the elements together
    # source_bin -> -> nvh264-decoder -> PGIE -> Tracker
    # tiler -> nvvidconv -> nvosd -> video-renderer
    print("Linking elements in the Pipeline \n")
    
    

    # lineas ya ejecutadas en el for anterior
    #sinkpad = streammux.get_request_pad("sink_0")
    #if not sinkpad:
    #    sys.stderr.write(" Unable to get the sink pad of streammux \n")
    #srcpad = decoder.get_static_pad("src")
    #if not srcpad:
    #    sys.stderr.write(" Unable to get source pad of decoder \n")

    srcpad.link(sinkpad)
    source_bin.link(h264parser)
    h264parser.link(decoder)     
    decoder.link(streammux)
    # -------
    streammux.link(pgie)
    pgie.link(nvvidconv1)
    nvvidconv1.link(filter1)
    filter1.link(tracker)
    tracker.link(tiler)
    #filter1.link(tiler)
    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    if is_aarch64():
        nvosd.link(transform)
        transform.link(sink)
    else:
        nvosd.link(sink)

    #pgie.link(tracker)

    '''
    srcpad.link(sinkpad)
    source_bin.link(h264parser)
    h264parser.link(decoder)     
    #source_bin.link(decoder)     Se agregaron las dos lineas anteriores
    decoder.link(streammux)
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(tiler)
    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    
    if is_aarch64():
        nvosd.link(transform)
        transform.link(sink)
    else:
        nvosd.link(sink)

    '''

    # create and event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.

    tiler_src_pad = tracker.get_static_pad("src")
    if not tiler_src_pad:
        sys.stderr.write(" Unable to get src pad \n")
    else:
        tiler_src_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_src_pad_buffer_probe, 0)
    
    print("Starting pipeline \n")
    pipeline.set_state(Gst.State.PLAYING)
    
    # start play back and listed to events
    try:
        loop.run()
    except Exception as e:
        print("This line? "+str(e))
        pass

    # cleanup
    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main())
