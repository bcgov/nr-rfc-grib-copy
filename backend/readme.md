# Message Listener / Subscriber

Code related to listening / subscribing to the AMQP server for events and then
implementing actions based on those events

At a high level the code will listen to events, coallate them until all the data
we want has been emitted, then trigger a job that downloads the data and
processes it.