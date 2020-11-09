import logging

from zeus.reviews.interface import Review


class BasicReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(BasicReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time, reason=None):
        self._logger.info("Placing {} in review until {} for {}".format(ticket, hold_time, reason))
        return self._review_until(ticket, 'hold_until', hold_time, 'hold_reason', reason)


class SucuriReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(SucuriReview, self).__init__(settings)

    def place_in_review(self, ticket, sucuri_hold_time, reason=None):
        self._logger.info("Placing {} in Sucuri review until {} for {}".format(ticket, sucuri_hold_time, reason))
        return self._review_until(ticket, 'sucuri_hold_until', sucuri_hold_time, 'sucuri_hold_reason', reason)


class FraudReview(Review):
    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        super(FraudReview, self).__init__(settings)

    def place_in_review(self, ticket, hold_time, reason=None):
        self._logger.info("Placing {} in fraud review until {} for {}".format(ticket, hold_time, reason))
        return self._review_until(ticket, 'fraud_hold_until', hold_time, 'fraud_hold_reason', reason)
