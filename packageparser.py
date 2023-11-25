from strategy import Submission, TestSet, Limits
from strategy.checker import Checker
import xml.etree.ElementTree as ET
import os
from parser import get_xml_tag_parser


def parse_package(xml_path, package_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    strategy_path = os.path.join(package_path, root.attrib["path"])

    arguments = []
    for child in tree.getroot():
        arguments.append(get_xml_tag_parser(child.tag)(child, package_path))

    return strategy_path, arguments
