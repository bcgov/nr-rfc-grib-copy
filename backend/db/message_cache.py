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

from sqlalchemy import create_engine


class MessageCache:
    def __init__(self):
        # db file location should come from an env var, different depending
        # on local vs deployed
        self.db = create_engine("sqlite://", echo=True)
        pass

    def cache_event(self, msg):
        pass

    def is_event_of_intestest(self, msg):
        """
        is the event one that we are interested in, ie does it correspond
        with a piece of information that we are wanting to download
        """
        pass

    def is_all_data_there(self):
        """
        returns a boolean value indicating if all the data we are attempting
        to download is available.
        """
        pass

    def get(self):
        """returns a cache of all the data that currently exists in our
        cache of events.
        """
        pass

    def clear_cache(self):
        """when all the data we are expecting has been provided and passed on
        to the next process we will need to clear the cache.  That is what
        this method will do.
        """
        pass
