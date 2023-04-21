# contains the callback functions used for CMC grib messages / channels

import logging

import db.message_cache

LOGGER = logging.getLogger(__name__)

class CMC_Grib_Callback:

    def __init__(self):
        # init db connection
        self.mc = db.message_cache.MessageCache()

        # current idem key
        self.cur_idem_key = self.mc.get_current_idempotency_key()

        # TODO: check for multiple idem keys and figure out logic for those

        # load any residual transactions possibly
        if self.mc.is_all_data_there():
            # emit event...
            self.emit_event()

    def cmc_callback(self, ch, method, properties, body):
        # example of emitted message body string:
        #   20230419181943.032 https://hpfx.collab.science.gc.ca /20230419/WXO-DD/.hello_weather/observations/08/08005.1.OBS.MAR.EN.SPX~20230419180500-20230419200500-1557
        #   0 - datetimestamp (i think!)
        #   1 - protocol / domain to server w/ data
        #   2 - directory path to the data that is now available
        msg_body = body.decode()
        msg_list = msg_body.split(' ')
        emitted_file_name = msg_list[2]

        # is this an event we are interested in
        if self.mc.is_event_of_interest(emitted_file_name):

            # store event in cache
            self.mc.cache_event(emitted_file_name)

            # check to see if all the events are available.
            if self.mc.is_all_data_there():
                LOGGER.info(f"data complete for idem key: {self.mc.current_idempotency_key}")
                self.emit_event()

    def emit_event(self):
        """called when a new event is emitted
        """
        LOGGER.info(f"NEW EVENT EMITTING: {self.mc.current_idempotency_key}")
        self.mc.clear_cache()
