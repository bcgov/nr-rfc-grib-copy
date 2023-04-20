# contains the callback functions used for CMC grib messages / channels

import db.message_cache


class CMC_Grib_Callback:

    def __init__(self):
        # init db connection
        self.mc = db.message_cache.MessageCache()
        # load any residual transactions possibly
        if self.mc.is_all_data_there()

    def cmc_callback(self, ch, method, properties, body):

        # example of emitted message body string:
        #   20230419181943.032 https://hpfx.collab.science.gc.ca /20230419/WXO-DD/.hello_weather/observations/08/08005.1.OBS.MAR.EN.SPX~20230419180500-20230419200500-1557
        #   0 - datetimestamp (i think!)
        #   1 - protocol / domain to server w/ data
        #   2 - directory path to the data that is now available
        msg_body = body.decode()
        msg_list = msg_body.split(' ')
        emitted_file_name = msg_list[2]

        # store event in cache
        self.mc.cache_event(emitted_file_name)

        # check to see if all the events are available.



