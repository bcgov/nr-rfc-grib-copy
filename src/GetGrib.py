import datetime
import inspect
import logging
import os
import subprocess
import sys

import requests

import config
import GetGribConfig
import ObjectStore

LOGGER = logging.getLogger(__name__)

class GetGrib:
    def __init__(self, dest_folder:str, config: GetGribConfig.GribConfig):
        self.config = config
        self.set_dest_folder(dest_folder)

    def set_dest_folder(self, dest_folder):
        """
        defines the destination folder for where data will be downloaded
        to

        :param dest_folder: a string that defines the destination folder for any
            grib data that will be downloaded using this module
        :type dest_folder: str
        """
        self.dest_folder = os.path.join(dest_folder, self.config.datestr)
        if not os.path.exists(self.dest_folder):
            os.makedirs(self.dest_folder)
        self.dest_folder = os.path.realpath(self.dest_folder)

    def get(self):
        for iterval in self.config.iteratorlist:
            LOGGER.debug(f"iterval: {iterval}")
            url = self.get_url(iterator=iterval)
            LOGGER.debug(f"url: {url}")
            src_file = self.get_src_file(iterator=iterval)
            full_url = os.path.join(url, src_file)
            dest_file = os.path.join(self.dest_folder, src_file)
            LOGGER.info(f"url to aquire file from: {full_url}")
            if not os.path.exists(dest_file):
                r = requests.get(full_url, allow_redirects=True)
                LOGGER.debug(f"request: {r.status_code}")
                r.raise_for_status()
                with open(dest_file, 'wb') as fh:
                    fh.write(r.content)

    def extract(self):
        # extract code = P or T
        # extract name = P1, T1, T2... etc
        # wgrib_params = the parameters to be used when wgrib2 is executed
        start_dir = os.getcwd()
        os.chdir(self.dest_folder)
        LOGGER.debug(f"dest folder: {self.dest_folder}")
        extract_output_dict = {}
        LOGGER.info("extracting data from the grib2 files...")
        # iterating through the various input values that went into the
        # defining the file that needed to be downloaded
        for iterval in self.config.iteratorlist:
            # get the name of the grib2 file to read
            src_file = self.get_src_file(iterator=iterval)
            # get the parameter list for each wgrib2 run on this file type
            extract_params = self.config.extract_params_object.get_wgrib_params(self.config.extract_code)
            # iterate over the extract params using a counter... the counter
            # will be used to define the output p1, p2.. or t1, t2.. files
            for extract_cnt in range(0, len(extract_params)):
                # calculate the output key, t1 p1 p3 etc
                extract_name = f'{self.config.extract_code}{extract_cnt + 1}'
                # wgrib params as a single string
                wgrib_params = extract_params[extract_name]
                # putting into a list to assemble the command for subprocess
                wgrib_params_list = wgrib_params.split(' ')
                # creating the command line to call wgrib
                cmd = [config.WGRIB_UTILITY, src_file]
                cmd.extend(wgrib_params_list)
                LOGGER.debug(f"running cmd: {' '.join(cmd[0:5])} ...")
                LOGGER.info(f"extracting from {src_file}")
                # running the command
                process = subprocess.Popen(cmd,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
                # collect the output from the command
                stdout, stderr = process.communicate()
                LOGGER.debug(f"stdout: {stdout[0:40]}...")
                LOGGER.debug(f"stderr: {stderr}")

                # extract_code like 'P' or 'T' + iteration number
                # creates key, ie P1, P2, T1, T2 etc...
                # put the output into a dictionary where the key corresponds
                # with the output type, ie p1, p2 etc...
                if extract_name not in extract_output_dict:
                    extract_output_dict[extract_name] = ''
                LOGGER.debug(f"stdout type: {type(stdout)}")
                extract_output_dict[extract_name] = extract_output_dict[extract_name] + stdout.decode("utf-8")
        os.chdir(start_dir)
        return extract_output_dict

    def get_url(self, iterator=None):
        """templates can use any property that is populated in the class
        This method looks at what properties are required, and uses them
        to create the url string using the url format string.
        """
        fstring_properties = self.get_property_in_fstring(self.config.url_template)
        if iterator and 'iterator' in self.config.file_template:
            fstring_properties['iterator'] = iterator
        url = self.config.url_template.format(**fstring_properties)
        LOGGER.debug(f'url: {url}')
        return url

    def get_property_in_fstring(self, fstring):
        """_summary_

        :param fstring: _description_
        :return: _description_
        """
        fstring_property_dict = {}
        properties = self.get_property_list()
        for prop in properties:
            if prop in fstring:
                fstring_property_dict[prop] = getattr(self.config, prop)
        return fstring_property_dict

    def get_property_list(self):
        property_list = []
        props = inspect.getmembers(self.config)
        for prop in props:
            if prop[0][0] != '_':
                property_list.append(prop[0])
        return property_list

    def get_src_file(self, iterator=None):
        LOGGER.debug(f"iterator: {iterator}")
        fstring_properties = self.get_property_in_fstring(self.config.file_template)
        if iterator and 'iterator' in self.config.file_template:
            fstring_properties['iterator'] = iterator
        LOGGER.debug(f"properties: {fstring_properties}")
        LOGGER.debug(f"fstring: {self.config.file_template}")
        file_name = self.config.file_template.format(**fstring_properties)
        LOGGER.debug(f"file_name: {file_name}")
        return file_name

class CoalateGribOutput:
    """
    There are 4 different grib files that get downloaded from env can.
    There are numerous files for each type
    WGRIB2 executable gets run against each file with 4 different sets
    of input parameters
    The output from the WGRIB2 command is collected in a dictionary
    with keys that correspond with the various output types
        P1, P2, P3... T1, T2, T3.. etc

    The class exists to combine the various dictionaries into a single
    dictionary, and then output the results of the single dictionary
    to files.
    """

    def __init__(self):
        self.grib_outputs = {}

    def add_dict(self, input_dict):
        for key in input_dict:
            if key not in self.grib_outputs:
                self.grib_outputs[key] =  ''
            self.grib_outputs[key] = self.grib_outputs[key] + input_dict[key]

    def output(self, output_directory):
        """writes the combined grib data output to text files

        :param output_directory: _description_
        """
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        for key in self.grib_outputs:
            outfile = os.path.join(output_directory, f'{key}.txt')
            with open(outfile, 'w') as fh:
                fh.write(self.grib_outputs[key])

class CopyCMC2ObjectStorage:
    def __init__(self):
        self.objstor = ObjectStore.ObjectStoreUtil()
        self.grib_confs = GetGribConfig.GribConfigCollection()

    def copy_to_ostore(self, src_folder, ostore_folder):
        # iterate over the various configs...
        # copy tmp/gribs/<date> to ostore
        src_files = os.listdir(src_folder)

        ostore_objects = self.objstor.listObjects(ostore_folder, recursive=True, returnFileNamesOnly=True)
        ostore_objects = [os.path.basename(ostore_file) for ostore_file in ostore_objects]

        LOGGER.info(f"found {len(ostore_objects)} in the ostore folder: {ostore_folder}")
        for src_file in src_files:
            src_file_path = os.path.join(src_folder, src_file)
            ostore_file_path = os.path.join(ostore_folder, src_file)
            if src_file not in ostore_objects:
                LOGGER.debug(f"creating ostore folder: {ostore_file_path}")
                self.objstor.putObject(ostore_file_path, src_file_path)

if __name__ == '__main__':
    dest_folder = 'tmp'
    reg1_config = GetGribConfig.GribRegional_1()
    reg1_get = GetGrib(dest_folder, reg1_config)
    reg1_get.get()

