import abc
import os


class Mailer(object, metaclass=abc.ABCMeta):
    def __init__(self, app_settings):
        self.env = os.getenv('sysenv', 'dev')
        self.cert = app_settings.ZEUS_CLIENT_CERT
        self.key = app_settings.ZEUS_CLIENT_KEY

    def generate_kwargs_for_hermes(self):
        """
        This function helps generate common kwargs expected by the hermes library
        :return:
        """
        return {'env': self.env, 'cert': self.cert, 'key': self.key}
