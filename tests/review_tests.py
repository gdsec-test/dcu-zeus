from unittest import TestCase

import mongomock
from dcdatabase.phishstorymongo import PhishstoryMongo

from settings import UnitTestConfig
from zeus.reviews.reviews import (BasicReview, FraudReview, HighValueReview,
                                  SucuriReview)


class TestReview(TestCase):
    HOLD_REASON = 'New Account'
    HOLD_TIME = 'Hold Time'
    KEY_FRAUD_HOLD_REASON = 'fraud_hold_reason'
    KEY_FRAUD_HOLD_UNTIL = 'fraud_hold_until'
    KEY_HOLD_REASON = 'hold_reason'
    KEY_HOLD_UNTIL = 'hold_until'
    SUCURI_HOLD_REASON = '72hr_notice_sent'
    HIGH_VALUE_HOLD_REASON = '72hr_notice_sent'

    def setUp(self):
        self._config = UnitTestConfig()
        self._db = PhishstoryMongo(self._config)
        # replace collection with mock
        self._db._mongo._collection = mongomock.MongoClient().db.collection
        self._db.add_new_incident(1236, dict(sourceDomainOrIp='lmn.com'))
        self._db.add_new_incident(1237, dict(sourceDomainOrIp='abc.com'))
        self._db.add_new_incident(1238, dict(sourceDomainOrIp='xyz.com'))
        self._db.add_new_incident(1239, dict(sourceDomainOrIp='123.com'))

        self._basic = BasicReview(self._config)
        self._basic._db = self._db  # Replace db with mock

        self._fraud = FraudReview(self._config)
        self._fraud._db = self._db  # Replace db with mock

        self._sucuri = SucuriReview(self._config)
        self._sucuri._db = self._db  # Replace db with mock

        self._high_value = HighValueReview(self._config)
        self._high_value._db = self._db  # Replace db with mock

    def test_basic_hold(self):
        doc = self._basic.place_in_review(1236, self.HOLD_TIME)
        self.assertIsNotNone(doc.get(self.KEY_HOLD_UNTIL))
        self.assertIsNone(doc.get(self.KEY_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)

    def test_basic_hold_with_reason(self):
        doc = self._basic.place_in_review(1236, self.HOLD_TIME, self.HOLD_REASON)
        self.assertIsNotNone(doc.get(self.KEY_HOLD_UNTIL))
        self.assertIsNotNone(doc.get(self.KEY_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)
        self.assertEqual(doc.get(self.KEY_HOLD_REASON), self.HOLD_REASON)

    def test_fraud_hold_with_reason(self):
        doc = self._fraud.place_in_review(1237, self.HOLD_TIME, self.HOLD_REASON)
        self.assertIsNotNone(doc.get(self.KEY_FRAUD_HOLD_UNTIL))
        self.assertIsNotNone(doc.get(self.KEY_FRAUD_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_FRAUD_HOLD_UNTIL), self.HOLD_TIME)
        self.assertEqual(doc.get(self.KEY_FRAUD_HOLD_REASON), self.HOLD_REASON)

    def test_fraud_hold(self):
        doc = self._fraud.place_in_review(1237, self.HOLD_TIME)
        self.assertIsNotNone(doc.get(self.KEY_FRAUD_HOLD_UNTIL))
        self.assertIsNone(doc.get(self.KEY_FRAUD_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_FRAUD_HOLD_UNTIL), self.HOLD_TIME)

    def test_sucuri_hold(self):
        doc = self._sucuri.place_in_review(1238, self.HOLD_TIME)
        self.assertIsNotNone(doc.get(self.KEY_HOLD_UNTIL))
        self.assertIsNone(doc.get(self.KEY_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)

    def test_sucuri_hold_with_reason(self):
        """
        Sucuri holds use the same 'hold_until' and 'hold_reason' fields
        """
        doc = self._sucuri.place_in_review(1238, self.HOLD_TIME, self.SUCURI_HOLD_REASON)
        self.assertIsNotNone(doc.get(self.KEY_HOLD_UNTIL))
        self.assertIsNotNone(doc.get(self.KEY_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)
        self.assertEqual(doc.get(self.KEY_HOLD_REASON), self.SUCURI_HOLD_REASON)

    def test_high_value_hold(self):
        doc = self._high_value.place_in_review(1239, self.HOLD_TIME)
        self.assertIsNotNone(doc.get(self.KEY_HOLD_UNTIL))
        self.assertIsNone(doc.get(self.KEY_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)

    def test_high_value_hold_with_reason(self):
        doc = self._sucuri.place_in_review(1239, self.HOLD_TIME, self.HIGH_VALUE_HOLD_REASON)
        self.assertIsNotNone(doc.get(self.KEY_HOLD_UNTIL))
        self.assertIsNotNone(doc.get(self.KEY_HOLD_REASON))
        self.assertEqual(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)
        self.assertEqual(doc.get(self.KEY_HOLD_REASON), self.HIGH_VALUE_HOLD_REASON)
