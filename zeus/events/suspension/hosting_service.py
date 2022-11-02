from zeus.events.suspension.angelo import Angelo
from zeus.events.suspension.diablo import Diablo
from zeus.events.suspension.gocentral import GoCentral
from zeus.events.suspension.interface import Product
from zeus.events.suspension.mwp_one import MWPOne
from zeus.events.suspension.vertigo import Vertigo
from zeus.events.suspension.vps4 import VPS4
from zeus.persist.notification_timeouts import Throttle
from zeus.events.suspension.nes_helper import NESHelper
from zeus.utils.functions import get_host_customer_id_from_dict


class ThrottledHostingService:
    def __init__(self, app_settings):
        self._decorated = HostingService(app_settings)
        self._throttle = Throttle(app_settings.REDIS, app_settings.SUSPEND_HOSTING_LOCK_TIME)

    def can_suspend_hosting_product(self, identifier):
        return self._throttle.can_suspend_hosting_product(identifier)

    def suspend_hosting(self, product, identifier, data):
        return self._decorated.suspend(product, identifier, data)

    def can_reinstate_hosting_product(self, identifier):
        return self._throttle.can_reinstate_hosting_product(identifier)

    def reinstate_hosting(self, product, identifier, data):
        return self._decorated.reinstate(product, identifier, data)


class HostingService(Product):
    UNSUPPORTED_PRODUCT = "Unsupported Product: {}"
    UNSUPPORTED_OPERATION = "Unsupported Operation: {}"

    def __init__(self, app_settings):
        self._products = {'diablo': Diablo(app_settings),
                          'vertigo': Vertigo(app_settings),
                          'mwp 1.0': MWPOne(app_settings),
                          'plesk': Angelo(app_settings),
                          'vps4': VPS4(app_settings),
                          'gocentral': GoCentral(app_settings)}
        self.nes_helper = NESHelper(app_settings)

    def suspend(self, product, identifier, data):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)

        # Use the correct API
        # TODO CMAPT-5272: remove the if statement and other return statement and just use NES
        if self.PRODUCTS_USE_NES_FLAG.get(product, 'False') == 'True' or self.ALL_USE_NES_FLAG == 'True':
            customer_id = get_host_customer_id_from_dict(data)
            return self.nes_helper.suspend(identifier, customer_id)

        return self._products.get(product).suspend(guid=identifier, data=data)

    def reinstate(self, product, identifier, data):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)

        # Use the correct API
        # TODO CMAPT-5272: remove the if statement and other return statement and just use NES
        if self.nes_helper.get_use_nes():
            customer_id = get_host_customer_id_from_dict(data)
            return self.nes_helper.reinstate(identifier, customer_id)

        return self._products.get(product).reinstate(guid=identifier, data=data)

    # TODO CMAPT-5272: remove the rest of these functions.  They were never used
    def cancel(self, product, identifier):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('cancel')

    def block_content(self, product, identifier):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('block_content')

    def unblock_content(self, product, identifier):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('unblock_content')

    def delete_content(self, product, identifier):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('delete_content')
