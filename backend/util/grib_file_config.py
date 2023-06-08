"""
The data processing script contains the parameters used to determine what
data files need to be downloaded.  This method provides a wrapper around that
functionality to allow for easy identification of things like:

a) what are all the files that need to be downloaded
b) what is the pattern to use for the amqp subtopic
c) is a given file part of a pattern defined in the grib config for dl

"""

import datetime
import inspect
import logging
import os
import sys
import urllib.parse

# hack... need to fix this.
path2Add = os.path.join(os.path.dirname(__file__), '..', '..', 'scripts/src')
sys.path.append(path2Add)
import GetGribConfig

LOGGER = logging.getLogger(__name__)


class GribFiles:

    def __init__(self):
        #self.calculate_file_list()
        cur = datetime.datetime.now()

        self.gribcollection = GetGribConfig.GribConfigCollection()

    def calculate_expected_file_list(self, only_file_path=False, date_str=None):
        """
        using the config calculates the path to the files that are required by
        the RFC to be downloaded when available.  The file path is also going
        to be the message that is emitted by the message queue indicating that
        the file is now ready for download

        :param only_file_path: if set to true will only include the directory
                    path to the file, and not the protocol.

                    example when true would create list that looks like:
                      /20230419/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/090/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023041900_P090.grib2
                      /20230419/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/093/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023041900_P093.grib2
                      /20230419/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/096/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023041900_P096.grib2', '/20230419/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/099/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023041900_P099.grib2
                      etc...

                    when set to false will return the full url to the file:
                      https://hpfx.collab.science.gc.ca/20230419/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/090/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023041900_P090.grib2
                      https://hpfx.collab.science.gc.ca/20230419/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/093/CMC_glb_PRATE_SFC_0_latlon.15x.15_2023041900_P093.grib2
                      etc....
        """
        file_list = []
        class_dict = self.gribcollection.get_class_dict()
        config_class_names_list = class_dict.keys()
        for config_class in config_class_names_list:
            LOGGER.debug(f"config_class name: {config_class}")
            config_instance = self.gribcollection.cls_dict[config_class]

            iterator = config_instance.get_iterator()
            for iter in iterator:
                url = self.get_url(config_instance, iterator=iter, date_str=date_str)
                LOGGER.debug(f"url: {url}")
                src_file = self.get_src_file(
                    config_instance=config_instance,
                    iterator=iter,
                    date_str=date_str)
                full_url = os.path.join(url, src_file)
                if only_file_path:
                    parse_obj = urllib.parse.urlparse(full_url)
                    file_list.append(parse_obj.path)
                else:
                    file_list.append(full_url)

            # now from the instance call methods to get file list
            LOGGER.debug(f"instance: {config_instance.model_number}")
        LOGGER.info(f"expecting {len(file_list)} grib files to initiate processing")
        return file_list

    def get_src_file(self, config_instance, iterator=None, date_str=None):
        LOGGER.debug(f"iterator: {iterator}")
        fstring_properties = self.get_property_in_fstring(config_instance, config_instance.file_template)
        if iterator and 'iterator' in config_instance.file_template:
            fstring_properties['iterator'] = iterator
        if date_str is not None and 'datestr' in fstring_properties:
            fstring_properties['datestr'] = date_str
        LOGGER.debug(f"properties: {fstring_properties}")
        LOGGER.debug(f"fstring: {config_instance.file_template}")
        file_name = config_instance.file_template.format(**fstring_properties)
        LOGGER.debug(f"file_name: {file_name}")
        return file_name

    def get_property_in_fstring(self, config_instance, fstring):
        """gets an fstring and returns a list of the properties that are
        defined in the fstring.

        :param fstring: input fstring
        :return: list of properties defined in the fstring
        """
        fstring_property_dict = {}
        properties = self.get_property_list(config_instance)
        for prop in properties:
            if prop in fstring:
                fstring_property_dict[prop] = getattr(config_instance, prop)
        return fstring_property_dict

    def get_url(self, config_instance, iterator=None, date_str=None):
        """templates can use any property that is populated in the class
        This method looks at what properties are required, and uses them
        to create the url string using the url format string.
        """
        LOGGER.debug(f"iterator: {iterator}")

        fstring_properties = self.get_property_in_fstring(config_instance, config_instance.url_template)
        if date_str is not None and 'datestr' in fstring_properties:
            fstring_properties['datestr'] = date_str

        LOGGER.debug(f"fstring_properties: {fstring_properties}")
        if iterator and 'iterator' in config_instance.file_template:
            fstring_properties['iterator'] = iterator
        url = config_instance.url_template.format(**fstring_properties)
        LOGGER.debug(f'url: {url}')
        return url

    def get_property_list(self, config_instance):
        property_list = []
        props = inspect.getmembers(config_instance)
        for prop in props:
            if prop[0][0] != '_':
                property_list.append(prop[0])
        return property_list

    def get_all_topic_strings(self):
        """reads the various grib config files and retrieves the topic strings
        and returns them as a list.  The topic strings are the specific format
        used to identify what the listener should be listening to when creating
        a subscription to the message queue.

        Follows the format described here:
        https://samuelguay.ca/open-data/msc-datamart/amqp_en/#contact-us

        """
        topic_strings = []
        class_dict = self.gribcollection.get_class_dict()

        for config_class in class_dict.keys():
            instance = class_dict[config_class]
            topic_strings.append(instance.amqp_topic_pattern)
        # topic strings should be unique so remove duplicates
        topic_strings = list(set(topic_strings))
        return topic_strings
