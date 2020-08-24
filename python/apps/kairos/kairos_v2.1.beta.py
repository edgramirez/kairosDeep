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

PEOPLE_COUNTING_SERVICE = 0
AFORO_ENT_SAL_SERVICE = 1
SOCIAL_DISTANCE_SERVICE = 2

#
# Variables adicionales para el manejo de la funcionalidad de Tiler
# independientemente como venga los parametros del video se ajusta 
# a los parametros del muxer
#

MAX_DISPLAY_LEN = 64
MUXER_OUTPUT_WIDTH = 1920             # 1280 
MUXER_OUTPUT_HEIGHT = 1080            # 1080
MUXER_BATCH_TIMEOUT_USEC = 4000000
TILED_OUTPUT_WIDTH = 1920             # 720p
TILED_OUTPUT_HEIGHT = 1080            # 720p
GST_CAPS_FEATURES_NVMM = "memory:NVMM"

#pgie_classes_str = ["Vehicle", "TwoWheeler", "Person", "RoadSign"]
servicios_habilitados = {}


# directorio actual
CURRENT_DIR = os.getcwd()

# Matriz de frames per second
# Se utiliza en tiler
fps_streams = {}

global counter
global current_time
global offset_time
#global entrada
#global salida                       # Faltaba definirla

# inicializacion de contadores para Aforo
# que se imprimara en la pantalla

#entrada = 0
#salida = 0



def addSecs(tm, secs):
    fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
    fulldate = fulldate + datetime.timedelta(seconds=secs)
    return fulldate.time()


def set_counter():
    global counter
    counter = 0


def get_counter():
    global counter
    return counter


def increment():
    global counter
    counter += 1


def set_current_time():
    global current_time
    current_time = datetime.datetime.now().time()


def get_current_time():
    global current_time
    return current_time


def set_offset_time():
    global offset_time
    offset_time = addSecs(get_current_time(), 60)


def get_offset_time():
    global offset_time
    return offset_time


set_counter()
set_current_time()
set_offset_time()

#
# Funcion principal donde se evaluan los frames y los objectos detectados
#
#

def tiler_src_pad_buffer_probe(pad, info, u_data):

    # Intiallizing object counter with 0.
    # version 2.1 solo personas
    #global entrada, salida                  # definicion de variables de conteo para Aforo
    entrada = 0
    salida = 0

    servicios_habilitados = service.emulate_reading_from_server()    
    #print("Valores Servicios :", servicios_habilitados[AFORO_ENT_SAL_SERVICE],servicios_habilitados[PEOPLE_COUNTING_SERVICE],servicios_habilitados[SOCIAL_DISTANCE_SERVICE])


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
    
    if servicios_habilitados[AFORO_ENT_SAL_SERVICE] and ( pyds.NvDsFrameMeta.cast(l_frame.data).pad_index % 2 == 0  ):
        previous = service.get_previous()

    '''
    #====================== Definicion de valores de mensajes a pantalla
    display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
    
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
    
    if servicios_habilitados[AFORO_ENT_SAL_SERVICE]:
        display_meta.num_lines = 1      # numero de lineas
        display_meta.num_rects = 1      # numero de rectangulos  
        py_nvosd_line_params = display_meta.line_params[0]                
        py_nvosd_rect_params = display_meta.rect_params[0]        

        # Setup de la linea de Ent/Sal
        # los valos de las coordenadas tienen que ser obtenidos del archivo de configuracion
        # en este momento estan hardcode
 
        py_nvosd_line_params.x1 = 510
        py_nvosd_line_params.y1 = 740
        py_nvosd_line_params.x2 = 1050
        py_nvosd_line_params.y2 = 740
        py_nvosd_line_params.line_width = 5
        py_nvosd_line_params.line_color.red = 1.0
        py_nvosd_line_params.line_color.green = 1.0
        py_nvosd_line_params.line_color.blue = 1.0
        py_nvosd_line_params.line_color.alpha = 1.0

        # setup del rectangulo de Ent/Sal
        # de igual manera que los parametros de linea, 
        # los valores del rectangulo se calculan en base a
        # los valoes del archivo de configuracion

        py_nvosd_rect_params.left = 500
        py_nvosd_rect_params.height = 120
        py_nvosd_rect_params.top = 680
        py_nvosd_rect_params.width = 560
        py_nvosd_rect_params.border_width = 4
        py_nvosd_rect_params.border_color.red = 0.0
        py_nvosd_rect_params.border_color.green = 0.0
        py_nvosd_rect_params.border_color.blue = 1.0
        py_nvosd_rect_params.border_color.alpha = 1.0
        
    #======================  '''

    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        # que hace esta funcion ????
        #if get_counter() == 60:
        #    set_counter()

        #    if get_current_time() > get_offset_time():
        #        print('aca...............')
        #        service.emulate_reading_from_server()
        #        set_offset_time()
        #    else:
        #        set_current_time()
        #else:
        #    increment()

        frame_number = frame_meta.frame_num
        l_obj = frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta

        # La camara Meraki tiene que estar configurada en 720p, todas se pueden a excepcion de la MV32 que el minimo es 1080p
        #
        #print(frame_meta.source_frame_height, frame_meta.source_frame_width)   # Alto 720 Ancho 1280
        
        #
        #print("stream_"+str(frame_meta.pad_index))     El numero de fuente viene en el pad_index
        # este valor debe usarse para identificar que servicio se debe ejecutar en el ciclo interno
        # 
    
        # Estos arreglos se usan y definen solo para AFORO
        ids = []
        boxes = []

        #
        # Ciclo interno donde se evaluan los objetos dentro del frame
        #
        while l_obj is not None: 
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)         
            except StopIteration:
                break           

            # validacion de solo personas, solo para control de debug
            # print(" Class ID ", pgie_classes_str[obj_meta.class_id])
            #print(obj_meta.detector_bbox_info)

            obj_counter[obj_meta.class_id] += 1
            #x = int(obj_meta.rect_params.left)
            #y = int(obj_meta.rect_params.top)
            x = int(obj_meta.rect_params.width) +  int(obj_meta.rect_params.left/2)          
            #y = int(obj_meta.rect_params.height) + int(obj_meta.rect_params.top)    # Ahora considera la base del box para contabilizar
            y = int(obj_meta.rect_params.height) + int(obj_meta.rect_params.top/2)  # Aqui considera la parte media del Box 

            
            
            # Service Aforo (in and out)
            
            #ids.append(obj_meta.object_id)
            #boxes.append((x, y))

            #print(servicios_habilitados[AFORO_ENT_SAL_SERVICE])
            # 19-Agosto-2020
            # En este momento los streaming 0,2,4,6 ( pares ) son para Aforo y los nones son para Social Distance
            # Es importante introducir los sources considerando lo anterior
            #
            if servicios_habilitados[AFORO_ENT_SAL_SERVICE] and ( frame_meta.pad_index % 2 == 0  ): 
                
                ids.append(obj_meta.object_id)
                boxes.append((x, y))

                #print("Servicio de Aforo habilitado")
                entrada, salida = service.aforo((x, y), obj_meta.object_id, ids, previous)
                print("x=",x," y=",y," ID = ",obj_meta.object_id," Entrada=",entrada," Salida= ",salida," Frame =",frame_meta.pad_index,"Bandera=",previous)
                #if direction == 1: 
                #    contador_entrada += 1
                #    print("Entrada", contador_entrada)
                #elif direction == 0:
                #    print("Salida", contador_salida)
                #    contador_salida += 1
            #else:
                # Service People counting
                # print ("People Counting ") 
                #if previous:
                #    service.people_counting_last_time_detected(ids)
                #    service.people_counting_storing_fist_time(obj_meta.object_id)

            try: 
                l_obj = l_obj.next
            except StopIteration:
                break

        # Nota 18-Agst-2020
        # El codigo de Social Distance se esta en este momento ejecutando fuera del ciclo de identificacion
        # de objetos dentro del frame, creo que no debe ser asi

        # Service Social Distance
        # Solo aplican las fuentes impares 
        
        if servicios_habilitados[SOCIAL_DISTANCE_SERVICE] and ( frame_meta.pad_index % 2 != 0  ):
            boxes_length = len(boxes)
            if boxes_length > 1:
                service.set_frame_counter(frame_number)
                service.tracked_on_time_social_distance(boxes, ids, boxes_length)

        if not previous and servicios_habilitados[AFORO_ENT_SAL_SERVICE] and ( frame_meta.pad_index % 2 == 0  ):
            previous = service.set_previous()

        # Impresion en el video de los valores que nos interesan
        # Dibujo de la linea de Ent/Sal 
        # 
    
        #====================== Definicion de valores de mensajes a pantalla
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
    
        # Todos los servicios requieren impresion de texto solo para Aforo se requiere una linea y un rectangulo
        display_meta.num_labels = 1                            # numero de textos
        py_nvosd_text_params = display_meta.text_params[0]
        
        # Setup del label de impresion en pantalla
        py_nvosd_text_params.x_offset = 100
        py_nvosd_text_params.y_offset = 120
        py_nvosd_text_params.font_params.font_name = "Arial"
        py_nvosd_text_params.font_params.font_size = 20
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)
        #py_nvosd_text_params.font_params.font_color.red = 1.0
        #py_nvosd_text_params.font_params.font_color.green = 1.0
        #py_nvosd_text_params.font_params.font_color.blue = 1.0
        #py_nvosd_text_params.font_params.font_color.alpha = 1.0
        py_nvosd_text_params.set_bg_clr = 1
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        #py_nvosd_text_params.text_bg_clr.red = 0.0
        #py_nvosd_text_params.text_bg_clr.green = 0.0
        #py_nvosd_text_params.text_bg_clr.blue = 0.0
        #py_nvosd_text_params.text_bg_clr.alpha = 1.0
        
        if servicios_habilitados[AFORO_ENT_SAL_SERVICE] and ( frame_meta.pad_index % 2 == 0 ):
            display_meta.num_lines = 1      # numero de lineas
            display_meta.num_rects = 1      # numero de rectangulos  
            py_nvosd_line_params = display_meta.line_params[0]                
            py_nvosd_rect_params = display_meta.rect_params[0]        

            # Setup de la linea de Ent/Sal
            # los valos de las coordenadas tienen que ser obtenidos del archivo de configuracion
            # en este momento estan hardcode
 
            py_nvosd_line_params.x1 = 500      # 510
            py_nvosd_line_params.y1 = 730      # 740
            py_nvosd_line_params.x2 = 1150     # 1050
            py_nvosd_line_params.y2 = 730      # 740
            py_nvosd_line_params.line_width = 5
        
            py_nvosd_line_params.line_color.red = 1.0
            py_nvosd_line_params.line_color.green = 1.0
            py_nvosd_line_params.line_color.blue = 1.0
            py_nvosd_line_params.line_color.alpha = 1.0

            # setup del rectangulo de Ent/Sal
            # de igual manera que los parametros de linea, 
            # los valores del rectangulo se calculan en base a
            # los valoes del archivo de configuracion

            py_nvosd_rect_params.left = 500
            py_nvosd_rect_params.height = 120
            py_nvosd_rect_params.top = 680
            py_nvosd_rect_params.width = 560
            py_nvosd_rect_params.border_width = 4
            
            py_nvosd_rect_params.border_color.red = 0.0
            py_nvosd_rect_params.border_color.green = 0.0
            py_nvosd_rect_params.border_color.blue = 1.0
            py_nvosd_rect_params.border_color.alpha = 1.0
        
    #===================== '''


        #py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicle_count={} Person_count={}".format(frame_number, num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE],obj_counter[PGIE_CLASS_ID_PERSON])
        if servicios_habilitados[AFORO_ENT_SAL_SERVICE] and ( frame_meta.pad_index % 2 == 0  ):
            py_nvosd_text_params.display_text = "AFORO Source ID={} Person_count={} Entradas={} Salidas={}".format(frame_meta.pad_index , obj_counter[PGIE_CLASS_ID_PERSON], entrada, salida)
        elif servicios_habilitados[SOCIAL_DISTANCE_SERVICE] and ( frame_meta.pad_index % 2 != 0  ):
            #print("SOCIAL DISTANCE DSIPLAY")
            py_nvosd_text_params.display_text = "SOCIAL DISTANCE Source ID={} Person_count={} ".format( frame_meta.pad_index , obj_counter[PGIE_CLASS_ID_PERSON])
        
            
        # Lo manda a directo streaming
        #if servicios_habilitados[AFORO_ENT_SAL_SERVICE] and ( frame_meta.pad_index % 2 == 0  ): 
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        #else:
        #    pyds.nvds_remove_display_meta_from_frame(frame_meta, display_meta)


        # Lo manda a terminal, siguientes 2 lineas, hacen lo mismo, diferentes funciones 
        #print(pyds.get_string(py_nvosd_text_params.display_text))        
        #print("Frame Number=", frame_number, "Number of Objects=",num_rects,"Vehicle_count=",vehicle_count,"Person_count=",person)

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

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
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


def main(args):
    # Check input arguments
    # Permite introducir un numero x de fuentes, en nuestro caso streamings delas camaras Meraki        
    number_sources = len(args)-1    

    if number_sources+1 < 2:
        sys.stderr.write("usage: %s <uri1> [uri2] ... [uriN]\n" % args[0])
        sys.exit(1)

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
    for i in range(number_sources):

        print("Creating source_bin...........", i, " \n ")
        uri_name = args[i+1]

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
    
    
    # Prueba de Dewarp
    nvdewarp = Gst.ElementFactory.make("nvdewarper","nvdewarp0")
    if not nvdewarp:
        sys.stderr.write(" Unableto create dewarp \n")

    #nvdewarp.set_property('config-file',CURRENT_DIR + "/configs/dewarp_config.txt")
    nvdewarp.set_property("config-file",CURRENT_DIR + "/configs/config_dewarper.txt")
    nvdewarp.set_property('source_id', 0)
    
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
        
    # Tamano del streammux, si el video viene a 720p, se ajusta automaticamente
    # Ahorita los videos meraki viene configurados a 720p

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

    pipeline.add(decoder)   #Se elimina en version 2.1
    pipeline.add(nvdewarp)
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

    srcpad.link(sinkpad)    
    source_bin.link(decoder)
    decoder.link(nvdewarp)
    nvdewarp.link(streammux)
    #decoder.link(streammux)
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

    #servicios_habilitados = {
    #    PEOPLE_COUNTING_SERVICE: False,
    #    AFORO_ENT_SAL_SERVICE: False,
    #    SOCIAL_DISTANCE_SERVICE: False   
    #        }


    #print("Valor Aforo Antes de leer del Servidor:", servicios_habilitados[AFORO_ENT_SAL_SERVICE],servicios_habilitados[PEOPLE_COUNTING_SERVICE],servicios_habilitados[SOCIAL_DISTANCE_SERVICE])
    #servicios_habilitados = service.emulate_reading_from_server()
    #print("Valor Aforo :", servicios_habilitados[AFORO_ENT_SAL_SERVICE],servicios_habilitados[PEOPLE_COUNTING_SERVICE],servicios_habilitados[SOCIAL_DISTANCE_SERVICE])

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
    sys.exit(main(sys.argv))
