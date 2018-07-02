import logging

from zeus.events.suspension.interface import Product


class Angelo(Product):
    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)

    def suspend(self): pass

    def reinstate(self): pass

    def cancel(self): pass

    def block_content(self): pass

    def unblock_content(self): pass

    def delete_content(self): pass
