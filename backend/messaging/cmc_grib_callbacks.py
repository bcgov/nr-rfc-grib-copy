# contains the callback functions used for CMC grib messages / channels

import logging
import pathlib

import db.message_cache
import requests
import util.config

LOGGER = logging.getLogger(__name__)

class CMC_Grib_Callback:

    def __init__(self):
        # load any residual transactions possibly
        self.emit_cnt = 0

        # init db connection
        self.mc = db.message_cache.MessageCache()

        # whether to ack messages or not
        self.ack = util.config.MESSAGE_ACK

        # current idem key
        self.cur_idem_key = self.mc.get_current_idempotency_key()

        # TODO: check for multiple idem keys and figure out logic for those
        self.emit_cached_events()


    def emit_cached_events(self):
        idem_keys = self.mc.get_cached_id_keys()
        for idem_key in idem_keys:
            if self.mc.is_all_data_there(idem_key=idem_key):
                # emit event...
                self.emit_event(idem_key=idem_key)

    def cmc_callback(self, body, delivery_tag, channel):
        # example of emitted message body string:
        #   20230419181943.032 https://hpfx.collab.science.gc.ca /20230419/WXO-DD/.hello_weather/observations/08/08005.1.OBS.MAR.EN.SPX~20230419180500-20230419200500-1557
        #   0 - datetimestamp (i think!)
        #   1 - protocol / domain to server w/ data
        #   2 - directory path to the data that is now available
        LOGGER.debug(f"param: {channel}")
        LOGGER.debug(f"body: {body}")

        msg_body = body.decode()
        msg_list = msg_body.split(' ')
        emitted_file_name = msg_list[2]
        LOGGER.debug(f"message recieved: {msg_body}")

        # because we are using the hpfx server, we are expecting the date to be
        # the first directory in the message (path)
        # extracting that from the message
        # /20230422/WXO-DD/model_gem_global/15km/grib2/lat_lon/00/150/CMC_glb_TMP_TGL_2_latlon.15x.15_2023042200_P150.grib2
        p = pathlib.Path(emitted_file_name)
        date_str = p.parts[1]

        # store event in cache - caching every event to help with debugging
        self.mc.cache_event(emitted_file_name, idem_key=date_str)

        # is this an event we are interested in, working on the current date that
        # has been calculated in the message cache property 'current_idempotency_key'
        if self.mc.is_event_of_interest(emitted_file_name, idem_key=date_str):
            # check to see if all the events are available.
            if self.mc.is_all_data_there(idem_key=date_str):
                LOGGER.info(f"data complete for idem key: {self.mc.current_idempotency_key}")
                self.emit_event(idem_key=date_str)
        LOGGER.debug("acknowledging message")
        if self.ack:
            channel.basic_ack(delivery_tag)

    def emit_event(self, idem_key=None):
        """called when a new event is emitted
        """
        if idem_key is None:
            idem_key = self.mc.current_idempotency_key
        LOGGER.info(f"NEW EVENT EMITTING: {idem_key}")

        # make webhook call to github action
        github_org = util.config.GH_ORG
        github_repo = util.config.GH_REPO
        github_token = util.config.GH_TOKEN
        remote_type = 'run-cmc-grib-download'
        #remote_type = 'do-something' # test job

        # if self.emit_cnt > 0:

        payload = {"event_type": remote_type, "client_payload": {"idem_key": f"{idem_key}","message":"demo"}}
        header = {"Accept": "application/vnd.github+json", "Authorization": f"token {github_token}"}
        url = f'https://api.github.com/repos/{github_org}/{github_repo}/dispatches'
        resp = requests.post(url=url, headers=header, json=payload)
        #resp.raise_for_status()
        LOGGER.info(f"webhook call to github action status: {resp.status_code}")
        LOGGER.debug(f"url: {url}")

        # TODO: commenting this out until the downstream events are configured
        #       so that we do not lose the events that are currently being cached
        #       in the database.
        if resp.ok:
            self.mc.clear_cache(idem_key=idem_key)
        else:
            LOGGER.error(f"webhook call to github action failed: {resp.status_code} idem_key: {idem_key} url: {url}")

        self.emit_cnt += 1
