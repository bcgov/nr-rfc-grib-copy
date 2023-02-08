"""class to help setup download for different grib2 files

https://spire.com/tutorial/spire-weather-tutorial-intro-to-processing-grib2-data-with-python/
"""
import abc
import datetime
import inspect
import logging
import sys

import pytz

LOGGER = logging.getLogger(__name__)

class GribConfig(metaclass=abc.ABCMeta):
    """Using this class to ensure that subclasses of it posses the expected
    properties

    :param metaclass: declaring as an Abstract base class, defaults to abc.ABCMeta
    """

    @property
    @abc.abstractmethod
    def model_number(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def url_template(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def date_str_format(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def iteratorlist(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def file_template(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def timezone(self):
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def extract_code(self):
        raise NotImplementedError

    @property
    def datestr(self):
        now = datetime.datetime.now(self.timezone)
        datestr = now.strftime(self.date_str_format)
        return datestr

    @property
    def extract_params_object(self):
        # TODO: replace this logic with a method that returns the params for the
        #       input extract_name
        extract_params = WGribExtractParams()
        return extract_params

    # @property
    # def wgrib_commandline_parameters(self):
    #     # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     wgrib_params1 = "-lon 237.64 49.025 -lon 238.24 49.243 -lon 238.719 50.708 -lon 235.84 49.35 -lon 231.843 52.185 -lon 237.064 50.102 -lon 240.71 52.129 -lon 229.361 53.493 -lon 236.998 49.126 -lon 234.041 54.383 -lon 236.889 50.144 -lon 228.984 51.936 -lon 232.529 52.187 -lon 239.918 51.653 -lon 238.315 51.266 -lon 238.495 51.145 -lon 235.1 49.717 -lon 244.218 49.612 -lon 243.499 49.082 -lon 239.817 55.742 -lon 229.974 58.426 -lon 236.189 49.209 -lon 236.561 48.432 -lon 233.457 49.383 -lon 234.007 50.454 -lon 237.403 58.836 -lon 235.714 54.455 -lon 239.26 56.238 -lon 229.302 54.58 -lon 232.368 50.94 -lon 229.639 54.172 -lon 238.507 49.37 -lon 238.502 49.368 -lon 236.701 49.488 -lon 239.558 50.702 -lon 239.551 50.702 -lon 240.6 49.941 -lon 240.622 49.957 -lon 227.228 53.316 -lon 226.942 54.255 -lon 238.066 50.684 -lon 238.418 50.224 -lon 238.418 50.224 -lon 236.862 55.305 -lon 236.867 55.299 -lon 236.47 48.575 -lon 239.222 50.113 -lon 242.183 50.269 -lon 242.695 49.491 -lon 236.281 48.824 -lon 234.003 53.772 -lon 240.559 49.028 -lon 237.266 50.306 -lon 240.398 49.462 -lon 237.31 49.208 -lon 236.735 49.33 -lon 235.073 49.317 -lon 232.633 50.681 -lon 235.503 49.835 -lon 237.328 53.889 -lon 237.322 53.884 -lon 239.49 49.465 -lon 235.864 52.114 -lon 235.606 49.337 -lon 237.494 53.027 -lon 237.49 53.026 -lon 241.824 50.958 -lon 241.817 50.967 -lon 228.339 54.159 -lon 240.709 50.703 -lon 228.187 53.25 -lon 228.186 53.254 -lon 231.092 50.821 -lon 236.872 48.775 -lon 236.955 48.784 -lon 236.285 49.458 -lon 236.079 48.377 -lon 232.811 54.824 -lon 232.817 54.825 -lon 232.06 50.112 -lon 245.116 49.745 -lon 236.839 49.783 -lon 240.351 49.563 -lon 235.597 51.675 -lon 231.422 54.469 -lon 236.695 48.457 -lon 236.813 49.182 -lon 236.878 49.295 -lon 236.816 49.195 -lon 240.806 50.223 -lon 236.675 48.413 -lon 236.574 48.647 -lon 242.261 49.112 -lon 236.807 49.347 -lon 237.045 50.129 -lon 237.216 49.018 -lon 237.946 52.183 -lon 243.655 51.443"
    #     # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     wgrib_params2 = "-lon 241.452 52.907 -lon 239.683 53.308 -lon 238.509 53.057 -lon 238.994 54.106 -lon 239.618 53.786 -lon 238.976 53.622 -lon 233.581 53.731 -lon 232.355 53.586 -lon 233.127 53.164 -lon 237.076 50.796 -lon 237.794 50.764 -lon 239.132 52.107 -lon 238.645 52.832 -lon 237.071 50.536 -lon 238.288 49.032 -lon 238.341 49.661 -lon 240.677 52.182 -lon 240.276 52.596 -lon 239.968 52.204 -lon 241.382 50.45 -lon 241.014 51.406 -lon 241.853 51.035 -lon 241.774 52.221 -lon 241.649 50.068 -lon 242.296 50.434 -lon 245.031 49.448 -lon 244.226 49.251 -lon 243.863 51.06 -lon 243.074 50.64 -lon 242.913 49.69 -lon 241.323 49.552 -lon 241.051 49.945 -lon 240.023 49.867 -lon 239.227 49.094 -lon 235.54 51.244 -lon 235.378 51.776 -lon 236.564 50.154 -lon 234.321 49.704 -lon 235.724 48.97 -lon 233.75 52.481 -lon 237.362 55.353 -lon 233.251 57.548 -lon 234.927 57.624 -lon 233.258 56.437 -lon 233.696 54.197 -lon 232.302 55.863 -lon 232.325 54.646 -lon 231.29 55.152 -lon 229.75 57.567"
    #     # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     wgrib_params3 = "-lon 235.353 48.928 -lon 234.211 50.049 -lon 233.393 50.213 -lon 235.927 50.568 -lon 234.972 51.189 -lon 233.549 51.593 -lon 231.14 54.917 -lon 231.423 54.17 -lon 228.829 57.914 -lon 226.333 59.583 -lon 229.992 57.857 -lon 229.747 56.983 -lon 238.603 58.838 -lon 239.211 59.421 -lon 235.901 59.617 -lon 238.703 57.497 -lon 239.763 57.782 -lon 237.542 56.435 -lon 234.689 58.866 -lon 239.066 55.027 -lon 237.441 57.077 -lon 236.384 57.884 -lon 238.01 56.035 -lon 238.235 56.718 -lon 239.424 54.633 -lon 237.483 55.525 -lon 235.768 55.58 -lon 237.726 54.716 -lon 234.82 57.019 -lon 237.309 54.509 -lon 236.921 54.726 -lon 235.733 55.023 -lon 232.966 56.329 -lon 233.373 54.412 -lon 233.947 55.688 -lon 234.588 53.071 -lon 235.488 53.383 -lon 234.475 54.362 -lon 233.2 55.033 -lon 234.523 55.082 -lon 233.422 55.553 -lon 232.601 54.075 -lon 239.364 53.929 -lon 236.75 52.535 -lon 236.727 52.084 -lon 234.697 52.457 -lon 236.182 51.48 -lon 235.518 52.71 -lon 237.338 51.452 -lon 235.125 51.702 -lon 233.972 52.251 -lon 240.825 52.453 -lon 239.134 49.715 -lon 239.816 49.139 -lon 241.34 52.372 -lon 241.897 51.997 -lon 243.215 51.065 -lon 243.636 51.042 -lon 242.458 51.716 -lon 242.82 50.781 -lon 241.374 49.96 -lon 240.912 49.457 -lon 241.64 49.527 -lon 241.919 49.699 -lon 242.56 49.785 -lon 244.334 50.495 -lon 244.845 49.288 -lon 243.945 50.513 -lon 245.463 49.079 -lon 244.263 49.922 -lon 244.023 50.145 -lon 231.007 55.288 -lon 232.353 55.435 -lon 231.687 55.027 -lon 230.9 56.013 -lon 231.958 55.6 -lon 230.707 56.348 -lon 231.295 55.577 -lon 239.514 55.296 -lon 234.489 59.334 -lon 232.665 59.723 -lon 232.875 58.727 -lon 230.89 59.368 -lon 231.292 60.067 -lon 245.1 50.087 -lon 244.013 49.454 -lon 244.734 50.185 -lon 242.77 51.177 -lon 243.755 50.819 -lon 242.943 51.436 -lon 241.409 51.853 -lon 240.876 49.767 -lon 244.786 49.667 -lon 241.728 51.515 -lon 235.799 48.571 -lon 233.566 50.37 -lon 234.718 49.17 -lon 233.072 50.132 -lon 239.618 56.558 -lon 236.59 50.62 -lon 237.894 53.526 -lon 238.44 53.463 -lon 239.088 52.91 -lon 239.015 52.391 -lon 238.611 51.913 -lon 240.118 51.253"
    #     # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    #     # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
    #     wgrib_params4 = "-lon 239.518 50.673 -lon 243.254 49.436 -lon 238.642 49.655 -lon 239.379 49.948 -lon 239.543 49.433 -lon 244.37 49.459 -lon 235.067 49.377 -lon 236.677 53.865 -lon 237.935 52.91 -lon 238.163 49.723 -lon 238.238 53.262 -lon 240.706 52.122 -lon 235.298 49.437 -lon 240.007 49.868 -lon 234.243 54.259 -lon 240.162 50.888 -lon 235.561 53.401 -lon 239.142 53.576 -lon 236.125 49.048 -lon 244.458 49.188 -lon 237.68 51.403 -lon 239.905 51.629 -lon 239.61 51.724 -lon 244.152 49.667 -lon 242.042 50.765 -lon 241.577 50.602 -lon 237.502 50.522 -lon 243.033 49.367 -lon 229.981 58.426 -lon 243.617 49.784 -lon 234.221 53.502 -lon 241.422 49.433 -lon 242.12 50.383 -lon 240.52 50.207 -lon 237.311 50.911 -lon 238.362 49.104 -lon 237.426 58.841 -lon 235.739 54.394 -lon 237.751 51.177 -lon 233.052 54.801 -lon 238.258 52.47 -lon 239.712 50.27 -lon 243.836 49.125 -lon 242.936 50.366 -lon 241.513 51.669 -lon 241.584 49.031 -lon 234.124 53.945 -lon 237.12 50.796 -lon 233.41 52.387 -lon 240.887 51.523 -lon 237.404 53.411 -lon 240.287 53.345 -lon 235.223 53.936 -lon 227.884 53.253 -lon 238.603 52.33 -lon 238.126 52.05 -lon 244.775 49.047 -lon 239.164 50.615 -lon 238.487 52.615 -lon 238.112 50.672 -lon 238.838 51.507 -lon 241.227 50.352 -lon 236.907 55.322 -lon 239.588 51.211 -lon 239.847 53.295 -lon 240.585 49.148 -lon 238.642 50.792 -lon 238.283 51.375 -lon 239.254 50.087 -lon 235.863 48.823 -lon 233.072 53.942 -lon 237.979 49.902 -lon 242.006 49.254 -lon 236.404 52.958 -lon 242.213 49.502 -lon 233.793 55.135 -lon 236.246 54.155 -lon 233.611 54.019 -lon 239.326 50.504 -lon 233.483 53.987 -lon 237.271 50.306 -lon 242.586 49.051 -lon 240.447 49.518 -lon 232.674 54.684 -lon 238 51.817 -lon 243.145 49.906 -lon 234.706 50.027 -lon 241.783 51.06 -lon 237.496 51.959 -lon 241.063 49.052 -lon 243.207 50.613 -lon 240.765 50.685 -lon 236.526 48.774 -lon 238.348 54.17 -lon 241.085 51.274 -lon 240.997 50.863 -lon 233.883 57.852 -lon 238.448 50.439 -lon 242.552 49.497 -lon 239.133 50.924 -lon 238.345 50.351 -lon 242.239 51.751 -lon 235.395 51.907 -lon 242.573 50.605 -lon 236.435 49.428 -lon 234.869 50.271 -lon 236.613 49.586 -lon 235.385 50.104 -lon 240.37 50.803 -lon 237.427 49.264 -lon 240.685 52.788 -lon 240.701 52.87 -lon 235.991 54.056 -lon 239.756 52.343 -lon 239.35 51.67"
    #     wgrib_params_all = [wgrib_params1, wgrib_params2, wgrib_params3, wgrib_params4]
    #     return wgrib_params_all


class WGribExtractParams:
    def __init__(self):
        self.wgrib_params_dict = {}
        self.define_params()

    def define_params(self):
        # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        wgrib_params1 = "-lon 237.64 49.025 -lon 238.24 49.243 -lon 238.719 50.708 -lon 235.84 49.35 -lon 231.843 52.185 -lon 237.064 50.102 -lon 240.71 52.129 -lon 229.361 53.493 -lon 236.998 49.126 -lon 234.041 54.383 -lon 236.889 50.144 -lon 228.984 51.936 -lon 232.529 52.187 -lon 239.918 51.653 -lon 238.315 51.266 -lon 238.495 51.145 -lon 235.1 49.717 -lon 244.218 49.612 -lon 243.499 49.082 -lon 239.817 55.742 -lon 229.974 58.426 -lon 236.189 49.209 -lon 236.561 48.432 -lon 233.457 49.383 -lon 234.007 50.454 -lon 237.403 58.836 -lon 235.714 54.455 -lon 239.26 56.238 -lon 229.302 54.58 -lon 232.368 50.94 -lon 229.639 54.172 -lon 238.507 49.37 -lon 238.502 49.368 -lon 236.701 49.488 -lon 239.558 50.702 -lon 239.551 50.702 -lon 240.6 49.941 -lon 240.622 49.957 -lon 227.228 53.316 -lon 226.942 54.255 -lon 238.066 50.684 -lon 238.418 50.224 -lon 238.418 50.224 -lon 236.862 55.305 -lon 236.867 55.299 -lon 236.47 48.575 -lon 239.222 50.113 -lon 242.183 50.269 -lon 242.695 49.491 -lon 236.281 48.824 -lon 234.003 53.772 -lon 240.559 49.028 -lon 237.266 50.306 -lon 240.398 49.462 -lon 237.31 49.208 -lon 236.735 49.33 -lon 235.073 49.317 -lon 232.633 50.681 -lon 235.503 49.835 -lon 237.328 53.889 -lon 237.322 53.884 -lon 239.49 49.465 -lon 235.864 52.114 -lon 235.606 49.337 -lon 237.494 53.027 -lon 237.49 53.026 -lon 241.824 50.958 -lon 241.817 50.967 -lon 228.339 54.159 -lon 240.709 50.703 -lon 228.187 53.25 -lon 228.186 53.254 -lon 231.092 50.821 -lon 236.872 48.775 -lon 236.955 48.784 -lon 236.285 49.458 -lon 236.079 48.377 -lon 232.811 54.824 -lon 232.817 54.825 -lon 232.06 50.112 -lon 245.116 49.745 -lon 236.839 49.783 -lon 240.351 49.563 -lon 235.597 51.675 -lon 231.422 54.469 -lon 236.695 48.457 -lon 236.813 49.182 -lon 236.878 49.295 -lon 236.816 49.195 -lon 240.806 50.223 -lon 236.675 48.413 -lon 236.574 48.647 -lon 242.261 49.112 -lon 236.807 49.347 -lon 237.045 50.129 -lon 237.216 49.018 -lon 237.946 52.183 -lon 243.655 51.443"
        # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        wgrib_params2 = "-lon 241.452 52.907 -lon 239.683 53.308 -lon 238.509 53.057 -lon 238.994 54.106 -lon 239.618 53.786 -lon 238.976 53.622 -lon 233.581 53.731 -lon 232.355 53.586 -lon 233.127 53.164 -lon 237.076 50.796 -lon 237.794 50.764 -lon 239.132 52.107 -lon 238.645 52.832 -lon 237.071 50.536 -lon 238.288 49.032 -lon 238.341 49.661 -lon 240.677 52.182 -lon 240.276 52.596 -lon 239.968 52.204 -lon 241.382 50.45 -lon 241.014 51.406 -lon 241.853 51.035 -lon 241.774 52.221 -lon 241.649 50.068 -lon 242.296 50.434 -lon 245.031 49.448 -lon 244.226 49.251 -lon 243.863 51.06 -lon 243.074 50.64 -lon 242.913 49.69 -lon 241.323 49.552 -lon 241.051 49.945 -lon 240.023 49.867 -lon 239.227 49.094 -lon 235.54 51.244 -lon 235.378 51.776 -lon 236.564 50.154 -lon 234.321 49.704 -lon 235.724 48.97 -lon 233.75 52.481 -lon 237.362 55.353 -lon 233.251 57.548 -lon 234.927 57.624 -lon 233.258 56.437 -lon 233.696 54.197 -lon 232.302 55.863 -lon 232.325 54.646 -lon 231.29 55.152 -lon 229.75 57.567"
        # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        wgrib_params3 = "-lon 235.353 48.928 -lon 234.211 50.049 -lon 233.393 50.213 -lon 235.927 50.568 -lon 234.972 51.189 -lon 233.549 51.593 -lon 231.14 54.917 -lon 231.423 54.17 -lon 228.829 57.914 -lon 226.333 59.583 -lon 229.992 57.857 -lon 229.747 56.983 -lon 238.603 58.838 -lon 239.211 59.421 -lon 235.901 59.617 -lon 238.703 57.497 -lon 239.763 57.782 -lon 237.542 56.435 -lon 234.689 58.866 -lon 239.066 55.027 -lon 237.441 57.077 -lon 236.384 57.884 -lon 238.01 56.035 -lon 238.235 56.718 -lon 239.424 54.633 -lon 237.483 55.525 -lon 235.768 55.58 -lon 237.726 54.716 -lon 234.82 57.019 -lon 237.309 54.509 -lon 236.921 54.726 -lon 235.733 55.023 -lon 232.966 56.329 -lon 233.373 54.412 -lon 233.947 55.688 -lon 234.588 53.071 -lon 235.488 53.383 -lon 234.475 54.362 -lon 233.2 55.033 -lon 234.523 55.082 -lon 233.422 55.553 -lon 232.601 54.075 -lon 239.364 53.929 -lon 236.75 52.535 -lon 236.727 52.084 -lon 234.697 52.457 -lon 236.182 51.48 -lon 235.518 52.71 -lon 237.338 51.452 -lon 235.125 51.702 -lon 233.972 52.251 -lon 240.825 52.453 -lon 239.134 49.715 -lon 239.816 49.139 -lon 241.34 52.372 -lon 241.897 51.997 -lon 243.215 51.065 -lon 243.636 51.042 -lon 242.458 51.716 -lon 242.82 50.781 -lon 241.374 49.96 -lon 240.912 49.457 -lon 241.64 49.527 -lon 241.919 49.699 -lon 242.56 49.785 -lon 244.334 50.495 -lon 244.845 49.288 -lon 243.945 50.513 -lon 245.463 49.079 -lon 244.263 49.922 -lon 244.023 50.145 -lon 231.007 55.288 -lon 232.353 55.435 -lon 231.687 55.027 -lon 230.9 56.013 -lon 231.958 55.6 -lon 230.707 56.348 -lon 231.295 55.577 -lon 239.514 55.296 -lon 234.489 59.334 -lon 232.665 59.723 -lon 232.875 58.727 -lon 230.89 59.368 -lon 231.292 60.067 -lon 245.1 50.087 -lon 244.013 49.454 -lon 244.734 50.185 -lon 242.77 51.177 -lon 243.755 50.819 -lon 242.943 51.436 -lon 241.409 51.853 -lon 240.876 49.767 -lon 244.786 49.667 -lon 241.728 51.515 -lon 235.799 48.571 -lon 233.566 50.37 -lon 234.718 49.17 -lon 233.072 50.132 -lon 239.618 56.558 -lon 236.59 50.62 -lon 237.894 53.526 -lon 238.44 53.463 -lon 239.088 52.91 -lon 239.015 52.391 -lon 238.611 51.913 -lon 240.118 51.253"
        # CMC_reg_PRATE_SFC_0_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_PRATE_SFC_0_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
        # CMC_glb_TMP_TGL_2_latlon.15x.15_%YYYY%%MT%%DD%%GH%_P%%A.grib2
        wgrib_params4 = "-lon 239.518 50.673 -lon 243.254 49.436 -lon 238.642 49.655 -lon 239.379 49.948 -lon 239.543 49.433 -lon 244.37 49.459 -lon 235.067 49.377 -lon 236.677 53.865 -lon 237.935 52.91 -lon 238.163 49.723 -lon 238.238 53.262 -lon 240.706 52.122 -lon 235.298 49.437 -lon 240.007 49.868 -lon 234.243 54.259 -lon 240.162 50.888 -lon 235.561 53.401 -lon 239.142 53.576 -lon 236.125 49.048 -lon 244.458 49.188 -lon 237.68 51.403 -lon 239.905 51.629 -lon 239.61 51.724 -lon 244.152 49.667 -lon 242.042 50.765 -lon 241.577 50.602 -lon 237.502 50.522 -lon 243.033 49.367 -lon 229.981 58.426 -lon 243.617 49.784 -lon 234.221 53.502 -lon 241.422 49.433 -lon 242.12 50.383 -lon 240.52 50.207 -lon 237.311 50.911 -lon 238.362 49.104 -lon 237.426 58.841 -lon 235.739 54.394 -lon 237.751 51.177 -lon 233.052 54.801 -lon 238.258 52.47 -lon 239.712 50.27 -lon 243.836 49.125 -lon 242.936 50.366 -lon 241.513 51.669 -lon 241.584 49.031 -lon 234.124 53.945 -lon 237.12 50.796 -lon 233.41 52.387 -lon 240.887 51.523 -lon 237.404 53.411 -lon 240.287 53.345 -lon 235.223 53.936 -lon 227.884 53.253 -lon 238.603 52.33 -lon 238.126 52.05 -lon 244.775 49.047 -lon 239.164 50.615 -lon 238.487 52.615 -lon 238.112 50.672 -lon 238.838 51.507 -lon 241.227 50.352 -lon 236.907 55.322 -lon 239.588 51.211 -lon 239.847 53.295 -lon 240.585 49.148 -lon 238.642 50.792 -lon 238.283 51.375 -lon 239.254 50.087 -lon 235.863 48.823 -lon 233.072 53.942 -lon 237.979 49.902 -lon 242.006 49.254 -lon 236.404 52.958 -lon 242.213 49.502 -lon 233.793 55.135 -lon 236.246 54.155 -lon 233.611 54.019 -lon 239.326 50.504 -lon 233.483 53.987 -lon 237.271 50.306 -lon 242.586 49.051 -lon 240.447 49.518 -lon 232.674 54.684 -lon 238 51.817 -lon 243.145 49.906 -lon 234.706 50.027 -lon 241.783 51.06 -lon 237.496 51.959 -lon 241.063 49.052 -lon 243.207 50.613 -lon 240.765 50.685 -lon 236.526 48.774 -lon 238.348 54.17 -lon 241.085 51.274 -lon 240.997 50.863 -lon 233.883 57.852 -lon 238.448 50.439 -lon 242.552 49.497 -lon 239.133 50.924 -lon 238.345 50.351 -lon 242.239 51.751 -lon 235.395 51.907 -lon 242.573 50.605 -lon 236.435 49.428 -lon 234.869 50.271 -lon 236.613 49.586 -lon 235.385 50.104 -lon 240.37 50.803 -lon 237.427 49.264 -lon 240.685 52.788 -lon 240.701 52.87 -lon 235.991 54.056 -lon 239.756 52.343 -lon 239.35 51.67"

        self.wgrib_params_dict = {
            "P1": wgrib_params1,
            "T1": wgrib_params1,
            "P2": wgrib_params2,
            "T2": wgrib_params2,
            "P3": wgrib_params3,
            "T3": wgrib_params3,
            "P4": wgrib_params4,
            "T4": wgrib_params4,
        }

    def get_wgrib_params(self, extract_code):
        """given a code like 'P' or 'T' returns a dictionary with only parameters
        for that type

        :param extract_code: _description_
        :raises InvalidExtractNameError: _description_
        :return: _description_
        """
        extract_dict = {}
        for extract_key in self.wgrib_params_dict.keys():
            if extract_key[0].upper() == extract_code:
                extract_dict[extract_key] = self.wgrib_params_dict[extract_key]

        if not extract_dict:
            extract_names_all = self.wgrib_params_dict.keys()
            raise InvalidExtractCodeError(extract_code)
        return extract_dict


class InvalidExtractCodeError(Exception):
    def __init__(self, extract_code):
        self.message = (
            f"requested an extract code: {extract_code} with no corresponding " + "values"
        )
        super().__init__(self.message)


class GribRegional_1(GribConfig):
    model_number = "06"
    extract_code = "P"

    url_template = "http://hpfx.collab.science.gc.ca/{datestr}/WXO-DD/model_gem_regional/10km/grib2/06/{iterator}"
    date_str_format = "%Y%m%d"
    iteratorlist = [
        "003",
        "006",
        "009",
        "012",
        "015",
        "018",
        "021",
        "024",
        "027",
        "030",
        "033",
        "036",
        "039",
        "042",
        "045",
        "048",
        "051",
        "054",
    ]

    file_template = "CMC_reg_PRATE_SFC_0_ps10km_{datestr}{model_number}_P{iterator}.grib2"
    # timezone = pytz.utc
    timezone = pytz.timezone("America/Vancouver")


class GribRegional_2(GribConfig):
    model_number = "06"
    extract_code = "T"
    url_template = "http://hpfx.collab.science.gc.ca/{datestr}/WXO-DD/model_gem_regional/10km/grib2/06/{iterator}"
    iteratorlist = [
        "000",
        "003",
        "006",
        "009",
        "012",
        "015",
        "018",
        "021",
        "024",
        "027",
        "030",
        "033",
        "036",
        "039",
        "042",
        "045",
        "048",
        "051",
        "054",
    ]
    date_str_format = "%Y%m%d"
    file_template = "CMC_reg_TMP_TGL_2_ps10km_{datestr}{model_number}_P{iterator}.grib2"
    # CMC_reg_TMP_TGL_2_ps10km_%YYYY%%MT%%DD%%RH%_P%%A.grib2
    # timezone = pytz.utc
    timezone = pytz.timezone("America/Vancouver")
    extract_code = "T"


class GribGlobal_1(GribConfig):
    model_number = "00"
    iteratorlist = [
        "063",
        "066",
        "069",
        "072",
        "075",
        "078",
        "081",
        "084",
        "087",
        "090",
        "093",
        "096",
        "099",
        "102",
        "105",
        "108",
        "111",
        "114",
        "117",
        "120",
        "123",
        "126",
        "129",
        "132",
        "135",
        "138",
        "141",
        "144",
        "147",
        "150",
        "153",
        "156",
        "159",
        "162",
        "165",
        "168",
        "171",
        "174",
        "177",
        "180",
        "183",
        "186",
        "189",
        "192",
        "195",
        "198",
        "201",
        "204",
        "207",
        "210",
        "213",
        "216",
        "219",
        "222",
        "225",
        "228",
        "231",
        "234",
        "237",
        "240",
    ]
    file_template = "CMC_glb_PRATE_SFC_0_latlon.15x.15_{datestr}{model_number}_P{iterator}.grib2"
    url_template = (
        "https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{model_number}/{iterator}"
    )
    date_str_format = "%Y%m%d"
    timezone = pytz.timezone("America/Vancouver")
    extract_code = "P"


class GribGlobal_2(GribConfig):
    model_number = "00"
    iteratorlist = [
        "006",
        "009",
        "012",
        "015",
        "063",
        "066",
        "069",
        "072",
        "075",
        "078",
        "081",
        "084",
        "087",
        "090",
        "093",
        "096",
        "099",
        "102",
        "105",
        "108",
        "111",
        "114",
        "117",
        "120",
        "123",
        "126",
        "129",
        "132",
        "135",
        "138",
        "141",
        "144",
        "147",
        "150",
        "153",
        "156",
        "159",
        "162",
        "165",
        "168",
        "171",
        "174",
        "177",
        "180",
        "183",
        "186",
        "189",
        "192",
        "195",
        "198",
        "201",
        "204",
        "207",
        "210",
        "213",
        "216",
        "219",
        "222",
        "225",
        "228",
        "231",
        "234",
        "237",
        "240",
    ]
    file_template = "CMC_glb_TMP_TGL_2_latlon.15x.15_{datestr}{model_number}_P{iterator}.grib2"
    url_template = (
        "https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/{model_number}/{iterator}"
    )
    date_str_format = "%Y%m%d"
    timezone = pytz.timezone("America/Vancouver")
    extract_code = "T"


class GribConfigCollection():
    def __init__(self):
        self.cls_dict = self.get_class_list()
        


    def get_class_list(self):
        """returns a list of class instances that are subclasses from 
        abc.ABCMeta, ie those that contain actual config implementations
        """
        class_dict = {}
        module_name = __name__
        LOGGER.debug(f"module name: {module_name}")
        clsmembers = inspect.getmembers(sys.modules[module_name], inspect.isclass)
        for cls_mem in clsmembers:
            class_name = cls_mem[0]
            class_inst = cls_mem[1]
            if cls_mem[1].__class__ is abc.ABCMeta:
                class_dict[class_name] = class_inst
        return class_dict



extractParams = WGribExtractParams()




if __name__ == "__main__":
    # testing the abc to confirm class variables required

    gribtest = GribRegional_1()
    gribtest2 = GribRegional_2()
    gribtest3 = GribGlobal_1()
    gribtest4 = GribGlobal_2()

    fstring = gribtest4.url_template.format(model_number=gribtest4.model_number, iterator="219")
    print(fstring)
    tz = pytz.timezone("America/Vancouver")
