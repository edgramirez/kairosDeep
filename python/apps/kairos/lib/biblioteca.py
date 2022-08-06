import os
import cv2
import time
import requests
import codecs, json
import face_recognition
import numpy as np
from os import walk
from datetime import datetime, timedelta

import lib.common as com
import lib.validate as validate
import lib.json_methods as jsm

font = cv2.FONT_HERSHEY_SIMPLEX


def compare_against_encoding_list(face_encoding, known_face_encodings_list, tolerated_difference=.59):
    # If our known face list is empty, just return nothing since we can't possibly have seen this face.
    if known_face_encodings_list:
        # Only check if there is a match
        matches = face_recognition.compare_faces(known_face_encodings_list, face_encoding, tolerated_difference)

        if True in matches:
            # si hay un True en la lista entonces hay un match, get the indexes of these matches
            indexes = [ index for index, item in enumerate(matches) if item]

            # crear una lista dinamica con los indices que hicieron match
            only_true_known_face_encodings = [known_face_encodings_list[ind] for ind in indexes]

            # obtener la distancia de los elementos en la nueva lista contra el encoding de la nueva imagen
            face_distances = face_recognition.face_distance(only_true_known_face_encodings, face_encoding)
            # Get the match with the shortest distance to the image.
            best_match_index = np.argmin(face_distances)

            # La distancia de este elemento con la menor distancia tiene que ser menor a nuestro parametro de aceptacion
            if face_distances[best_match_index] < tolerated_difference:
                # print("distancias:\n",face_distances,"best match:",best_match_index,"tolerance:",tolerated_difference)
                # Values returned:  
                # meta que hace match el indice real de la lista global, distancia a la imagen analizada
                return indexes[best_match_index], face_distances[best_match_index]
    return None, None


def lookup_known_face(face_encoding, known_face_encodings_list, known_face_metadata, tolerated_difference=0.59):
    '''
    - See if this face was already stored in our list of faces
    - tolerated_difference: is the parameter that indicates how much 2 faces are similar, 0 is the best match and 1
    means are completely different
    '''
    best_match, distance = compare_against_encoding_list(face_encoding, known_face_encodings_list)

    if best_match:
        return   known_face_metadata[best_match], best_match, distance

    return None, None, None


def encode_known_faces_from_images_in_dir(image_path, output_file, image_group=None, append=False):
    '''
    Esta funccion codifica los rostros encotrados en las imagenes presentes en el diretorio especificado
    '''
    if com.dir_exists(image_path) is False:
        com.log_error("Directory '{}' does not exist".format(image_path))

    files, root = com.read_images_in_dir(image_path)

    known_face_encodings = []
    known_face_metadata = []
    if append and com.file_exists(output_file):
        known_face_encodings, known_face_metadata = com.read_pickle(output_file)

    write_to_file = False
    model = None
    for file_name in files:
        # load the image into face_recognition library
        source_info = {}
        face_obj = face_recognition.load_image_file(root + '/' + file_name)
        name = os.path.splitext(file_name)[0]
        known_face_encodings, known_face_metadata, encoding_result = encode_and_update_face_image(
            face_obj, name, known_face_encodings, known_face_metadata, 0, model, image_group)

        if encoding_result is False:
            print('Archivo: {}/{}, no contiene rostros que puedan ser procesados, Retrying with cnn'.
                  format(image_path, name))
            model = "cnn"
            known_face_encodings, known_face_metadata, encoding_result = encode_and_update_face_image(
                face_obj, name, known_face_encodings, known_face_metadata, 1, model, image_group)

            if encoding_result is False:
                print('Archivo: {}/{}, no contiene rostros que puedan ser procesados, '
                      'Retrying with 3 cycles'.format(image_path, name))
                known_face_encodings, known_face_metadata, encoding_result = encode_and_update_face_image(
                    face_obj, name, known_face_encodings, known_face_metadata, 2, model, image_group)

        if encoding_result:
            #write_to_file = True
            #if write_to_file:
            #print(known_face_metadata)
            #print("\n\nedgar\n\n")
            #append_to_pickle(known_face_encodings, known_face_metadata, output_file)
            #quit()
            com.write_to_pickle(known_face_encodings, known_face_metadata, output_file)


def encode_and_update_face_image(face_obj, name, face_encodings, face_metadata, default_sample=0, model=None,
                                 image_group=None):
    new_encoding, new_metadata = encode_face_image(face_obj, name, None, None, True, default_sample, model, image_group)

    if new_encoding is not None:
        face_encodings.append(new_encoding)
        face_metadata.append(new_metadata)
        # if we are able to encode and get the metadata we return a third value indicating success with "True" value
        return face_encodings, face_metadata, True

    # if we are failed to encode and get the metadata we return a third value indicating failure with "False" value
    return face_encodings, face_metadata, False 


def encoding_image_from_source(camera_id, image, confidence, name=None):
    # codificando la imagen obtenida desde el streaming
    img_encoding, img_metadata = encode_face_image(image, name, camera_id, confidence, None, 0, model="cnn")

    # si el modelo de "face recognition" puede generar una codificacion de la imagen su valor es diferente de None
    if img_encoding is None:
        return [], []

    return img_encoding, img_metadata


def encode_face_image(face_obj, face_name, camera_id, confidence, print_name, default_sample=0,
                      model=None, image_group=None):
    # covert the array into cv2 default color format
    # THIS ALREADY DONE IN CROP
    # rgb_frame = cv2.cvtColor(face_obj, cv2.COLOR_RGB2BGR)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = face_obj[:, :, ::-1]

    # try to get the location of the face if there is one
    # face_location = face_recognition.face_locations(rgb_small_frame, number_of_times_to_upsample=2, model='cnn')
    if model is not None:
        print("face_location with: {}/{}".format(default_sample, model))
        # face_location = face_recognition.face_locations(rgb_small_frame, default_sample, model='cnn')
        # face_location = face_recognition.face_locations(rgb_small_frame, model='cnn')
        face_location = face_recognition.face_locations(rgb_small_frame)
    else:
        print("face_location with: {}".format(model))
        face_location = face_recognition.face_locations(rgb_small_frame)

    # if got a face, loads the image, else ignores it
    if face_location:
        # Grab the image of the face from the current frame of video
        top, right, bottom, left = face_location[0]
        face_image = rgb_small_frame[top:bottom, left:right]
        face_image = cv2.resize(face_image, (150, 150))
        encoding = face_recognition.face_encodings(face_image)

        # if encoding empty we assume the image was already treated 
        if len(encoding) == 0:
            encoding = face_recognition.face_encodings(rgb_small_frame)

        if encoding:
            face_metadata_dict = new_face_metadata(face_obj, face_name, camera_id, confidence, print_name, image_group)
            return encoding[0], face_metadata_dict

    return None, None


def new_face_metadata(face_image, name=None, camera_id=None, confidence=None, print_name=False, image_group=None):
    """
    Add a new person to our list of known faces
    """
    # if image_group and not image_group in com.IMAGE_GROUPS:
    # com.log_error("Image type most be one of the followings or None: {}".format(com.IMAGE_GROUPS))

    today_now = com.get_timestamp()

    if name is None:
        name = camera_id + '_' + str(today_now)
    else:
        if print_name:
            print('Saving face: {} in group: {}'.format(name, image_group))

    return {
        'name': name,
        'face_id': 0,
        'camera_id': camera_id,
        'first_seen': today_now,
        'first_seen_this_interaction': today_now,
        'image': False,
        'image_group': image_group,
        'confidence': confidence,
        'last_seen': today_now,
        'seen_count': 1,
        'seen_frames': 1
    }
