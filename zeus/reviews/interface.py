import abc

from dcdatabase.phishstorymongo import PhishstoryMongo


class Review(object, metaclass=abc.ABCMeta):
    def __init__(self, settings):
        self._db = PhishstoryMongo(settings)

    @abc.abstractmethod
    def place_in_review(self, ticket, hold_time, reason=None):
        """
        Places a ticket in review until the hold_time
        :param ticket:
        :param hold_time:
        :param reason:

        :return:
        """

    def _review_until(self, _ticket, _field, _date, _reason_field, _reason):
        """
        Place the specified ticket on hold until the specified date, using the given field
        :param _ticket:
        :param _field:
        :param _date:
        :param _reason_field:
        :param _reason:
        :return:
        """
        data = {_field: _date}
        if _reason:
            data[_reason_field] = _reason
        return self._db.update_incident(_ticket, data)
