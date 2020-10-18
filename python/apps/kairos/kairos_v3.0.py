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
import os
import re
sys.path.append('../')
import platform
import configparser

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import GETFPS

import pyds
import services as service

#Bibliotecas Adicioanles para la funcionaliad con Tiler
from gi.repository import GLib
from ctypes import *
import time
import math
import datetime



#
#  version 2.1 solo detectara personas
#  sin embargo la logica del programa permite 
#  seguir contando otras clases si asi se 
#  requiriera
#

PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

#PEOPLE_COUNTING_SERVICE = 0
#AFORO_ENT_SAL_SERVICE = 1
#SOCIAL_DISTANCE_SERVICE = 2

#
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

#pgie_classes_str = ["Vehicle", "TwoWheeler", "Person", "RoadSign"]

# directorio actual
CURRENT_DIR = os.getcwd()

# Matriz de frames per second, Se utiliza en tiler
fps_streams = {}

global aforo_list
global social_distance_list
global people_counting_list
global camera_list
global source_list
global srv_url
global token_file
global entradas_salidas
global initial_last_disappeared
global dict_of_ids_list

initial_last_disappeared = {}
source_list = []
aforo_list = {}
entradas_salidas = {}
dict_of_ids_list = {}


def set_social_distance_dict_of_ids(key_id):
    global dict_of_ids_list
    dict_of_ids_list.update({key_id: {}})


def get_socialt_distance_dict_of_ids(key_id):
    global dict_of_ids_list
    return dict_of_ids_list[key_id]


def set_initial_last_disappeared(key_id):
    global initial_last_disappeared
    initial_last_disappeared.update({key_id: [{}, {}, []]})


def get_initial_last(key_id):
    global initial_last_disappeared
    return initial_last_disappeared[key_id][0], initial_last_disappeared[key_id][1]


def set_disappeared(key_id, value = None):
    global initial_last_disappeared
    if value is None:
        initial_last_disappeared[key_id][2] = []
    else:
        initial_last_disappeared[key_id][2] = value


def get_disappeared(key_id):
    global initial_last_disappeared
    return initial_last_disappeared[key_id][2]


def set_people_counting(value=None):
    global people_counting_list
    if value is None:
        people_counting_list = []
    else:
        people_counting_list.append(value)


def get_people_counting(index = None, key = None):
    global people_counting_list
    if index is None:
        return people_counting_list
    else:
        return people_counting_list[index][key]


def set_social_distance(key_id = None, value=None):
    global social_distance_list
    if key_id is None:
        social_distance_list = {}
    else:
        social_distance_list.update({key_id: value})


def get_social_distance(key_id, key = None):
    global social_distance_list
    if key_id is None:
        return social_distance_list
    else:
        return social_distance_list[key_id][key]


def get_aforo(key_id = None, key = None, second_key = None):
    global aforo_list
    if key_id is None:
        return aforo_list
    else:
        if key is None:
            return aforo_list[key_id]
        else:
            if second_key is None:
                return aforo_list[key_id][key]
            else:
                return aforo_list[key_id][key][second_key]


def set_camera(value=None):
    global camera_list
    if value is None:
        camera_list = []
    else:
        camera_list.append(value)


def set_sources(value):
    global source_list
    source_list.append(value)


def get_sources():
    global source_list
    return source_list


def get_camera_id(index = None):
    global camera_list
    if index is None:
        return camera_list
    else:
        return camera_list[index]


def set_server_url(url):
    global srv_url
    srv_url = url


def set_token(token_file_name):
    global token_file
    token_file = token_file_name


def set_number_of_resources(num):
    global number_of_resources
    number_of_resources = num


def set_entrada_salida(key_id, entrada, salida):
    global entradas_salidas
    entradas_salidas.update({key_id: [entrada, salida]})


def get_entrada_salida(key_id):
    global entradas_salidas
    return entradas_salidas[key_id][0], entradas_salidas[key_id][1]


def log_error(msg):
    print("-- PARAMETER ERROR --\n"*5)
    print(" %s \n" % msg)
    print("-- PARAMETER ERROR --\n"*5)
    quit()


def set_aforo(key_id, aforo_data):
    global aforo_list

    if not isinstance(aforo_data, dict):
        log_error("'aforo_data' parameter, most be a dictionary")

    if aforo_data['enabled'] not in [True, False]:
        log_error("'aforo_data' parameter, most be True or False")

    if aforo_data['outside_area'] not in [1, 2]:
        log_error("'outside_area' parameter, most be 1 or 2.")

    if not isinstance(aforo_data['reference_line'], dict):
        log_error("reference_line, most be a dictionary. Undefining variable")

    # validate coordinate values exist and are integer or floats
    if len(aforo_data['reference_line']['coordinates']) != 2:
        log_error("coordinates, most be a pair of values.")

    for coordinate in aforo_data['reference_line']['coordinates']:
        if not isinstance(coordinate[0], int) or not isinstance(coordinate[1], int):
            log_error("coordinates elements, most be integers")

    if not isinstance(aforo_data['reference_line']['width'], int):
        log_error("coordinates elements, most be integers")

    if not isinstance(aforo_data['reference_line']['color'], list):
        log_error("coordinates elements, most be integers")

    for color in aforo_data['reference_line']['color']:
        if not isinstance(color, int) or color < 0 or color > 255:
            log_error("color values should be integers and within 0-255")

    if 'area_of_interest' in aforo_data['reference_line']:
        if not isinstance(aforo_data['reference_line']['area_of_interest'], dict):
            log_error("area of interest, most be a dictionary")
        
        if aforo_data['reference_line']['area_of_interest']['type'] not in ['horizontal', 'fixed', 'follow']:
            log_error("area of interest type, most be any of the values: ['horizontal', 'fixed', 'follow']")
        
        if aforo_data['reference_line']['area_of_interest']['type'] in ['horizontal', 'follow']:
            if isinstance(aforo_data['reference_line']['area_of_interest']['up'], int) and isinstance(aforo_data['reference_line']['area_of_interest']['down'], int) and isinstance(aforo_data['reference_line']['area_of_interest']['left'], int) and isinstance(aforo_data['reference_line']['area_of_interest']['right'], int) and aforo_data['reference_line']['area_of_interest']['up'] > -1 and aforo_data['reference_line']['area_of_interest']['down'] > -1 and aforo_data['reference_line']['area_of_interest']['left'] > -1 and aforo_data['reference_line']['area_of_interest']['right'] > -1: 

                # generating left_top_xy, width and height
                x1 = aforo_data['reference_line']['coordinates'][0][0]
                y1 = aforo_data['reference_line']['coordinates'][0][1]
                x2 = aforo_data['reference_line']['coordinates'][1][0]
                y2 = aforo_data['reference_line']['coordinates'][1][1]
                left = aforo_data['reference_line']['area_of_interest']['left']
                right = aforo_data['reference_line']['area_of_interest']['right']
                up = aforo_data['reference_line']['area_of_interest']['up']
                down = aforo_data['reference_line']['area_of_interest']['down']

                if x1 < x2:
                    topx = x1 - left
                else:
                    topx = x2 - left

                if y1 > y2:
                    topy = y1 - up
                else:
                    topy = y2 - up

                width = left + right + abs(x1 - x2)
                height = up + down + abs(y1 - y2)

                aforo_list.update(
                    {
                        key_id: {
                            'enabled': aforo_data['enabled'],
                            'outside_area': aforo_data['outside_area'],
                            'coordinates': aforo_data['reference_line']['coordinates'],
                            'width': aforo_data['reference_line']['width'],
                            'color': aforo_data['reference_line']['color'],
                            'area_of_interest': [topx, topy, width, height],
                            }
                        }
                    )
            else:
                log_error("area of interest values, most be positive integers")
        else:
            print('setup2 ...') 
    else:
        aforo_list.update(
                {
                    key_id: {
                        'enabled': aforo_data['enabled'],
                        'outside_area': aforo_data['outside_area'],
                        'coordinates': aforo_data['reference_line']['coordinates'],
                        'width': aforo_data['reference_line']['width'],
                        'color': aforo_data['reference_line']['color'],
                        'area_of_interest': None,
                        }
                    }
                )


def reading_server_config():
    from configs.Server_Emulatation_configs import config as scfg

    # setup the services for each camera
    set_people_counting()
    set_social_distance()
    set_camera()

    set_server_url(scfg['server']['url'])
    set_token(scfg['server']['token_file'])
    set_number_of_resources(len(scfg['cameras']))

    for camera in scfg['cameras'].keys():
        set_camera(camera)
        for key in scfg['cameras'][camera].keys():
            if key == 'source':
                set_sources(scfg['cameras'][camera][key])
            elif key == 'aforo':
                set_aforo(camera, scfg['cameras'][camera][key])
                set_initial_last_disappeared(camera)
                set_entrada_salida(camera, 0, 0)
            elif key == 'people_counting':
                set_people_counting(scfg['cameras'][camera][key])
            elif key == 'social_distance':
                set_social_distance(camera, scfg['cameras'][camera][key])
                set_social_distance_dict_of_ids(camera)


def tiler_src_pad_buffer_probe(pad, info, u_data):

    # Intiallizing object counter with 0.
    # version 2.1 solo personas
    global srv_url
    global token_file
    service.set_header(token_file)

    obj_counter = {
            PGIE_CLASS_ID_VEHICLE: 0,
            PGIE_CLASS_ID_PERSON: 0,
            PGIE_CLASS_ID_BICYCLE: 0,
            PGIE_CLASS_ID_ROADSIGN: 0
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
    aforo_info = get_aforo(camera_id) 
    is_aforo_enabled = aforo_info['enabled']
    is_social_distance_enabled = get_social_distance(camera_id, 'enabled')

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

    if is_aforo_enabled:
        service.set_aforo_url(srv_url)
        outside_area = aforo_info['outside_area']
        reference_line = aforo_info['coordinates']
        aforo_line_color = aforo_info['color']

        #------------------------------------------- display info
        display_meta.num_lines = 1      # numero de lineas
        display_meta.num_rects = 1      # numero de rectangulos  
        py_nvosd_line_params = display_meta.line_params[0]                
        py_nvosd_rect_params = display_meta.rect_params[0]        

        # Setup de la linea de Ent/Sal
        # los valos de las coordenadas tienen que ser obtenidos del archivo de configuracion
        # en este momento estan hardcode

        py_nvosd_line_params.x1 = reference_line[0][0]
        py_nvosd_line_params.y1 = reference_line[0][1]
        py_nvosd_line_params.x2 = reference_line[1][0]
        py_nvosd_line_params.y2 = reference_line[1][1]
        py_nvosd_line_params.line_width = aforo_info['width']
        py_nvosd_line_params.line_color.red = aforo_line_color[0]
        py_nvosd_line_params.line_color.green = aforo_line_color[1]
        py_nvosd_line_params.line_color.blue = aforo_line_color[2]
        py_nvosd_line_params.line_color.alpha = aforo_line_color[3]

        if aforo_info['area_of_interest']:
            '''
            # setup del rectangulo de Ent/Sal                        #TopLeftx, TopLefty --------------------
            # de igual manera que los parametros de linea,           |                                      |
            # los valores del rectangulo se calculan en base a       |                                      |
            # los valoes del archivo de configuracion                v                                      |
            #                                                        #Height -------------------------> Width
            '''

            TopLeftx = aforo_info['area_of_interest'][0]
            TopLefty = aforo_info['area_of_interest'][1]
            Width = aforo_info['area_of_interest'][2]
            Height = aforo_info['area_of_interest'][3]

            py_nvosd_rect_params.left = TopLeftx
            py_nvosd_rect_params.height = Height
            py_nvosd_rect_params.top = TopLefty
            py_nvosd_rect_params.width = Width

            py_nvosd_rect_params.border_width = 4
            py_nvosd_rect_params.border_color.red = 0.0
            py_nvosd_rect_params.border_color.green = 0.0
            py_nvosd_rect_params.border_color.blue = 1.0
            py_nvosd_rect_params.border_color.alpha = 1.0

    if is_social_distance_enabled:
        service.set_social_distance_url(srv_url)
        nfps = 19 # HARDCODED TILL GET THE REAL VALUE
        risk_value = nfps * get_social_distance(camera_id, 'persistence_time')
        tolerated_distance = get_social_distance(camera_id, 'tolerated_distance')

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number = frame_meta.frame_num
        l_obj = frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        
        ids = []
        boxes = []

        # Ciclo interno donde se evaluan los objetos dentro del frame
        while l_obj is not None: 
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)         
            except StopIteration:
                break           

            obj_counter[obj_meta.class_id] += 1
            x = int(obj_meta.rect_params.width + obj_meta.rect_params.left/2) #x = obj_meta.rect_params.left
            y = int(obj_meta.rect_params.height + obj_meta.rect_params.top/2) #y = obj_meta.rect_params.top

            # Service Aforo (in and out)
            ids.append(obj_meta.object_id)
            boxes.append((x, y))

            if is_aforo_enabled:
                if aforo_info['area_of_interest']:
                    #aa = service.is_point_insde_polygon(x, y, polygon_sides, polygon)
                    #print('aaaaaaaaaaaaaaaaaaaaaaa', aforo_info['area_of_interest'])
                    #quit()
                    if x > TopLeftx and x < (TopLeftx + Width) and y < (TopLefty + Height) and y > TopLefty:
                        #polygon_sides, polygon = get_reference_line(camera_id)
                        entrada, salida = get_entrada_salida(camera_id)
                        initial, last = get_initial_last(camera_id)
                        entrada, salida = service.aforo((x, y), obj_meta.object_id, ids, camera_id, outside_area, reference_line, initial, last, entrada, salida)
                        #print('despues de evaluar: index, entrada, salida', current_pad_index, entrada, salida)
                        set_entrada_salida(camera_id, entrada, salida)
                        #print("x=",x,"y=",y,"ID=",obj_meta.object_id,"Entrada=",entrada,"Salida=",salida)
                else:
                    entrada, salida = get_entrada_salida(camera_id)
                    initial, last = get_initial_last(camera_id)
                    entrada, salida = service.aforo((x, y), obj_meta.object_id, ids, camera_id, outside_area, reference_line, initial, last, entrada, salida)
                    #print('despues de evaluar: index, entrada, salida', current_pad_index, entrada, salida)
                    set_entrada_salida(camera_id, entrada, salida)
                    #print("x=",x,"y=",y,"ID=",obj_meta.object_id,"Entrada=",entrada,"Salida=",salida)
            try: 
                l_obj = l_obj.next
            except StopIteration:
                break

        if is_aforo_enabled:
            entrada, salida = get_entrada_salida(camera_id)
            py_nvosd_text_params.display_text = "AFORO Source ID={} Source Number={} Person_count={} Entradas={} Salidas={}".format(frame_meta.source_id, frame_meta.pad_index , obj_counter[PGIE_CLASS_ID_PERSON], entrada, salida)

            '''
            Este bloque limpia los dictionarios initial y last, recolectando los ID que 
            no ya estan en la lista actual, es decir, "candidatos a ser borrados" y 
            despues es una segunda corroboracion borrandolos
            '''
            if frame_number % 50 == 0:
                disappeared = get_disappeared(camera_id)
                initial, last = get_initial_last(camera_id)
                if disappeared:
                    elements_to_delete = [ key for key in last.keys() if key not in ids and key in disappeared ]
                    for x in elements_to_delete:
                        last.pop(x)
                        initial.pop(x)
                    set_disappeared(camera_id)
                else:
                    elements_to_delete = [ key for key in last.keys() if key not in ids ]
                    set_disappeared(camera_id, elements_to_delete)

                disappeared = elements_to_delete

        if is_social_distance_enabled:
            boxes_length = len(boxes) # if only 1 object is present there is no need to calculate the distance
            if boxes_length > 1:
                service.set_frame_counter(frame_number)
                service.evaluate_social_distance(boxes, ids, boxes_length, camera_id, nfps, risk_value, tolerated_distance, get_socialt_distance_dict_of_ids(camera_id))
            py_nvosd_text_params.display_text = "SOCIAL DISTANCE Source ID={} Source Number={} Person_count={} ".format(frame_meta.source_id, frame_meta.pad_index , obj_counter[PGIE_CLASS_ID_PERSON])
        #====================== FIN de definicion de valores de mensajes a pantalla

        # Lo manda a directo streaming
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()       
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK	


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

    # Variable para verificar si al menos un video esta vivo
    is_live = False

    for i in range(0, number_sources):
        fps_streams["stream{0}".format(i)] = GETFPS(i)
        
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create gstreamer elements
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()

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
        print("Creating source_bin...........", i, " \n ")
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
    # h264parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    # if not h264parser:
    #    sys.stderr.write(" Unable to create h264 parser \n")

    print("Creating Decoder \n")
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    if not decoder:
        sys.stderr.write(" Unable to create Nvv4l2 Decoder \n")

    # Use nvinfer to run inferencing on decoder's output,
    # behaviour of inferencing is set through config file
    
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")

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
    sink.set_property('sync', 0)
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")
        
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

    pgie.set_property('config-file-path', CURRENT_DIR + "/configs/dstest2_pgie_config.txt")
    # pgie.set_property('config-file-path', CURRENT_DIR + "/configs/config_infer_primary_yoloV3.txt")
    # pgie.set_property('config-file-path', CURRENT_DIR + "/configs/config_infer_primary_yoloV3_tiny.txt")
    # pgie.set_property('config-file-path', CURRENT_DIR + "/configs/config_infer_primary_fasterRCNN.txt")
    # Falta añadir la ruta completa del archivo de configuracion
    
    pgie_batch_size = pgie.get_property("batch-size")

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
    config.read('configs/dstest2_tracker_config.txt')
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width':
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        elif key == 'tracker-height':
            tracker_height = config.getint('tracker', key)
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

    pipeline.add(decoder)
    pipeline.add(pgie)
    pipeline.add(tracker)
    #pipeline.add(sgie1)
    #pipeline.add(sgie2)
    #pipeline.add(sgie3)
    pipeline.add(tiler)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
    if is_aarch64():
        pipeline.add(transform)

    # we link the elements together
    # source_bin -> -> nvh264-decoder -> PGIE -> Tracker
    # tiler -> nvvidconv -> nvosd -> video-renderer
    print("Linking elements in the Pipeline \n")
    
    #source.link(h264parser)
    #h264parser.link(decoder)

    # lineas ya ejecutadas en el for anterior
    #sinkpad = streammux.get_request_pad("sink_0")
    #if not sinkpad:
    #    sys.stderr.write(" Unable to get the sink pad of streammux \n")
    #srcpad = decoder.get_static_pad("src")
    #if not srcpad:
    #    sys.stderr.write(" Unable to get source pad of decoder \n")

    srcpad.link(sinkpad)    
    source_bin.link(decoder)
    decoder.link(streammux)
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(tiler)

    #tracker.link(sgie1)
    #sgie1.link(sgie2)
    #sgie2.link(sgie3)
    #sgie3.link(tiler)

    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    
    if is_aarch64():
        nvosd.link(transform)
        transform.link(sink)
    else:
        nvosd.link(sink)

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
    
    # start play back and listed to events
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except Exception as e:
        print("This line? "+str(e))
        pass

    # cleanup
    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    sys.exit(main())
    #sys.exit(main(sys.argv))
