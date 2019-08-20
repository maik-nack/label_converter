import base64
import cv2
import json
import matplotlib.path
import numpy as np
import os
import xml.etree.ElementTree as ET


XML_FILTER = ".xml"
PNG_FILTER = ".png"


def get_path_to_img(path_to_xml):
    return os.path.abspath(path_to_xml)[:-len(XML_FILTER)] + PNG_FILTER


def add_base_information(root, path_to_xml, layout):
    folder_element = ET.Element('folder')
    folder_element.text = os.path.basename(os.path.split(path_to_xml)[0])
    filename_element = ET.Element('filename')
    filename_element.text = os.path.basename(path_to_xml)[:-len(XML_FILTER)] + PNG_FILTER
    path_element = ET.Element('path')
    path_element.text = get_path_to_img(path_to_xml)
    source_element = ET.Element('source')
    ET.SubElement(source_element, 'database').text = "Unknown"
    size_element = ET.Element('size')
    ET.SubElement(size_element, 'width').text = str(layout['imageWidth'])
    ET.SubElement(size_element, 'height').text = str(layout['imageHeight'])
    ET.SubElement(size_element, 'depth').text = "3"
    segmented_element = ET.Element('segmented')
    segmented_element.text = "0"
    root.append(folder_element)
    root.append(filename_element)
    root.append(path_element)
    root.append(source_element)
    root.append(size_element)
    root.append(segmented_element)


def add_object(root, name, bbox):
    object_element = ET.Element('object')
    ET.SubElement(object_element, 'name').text = name
    ET.SubElement(object_element, 'pose').text = "Unspecified"
    ET.SubElement(object_element, 'truncated').text = "0"
    ET.SubElement(object_element, 'difficult').text = "0"
    bbox_element = ET.SubElement(object_element, 'bndbox')
    ET.SubElement(bbox_element, 'xmin').text = str(bbox[0])
    ET.SubElement(bbox_element, 'ymin').text = str(bbox[1])
    ET.SubElement(bbox_element, 'xmax').text = str(bbox[2])
    ET.SubElement(bbox_element, 'ymax').text = str(bbox[3])
    root.append(object_element)


def easy_convert(layout):
    labels = []
    for _ in layout:
        points = np.round(_['points'])
        path = matplotlib.path.Path(points)
        bbox = path.get_extents()
        labels.append({'name': _['label'], 'bbox': np.asarray([bbox.xmin, bbox.ymin, bbox.xmax, bbox.ymax], int)})
    return labels


def convert(path_to_json, path_to_xml, easy_mode):
    with open(path_to_json, 'r') as f:
        layout = json.load(f)
    if easy_mode:
        labels = easy_convert(layout['shapes'])
    else:
        labels = []

    tree = ET.ElementTree(element=ET.Element('annotation'))
    root = tree.getroot()
    add_base_information(root, path_to_xml, layout)
    for _ in labels:
        add_object(root, _['name'], _['bbox'])
    tree.write(path_to_xml)

    img_bytes = base64.b64decode(layout['imageData'])
    img = cv2.imdecode(np.fromstring(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    cv2.imwrite(get_path_to_img(path_to_xml), img)
