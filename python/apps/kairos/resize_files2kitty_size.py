import os
from os import listdir, getcwd
from os.path import isfile, join
from PIL import Image, ImageDraw, ImageFont


kitti_size = 960, 544
base_dir = getcwd()
result_dir = base_dir + '/resize_files'

try:
    os.makedirs(result_dir, mode=0o777)
except FileExistsError:
    print("Directory Already Exists")

dir_path = 'MAFA_Dataset/test-images/images/'
onlyfiles = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]

for item in onlyfiles:
    elements = item.split('.')
    if len(elements) > 1 and elements[-1].lower() in ['jpg', 'png', 'jpeg']:
        file_name = elements[0]
        file_extension = elements[1]
        outfile = result_dir + '/' + file_name + '_' + str(kitti_size[0]) + '_' + str(kitti_size[1]) + '.' + file_extension
        
        file_to_resize = dir_path + item

        if file_to_resize != outfile:
            try:
                print(file_to_resize)
                im = Image.open(file_to_resize).convert("RGB")
                resize_img = im.resize(kitti_size)
                resize_img.save(outfile, "JPEG")
            except IOError:
                print("cannot create thumbnail for '%s'" % outfile)
