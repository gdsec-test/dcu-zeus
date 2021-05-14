import logging

from zeus.events.suspension.interface import Product


class Legacy(Product):
    def __init__(self):
        self._logger = logging.getLogger('celery.tasks')

    def suspend(self):
        pass

    def reinstate(self):
        pass

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
