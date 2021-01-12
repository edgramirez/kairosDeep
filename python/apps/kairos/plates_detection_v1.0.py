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


import boto3
from PIL import Image, ImageDraw, ExifTags, ImageColor



frame_count={}
saved_count={}

#
#  version mask_detection solo detectara personas mask & nomask
#  
#

PGIE_CLASS_ID_FACE = 0
PGIE_CLASS_ID_PLATES = 1

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

pgie_classes_str = ["Carita", "Placa", "Modelo", "Marca"]

# directorio actual
CURRENT_DIR = os.getcwd()

# Matriz de frames per second, Se utiliza en tiler
fps_streams = {}

global aforo_list
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
global no_mask_ids_dict

initial_last_disappeared = {}
source_list = []
#aforo_list = {}
#people_distance_list = {}
#people_counting_counters = {}
camera_list = []
#social_distance_list = {}
#entradas_salidas = {}
#social_distance_ids = {}
#no_mask_ids_dict = {}


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




def log_error(msg):
    print("-- PARAMETER ERROR --\n"*5)
    print(" %s \n" % msg)
    print("-- PARAMETER ERROR --\n"*5)
    quit()


def reading_server_config():
    from configs.Server_Emulatation_configs import config as scfg

    if not service.set_header(scfg['server']['token_file']):
        log_error("Unable to set the 'Token' using parameter: {}".format(scfg['server']['token_file']))

    # setup the services for each camera
    set_server_url(scfg['server']['url'])
    global srv_url

    # setup the services for each camera
    set_number_of_resources(len(scfg['cameras']))

    for camera in scfg['cameras'].keys():
        activate_service = False# before False
        source = None
        for key in scfg['cameras'][camera].keys():

            if key == 'source':
                source = scfg['cameras'][camera][key]
                continue
            elif key == 'mask_detection' and scfg['cameras'][camera][key]['enabled']:
                #set_no_mask_ids_dict(camera)
                #service.set_mask_detection_url(srv_url)
                activate_service = True
            else:
                continue

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

    #aforo_info = get_aforo(camera_id) 
    #is_aforo_enabled = aforo_info['enabled']

    #social_distance_info = get_social_distance(camera_id)
    #is_social_distance_enabled = social_distance_info['enabled']

    #people_counting_info = get_people_counting(camera_id)
    #is_people_counting_enabled = people_counting_info['enabled']

    # Falta el servicio de Plates Detection
    #
    #

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

    #no_mask_ids = get_no_mask_ids_dict(camera_id)
    # por que ponerlo en 1 ????
    #frame_number = 1 # to avoid not definition issue

    client=boto3.client('rekognition')

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break
        #print( "primer ciclo") 
        frame_number = frame_meta.frame_num
        #print(" fps:",frame_meta.num_surface_per_frame)
        l_obj = frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        is_first_obj = True
        save_image = False

        #print(num_rects) ID numero de stream
        ids = set()

        # Ciclo interno donde se evaluan los objetos dentro del frame
        while l_obj is not None: 
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)         
            except StopIteration:
                break           
            

            obj_counter[obj_meta.class_id] += 1
            #print(obj_meta.confidence,"   ",obj_meta.object_id)
            #print(obj_counter[obj_meta.class_id],"   ",obj_counter[obj_meta.class_id]%5)
            # and (obj_meta.confidence > 0.9 )
            print(frame_number) 
            if (( obj_meta.class_id == 1 ) and ( frame_number%8 == 0 )):
                if is_first_obj:
                    is_first_obj = False
                    # Getting Image data using nvbufsurface
                    # the input should be address of buffer and batch_id
                    n_frame=pyds.get_nvds_buf_surface(hash(gst_buffer),frame_meta.batch_id)
                    #convert python array into numy array format.
                    frame_image=np.array(n_frame,copy=True,order='C')
                    #covert the array into cv2 default color format
                    frame_image=cv2.cvtColor(frame_image,cv2.COLOR_RGBA2BGRA)

                save_image = True
                frame_image=draw_bounding_boxes(frame_image,obj_meta,obj_meta.confidence)

                 
                response = client.detect_labels(Image={'Bytes': frame_image})
                print('Detected labels in ')    
                for label in response['Labels']:
                   print (label['Name'] + ' : ' + str(label['Confidence']))

            #py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Mask={} NoMaks={}".format(frame_number, num_rects, obj_counter[PGIE_CLASS_ID_FACE], obj_counter[PGIE_CLASS_ID_PLATES])

            try: 
                l_obj = l_obj.next
            except StopIteration:
                break
        

        #pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()  
        #print(save_image)
        #print(folder_name)
        if save_image:
            print("Entre a guardar imagen")
            print(obj_meta.class_id)
             
            cv2.imwrite(folder_name+"/stream_"+str(frame_meta.pad_index)+"/frame_"+str(frame_number)+".jpg",frame_image)
        saved_count["stream_"+str(frame_meta.pad_index)]+=1
      
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    '''
    if frame_number % 43 == 0:
        new_dict = {}
        no_mask_ids = get_no_mask_ids_dict(camera_id)

        for item in ids:
            if item in no_mask_ids:
                value = no_mask_ids[item]
                new_dict.update({item: value})

        set_no_mask_ids_dict(camera_id, new_dict)

        # Lo manda a directo streaming
    '''

    return Gst.PadProbeReturn.OK	


def draw_bounding_boxes(image,obj_meta,confidence):
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


    obj_name=pgie_classes_str[obj_meta.class_id]
    #image=cv2.rectangle(image,(left,top),(left+width,top+height),(0,0,255,0),2)
    #image=cv2.line(image, (left,top),(left+width,top+height), (0,255,0), 9)
    # Note that on some systems cv2.putText erroneously draws horizontal lines across the image
    #image=cv2.putText(image,obj_name+',C='+str(confidence),(left+10,top+10),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255,0),2)
    #crop_image = image[top-10:top+height+20,left-10:left+width+20]
    crop_image = image[top:top+height,left:left+width]
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
    
    global folder_name
    #folder_name=args[-1]
    folder_name = "frames"
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
