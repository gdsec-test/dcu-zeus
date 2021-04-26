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
    logger = logging.getLogger(__name__)

    data = dict(ticket=ticket)

    if kwargs:
        data.update(kwargs)

    try:
        logger.uevent(reason, extra=data)
    except Exception as e:
        logger.error('Unable to log event for ticket {} & reason {}: {}'.format(ticket, reason, e.message))
