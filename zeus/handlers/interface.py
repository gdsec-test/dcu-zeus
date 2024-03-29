import abc
from datetime import datetime


class Handler(object, metaclass=abc.ABCMeta):
    EPOCH = datetime(1970, 1, 1)

    @abc.abstractmethod
    def customer_warning(self, data):
        pass

    @abc.abstractmethod
    def intentionally_malicious(self, data):
        pass

    @abc.abstractmethod
    def repeat_offender(self, data):
        pass

    @abc.abstractmethod
    def shopper_compromise(self, data):
        pass

    @abc.abstractmethod
    def suspend(self, data):
        pass
