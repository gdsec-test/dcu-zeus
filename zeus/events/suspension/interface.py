import abc


class Product(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def suspend(self, **kwargs):
        pass

    @abc.abstractmethod
    def reinstate(self, **kwargs):
        pass

    @abc.abstractmethod
    def cancel(self, **kwargs):
        pass

    @abc.abstractmethod
    def block_content(self, **kwargs):
        pass

    @abc.abstractmethod
    def unblock_content(self, **kwargs):
        pass

    @abc.abstractmethod
    def delete_content(self, **kwargs):
        pass
