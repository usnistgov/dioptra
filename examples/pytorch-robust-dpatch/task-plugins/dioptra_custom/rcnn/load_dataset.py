# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
from __future__ import annotations

import importlib
from types import FunctionType, ModuleType
from typing import Union

import structlog
from structlog.stdlib import BoundLogger
from dioptra import pyplugs
import os
import xml.etree.ElementTree as ET
import cv2
import random
from detectron2.structures import BoxMode

LOGGER: BoundLogger = structlog.stdlib.get_logger()
    
@pyplugs.register
def load_dataset(
    data_dir: str,
    image_size: Tuple[int,int,int] = (400,300,3),
) -> Any:
    testing_dataset = get_sign_dicts(data_dir)
    imgs = []
    yss = []
    for d in random.sample(testing_dataset, 170):
        img = cv2.imread(d["file_name"])
        if (img.shape == image_size):
            imgs += [img]
            yss += [d]
    return imgs

def get_sign_dicts(
    base_path
):
    default_classes = ["stop", "crosswalk", "speedlimit", "trafficlight"]
    anno_path = str(base_path) + '/annotations'
    img_path = str(base_path) + '/images'   
    filelist = [f for f in os.listdir(anno_path) if os.path.isfile(os.path.join(anno_path, f))]
    dataset_dicts = []
    for file in filelist:
        xml_file = anno_path + "/" + file
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        record = {}
        filename = root.find('filename').text
        filename = os.path.join(img_path, filename)
        height, width = cv2.imread(filename).shape[:2]
        
        record["file_name"] = filename
        record["image_id"] = filename
        record["height"] = height
        record["width"] = width   
        objs = []
        
        for boxes in root.iter('object'):  
            name = boxes.find('name').text
            class_index = default_classes.index(name)

            ymin, xmin, ymax, xmax = None, None, None, None

            ymin = int(boxes.find("bndbox/ymin").text)
            xmin = int(boxes.find("bndbox/xmin").text)
            ymax = int(boxes.find("bndbox/ymax").text)
            xmax = int(boxes.find("bndbox/xmax").text)
            

            #poly = [(x+0.5, y+0.5) for x in range(xmin,xmax+1) for y in range(ymin,ymax+1)]
            poly = [(xmin,ymin),(xmin, ymax),(xmax, ymax),(xmax,ymin)]
            poly = [p for x in poly for p in x]
            
            obj = {
                "bbox": [xmin, ymin, xmax, ymax],
                "bbox_mode": BoxMode.XYXY_ABS,
                "segmentation": [poly],
                "category_id": class_index,
            }
            objs.append(obj)
            
        record["annotations"] = objs
        dataset_dicts.append(record)
    return dataset_dicts
