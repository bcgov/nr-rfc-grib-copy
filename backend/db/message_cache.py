"""
Provides message management.

Will be listening to events that correspond with data availability.

Determine if the event corresponds with data we are interested in.

Cache the event in persistent storage (database)

Identify if all the data we are expecting has been supplied or not.

Provides a recovery, in the event that the process crashes for some
reason, should start with filling in a list of the data that has
been cached.

"""

import collections
import datetime
import logging

import db.model
import util.config
import util.grib_file_config
from sqlalchemy import create_engine, delete, inspect, select
from sqlalchemy.orm import Session, sessionmaker

LOGGER = logging.getLogger(__name__)


class MessageCache:
    def __init__(self, db_str=None, id_key=None):
        # db file location should come from an env var, different depending
        # on local vs deployed
        if not db_str:
            db_str = util.config.get_db_string()

        self.db_str = db_str
        LOGGER.debug(f"db connection string: {db_str}")

        self.engine = create_engine(db_str, echo=False)
        self.init_db()

        self.session_maker = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        LOGGER.debug("session maker created")

        # now load any cached events from the database into memory
        LOGGER.debug("getting cached events ...")
        self.cached_events = self.get_cached_events_as_struct()
        for key in self.cached_events:
            LOGGER.debug(f"cached events for {key}: {len(self.cached_events[key])}")

        # data is collected daily so can use the date to identify a collection
        # of data
        self.current_idempotency_key = None
        if id_key is not None:
            self.current_idempotency_key = id_key

        self.current_idempotency_key = self.get_current_idempotency_key()
        LOGGER.debug("current idempotency key: %s", self.current_idempotency_key)

        # make sure the idempotency_key is in the in memory struct
        if self.current_idempotency_key not in self.cached_events:
            self.cached_events[self.current_idempotency_key] = []

        self.grib_config = util.grib_file_config.GribFiles()

        # getting a list of files that are expected per idem key
        # convert expected data into a dictionary using the idem_key as the key
        self.expected_data = {}
        self.expected_data[
            self.current_idempotency_key
        ] = self.grib_config.calculate_expected_file_list(
            only_file_path=True, date_str=self.current_idempotency_key
        )

        # # check for unemitted events
        # self.check_for_unemitted_events()

    # def check_for_unemitted_events(self):
    #     """ get the data that is in the database,
    #         iterate over the unique id keys,
    #         check to see if the data is there for the days that exist.
    #         emit the events associated if all the data is there
    #         get some kind of confirmation that the request was triggered
    #         delete all the data associated with the id keys that were emitted
    #     """
    #     un_emitted_idem_keys = self.get_cached_id_keys()
    #     for idem_key in un_emitted_idem_keys:
    #         if self.is_all_data_there(idem_key=idem_key):
    #             LOGGER.info(f"all data there for: {idem_key}")

    def get_cached_id_keys(self):
        """makes a database call to get all the id's that are currently in the
        database.
        """
        keys = []
        with Session(self.engine) as session:
            rows = session.query(db.model.Events.event_idempotency_key).distinct()
            # statement = select(db.model.Events.event_idempotency_key)
            # rows = session.execute(statement).all()
            for row in rows:
                # LOGGER.debug(f"row: {row}")
                keys.append(row[0])
        LOGGER.debug(f"number of cached ids: {len(keys)}")
        if len(keys) > 4:
            LOGGER.debug(f"sample keys: {keys[:3]}")
        else:
            LOGGER.debug(f"sample keys: {keys}")

        return keys

    def init_db(self):
        """if the database doesn't have the tables in it, then create them"""
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        LOGGER.debug(f"table names: {table_names}")

        # check to see if the expected table exists in the db.
        if db.model.Events.__tablename__ not in table_names:
            LOGGER.info("Creating the database tables")
            db.model.Base.metadata.create_all(bind=self.engine)
        else:
            LOGGER.info("db already there... table " + f"{db.model.Events.__tablename__} exists")

    def get_current_idempotency_key(self):
        """because the data is available daily, using the date stamp as the
        idempotency key.  This is going to return the current datetime string
        in the format used for idempotency keys.
        """
        cur_idem_key = self.current_idempotency_key
        if not cur_idem_key:
            cur_idem_key = datetime.datetime.now().strftime(util.config.default_datestring_format)
        return cur_idem_key

    def cache_event(self, msg, idem_key=None):
        """msg is the message that is recieved originally from the AMQP event.
        This method will store the message in the database and in memory.

        :param msg: _description_
        :type msg: _type_
        :param idem_key: _description_, defaults to None
        :type idem_key: _type_, optional
        """

        if idem_key is None:
            idem_key = self.current_idempotency_key

        # check if event has already been cached
        if (idem_key not in self.cached_events) or msg not in self.cached_events[idem_key]:

            event_record = db.model.Events(event_message=msg, event_idempotency_key=idem_key)

            with self.session_maker() as session:
                session.add(event_record)
                session.commit()
                # add to in memory struct
                if idem_key not in self.cached_events:
                    self.cached_events[idem_key] = []
                self.cached_events[idem_key].append(msg)
        else:
            LOGGER.debug(f"event {msg} with idem key: {idem_key} already cached")

    def is_event_of_interest(self, msg, idem_key=None):
        """
        is the event one that we are interested in, ie does it correspond
        with a piece of information that we are wanting to download
        """
        is_of_interest = False
        if idem_key is None:
            idem_key = self.current_idempotency_key

        if idem_key not in self.expected_data:
            # calculated the expected data list for the date in question
            self.expected_data[idem_key] = self.grib_config.calculate_expected_file_list(
                only_file_path=True, date_str=idem_key
            )

        # LOGGER.debug("input message: ")
        if msg in self.expected_data[idem_key]:
            is_of_interest = True
        return is_of_interest

    def is_all_data_there(self, idem_key=None):
        """
        returns a boolean value indicating if all the data we are attempting
        to download is available.
        """
        if idem_key is None:
            idem_key = self.current_idempotency_key

        if idem_key not in self.expected_data:
            self.expected_data[idem_key] = self.grib_config.calculate_expected_file_list(
                only_file_path=True, date_str=idem_key
            )

        all_there = True
        # first check the cached events, if the idem key not there then try to
        # load
        # if idem_key in self.cached_events:
        missing_files = []
        if idem_key not in self.cached_events:
            all_there = False
        for expected_file in self.expected_data[idem_key]:
            if all_there and expected_file not in self.cached_events[idem_key]:
                all_there = False
                missing_files.append(expected_file)
            missing_files = list(set(missing_files))
        LOGGER.info(f"number of missing files: {len(missing_files)}")
        if len(missing_files) < 5:
            LOGGER.info(f"missing files: {missing_files}")
        else:
            LOGGER.info(f"first 5 of {len(missing_files)} missing files: {missing_files[:5]}")

        # LOGGER.debug(f"missing files: {missing_files}")
        return all_there

    def get_missing(self):
        """if idem key is provided restricts results to just that idem key,
        otherwise will return a dict with all the idem keys and the missing
        data, as an associated list

        :param idem_key: a datestr in the format YYYYMMDD, defaults to None
        :type idem_key: str, optional
        """
        idem_keys = self.get_cached_id_keys()
        missing_files = {}
        for idem_key in idem_keys:
            if idem_key not in self.expected_data:
                self.expected_data[idem_key] = self.grib_config.calculate_expected_file_list(
                    only_file_path=True, date_str=idem_key
                )

            if idem_key not in self.cached_events:
                missing_files[idem_key] = self.expected_data[idem_key]
            else:
                for expected_file in self.expected_data[idem_key]:
                    if expected_file not in self.cached_events[idem_key]:
                        if idem_key not in missing_files:
                            missing_files[idem_key] = []
                        missing_files[idem_key].append(expected_file)
        missing_file_cnt = 0
        for idem_key in missing_files:
            missing_files[idem_key] = list(set(missing_files[idem_key]))
            missing_file_cnt = missing_file_cnt + len(missing_files[idem_key])
            if len(missing_files[idem_key]) < 5:
                LOGGER.info(f"missing files for {idem_key}: {missing_files[idem_key]}")
            else:
                LOGGER.info(
                    f"for {idem_key} first 5 of  {len(missing_files[idem_key])} missing files: {missing_files[idem_key][:5]}"
                )

        LOGGER.info(f"number of missing files: {missing_file_cnt}")
        return missing_files

    def clear_cache(self, idem_key=None):
        """when all the data we are expecting has been provided and passed on
        to the next process we will need to clear the cache.  That is what
        this method will do.
        """
        if idem_key is None:
            idem_key = self.current_idempotency_key

        # first get rid fo the database records
        with self.session_maker() as session:
            stmt = delete(db.model.Events).where(
                db.model.Events.event_idempotency_key.in_([idem_key])
            )
            LOGGER.debug(f"delete stmt: {stmt}")
            # stmt = delete(db.model.Events).all()
            session.execute(stmt)
            session.commit()
            LOGGER.info(f"cache has been cleared for idem_key: {idem_key}")

        # now get rid of the in memory struct
        if idem_key in self.cached_events:
            del self.cached_events[idem_key]

    def get_cached_events_as_struct(self):
        """
        queries the db for all the events then assembled a data structure like:
        struct:
            <idempotency_key> ... which is the date string when events are emitted
                event
                event
                event
                ...

        """
        LOGGER.debug("getting cached events")
        struct = {}
        events_result_set = self.get_cached_events()
        for event in events_result_set:
            if event.event_idempotency_key not in struct:
                struct[event.event_idempotency_key] = []
            struct[event.event_idempotency_key].append(event.event_message)
        LOGGER.debug(f"cached events: {len(struct)}")
        return struct

    def get_cached_events(self):
        """retrieves all the events from the database"""
        result_set = None
        with self.session_maker() as session:
            result_set = session.query(db.model.Events).all()
            LOGGER.debug(f"events retrieved from db: {len(result_set)}")
        return result_set

    def get_message_count(self):
        """returns the number of events that are in the database"""
        count = 0
        with self.session_maker() as session:
            count = session.query(db.model.Events).count()
            LOGGER.debug(f"message count: {count}")
        return count

    def has_stale(self):
        stale_keys = self.get_stale()
        return bool(stale_keys)

    def get_stale(self):
        LOGGER.debug("stale")
        stale_idem_keys = []
        idem_key = self.get_current_idempotency_key()
        current_key_time = datetime.datetime.strptime(
            idem_key, util.config.default_datestring_format
        )
        difference = datetime.timedelta(days=util.config.DAYS_TO_STALE)
        expirey_date = current_key_time - difference

        keys = self.get_cached_id_keys()
        for key in keys:
            key_time = datetime.datetime.strptime(key, util.config.default_datestring_format)
            if key_time < expirey_date:
                LOGGER.debug(f"key: {key} is stale")
                stale_idem_keys.append(key)
        return stale_idem_keys


    def flush_stale(self):
        """ Looks at the DAYS_TO_STALE parameter, uses that to identify stale
        records and then purges them from the database.
        """
        stale_keys = self.get_stale()
        for stale_key in stale_keys:
            LOGGER.debug(f"deleting records for {stale_key}")
            self.clear_cache(idem_key=stale_key)


