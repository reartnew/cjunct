"""The package contains everything related to configuration loading process"""

from .helpers import get_default_loader_class_for_file
from .xml import DefaultXMLConfigLoader
from .yaml import DefaultYAMLConfigLoader
