import logging


def generate_event(ticket, reason, **kwargs):
    """
    Logs an event for the given reason. Any key/value pairs defined in kwargs will be added to the
    log before being added to the database
    :param ticket:
    :param reason:
    :param kwargs:
    :return:
    """
    data = dict(ticket=ticket)
    if kwargs:
        data.update(kwargs)
    logging.getLogger(__name__).uevent(reason, extra=data)
