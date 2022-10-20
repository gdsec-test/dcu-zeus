from zeus.events.suspension.nes_helper import NESHelper
from zeus.persist.notification_timeouts import Throttle


class ThrottledHostingService:
    def __init__(self, app_settings):
        self._decorated = HostingService(app_settings)
        self._throttle = Throttle(app_settings.REDIS, app_settings.SUSPEND_HOSTING_LOCK_TIME)

    def can_suspend_hosting_product(self, identifier):
        return self._throttle.can_suspend_hosting_product(identifier)

    def suspend_hosting(self, product, identifier, customer_id, reason):
        return self._decorated.suspend(product, identifier, customer_id, reason)


class HostingService():
    UNSUPPORTED_PRODUCT = "Unsupported Product: {}"
    UNSUPPORTED_OPERATION = "Unsupported Operation: {}"

    def __init__(self, app_settings):
        self._products = ['diablo', 'vertigo', 'mwp 1.0', 'plesk', 'vps4', 'gocentral']
        self.nes_helper = NESHelper(app_settings)

    def suspend(self, product, identifier, customer_id, reason):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)

        return self.nes_helper.suspend(identifier, customer_id, reason)

    # TODO: LKM - figure out if we need to implement this or not.  If we do, we will probably want to add a 
    # 'reinstate_hosting' function in the Throttle above as well as a "can_reinstate_hosting_product" func
    def reinstate(self, product, identifier, data):
        product = product.lower() if product else None
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)

        return self._products.get(product).reinstate(guid=identifier, data=data)

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
