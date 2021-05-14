import logging

from zeus.reviews.interface import Review


class BasicReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger('celery.tasks')
        super(BasicReview, self).__init__(settings)

    def place_in_review(self, _ticket, _hold_time, _reason=None):
        self._logger.info("Placing {} in review until {} for {}".format(_ticket, _hold_time, _reason))
        return self._review_until(_ticket, 'hold_until', _hold_time, 'hold_reason', _reason)


class SucuriReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger('celery.tasks')
        super(SucuriReview, self).__init__(settings)

    def place_in_review(self, _ticket, _hold_time, _reason=None):
        """
        In order to avoid having another condition in each of the phishstory report bootcards,
         the field used will be "hold_until", which the current bootcard conditions check for
        """
        self._logger.info("Placing {} in Sucuri review until {} for {}".format(_ticket, _hold_time, _reason))
        return self._review_until(_ticket, 'hold_until', _hold_time, 'hold_reason', _reason)


class FraudReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger('celery.tasks')
        super(FraudReview, self).__init__(settings)

    def place_in_review(self, _ticket, _hold_time, _reason=None):
        self._logger.info("Placing {} in fraud review until {} for {}".format(_ticket, _hold_time, _reason))
        return self._review_until(_ticket, 'fraud_hold_until', _hold_time, 'fraud_hold_reason', _reason)
