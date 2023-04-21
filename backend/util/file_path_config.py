import os.path


def get_log_config_file_path():
    # returns the path to the logging config file
    config_file = os.path.realpath(os.path.join(
        os.path.dirname(__file__),
        '..',
        'logging.config'
    ))
    return config_file