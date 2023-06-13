from zeus.events.suspension.angelo import Angelo
from zeus.events.suspension.diablo import Diablo
from zeus.events.suspension.interface import Product
from zeus.events.suspension.mwp_one import MWPOne
from zeus.events.suspension.nes_helper import NESHelper
from zeus.events.suspension.vps4 import VPS4
from zeus.persist.notification_timeouts import Throttle
from zeus.utils.functions import (get_host_customer_id_from_dict,
                                  get_host_info_from_dict)
from zeus.utils.shopperapi import ShopperAPI


class ThrottledHostingService:
    def __init__(self, app_settings):
        self._decorated = HostingService(app_settings)
        self._throttle = Throttle(app_settings.REDIS, app_settings.SUSPEND_HOSTING_LOCK_TIME)

    def can_suspend_hosting_product(self, identifier):
        return self._throttle.can_suspend_hosting_product(identifier)

    def suspend_hosting(self, product, identifier, data, suspend_associated: bool = False):
        return self._decorated.suspend(product, identifier, data, suspend_associated)

    def reinstate_hosting(self, product, identifier, data):
        return self._decorated.reinstate(product, identifier, data)


class HostingService(Product):
    UNSUPPORTED_PRODUCT = "Unsupported Product: {}"
    UNSUPPORTED_OPERATION = "Unsupported Operation: {}"

    def __init__(self, app_settings):
        self.nes_helper = NESHelper(app_settings)
        self._products = {'diablo': Diablo(app_settings),
                          'mwp 1.0': MWPOne(app_settings),
                          'plesk': Angelo(app_settings),
                          'vps4': VPS4(app_settings),
                          'gocentral': self.nes_helper}
        self._shopper_api = ShopperAPI(app_settings)

    def suspend(self, product, identifier, data, suspend_associated: bool = False):
        product = product.lower() if product else ''
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)

        # Use the correct API
        # TODO CMAPT-5272: remove the if statement and other return statement and just use NES
        if self.nes_helper.get_use_nes(data):
            identifier = get_host_info_from_dict(data).get('entitlementId')
            customer_id = get_host_customer_id_from_dict(data)
            if not customer_id:
                host_shopper_id = get_host_info_from_dict(data).get('shopperId', '')
                customer_id = self._shopper_api.get_customer_id_from_shopper_id(host_shopper_id)
            result = self.nes_helper.suspend(identifier, customer_id)

            # Custom handling for W+M products.
            if result and suspend_associated and product == 'gocentral':
                entitlements = self.nes_helper.get_entitlements_from_subscriptions(customer_id, 'websiteBuilder', 'websitesAndMarketing')
                for e in entitlements:
                    self.nes_helper.suspend(e, customer_id)
            return result

        return self._products.get(product).suspend(guid=identifier, data=data)

    def reinstate(self, product, identifier, data):
        product = product.lower() if product else ''
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)

        # Use the correct API
        # TODO CMAPT-5272: remove the if statement and other return statement and just use NES
        if self.nes_helper.get_use_nes(data):
            customer_id = get_host_customer_id_from_dict(data)
            return self.nes_helper.reinstate(identifier, customer_id)

        return f'Cannot support reinstate.  {product} product is not NES supported.'

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
