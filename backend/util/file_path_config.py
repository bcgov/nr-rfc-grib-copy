# util module to calculate various file paths

import os.path


def get_log_config_file_path():
    """Calculates the path to the logging config file

    :return: path to the logging config file
    """
    # returns the path to the logging config file
    config_file = os.path.realpath(os.path.join(
        os.path.dirname(__file__),
        '..',
        'config',
        'logging.config'
    ))
    return config_file