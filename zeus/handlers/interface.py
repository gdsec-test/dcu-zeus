import abc


class Handler(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def customer_warning(self, data):
        pass

    @abc.abstractmethod
    def intentionally_malicious(self, data):
        pass

    @abc.abstractmethod
    def suspend(self, data):
        pass
