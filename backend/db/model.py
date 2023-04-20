import sqlalchemy.orm
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.sql import func

# leaving this line in here in case eventually pivot to postgres
# from sqlalchemy.dialects.postgresql import TIMESTAMP

Base = sqlalchemy.orm.declarative_base()


class Events(Base):
    """defines the Event table in the database.  Events need to be cached in
    order for a pod to recover from a crash and not lose any events.

    Events get emitted per new data set.  We need to collect these events and
    then when all the events for a give dataset have been emitted trigger a
    action somewhere else.

    :param Base: Event table is used to keep track of events that have been
        emitted and recieved and acknowledged by the subscriber, but that
        haven't resulted in a downstream action yet.


    """
    __tablename__ = "message_events"
    __table_args__ = (PrimaryKeyConstraint("event_id", name="event_pk"),)

    event_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    event_message = Column(String(200), nullable=False)
    event_timestmp = Column(DateTime(timezone=True), server_default=func.now())
    event_idempotency_key = Column(String(50), nullable=False)