from zeus.events.suspension.angelo import Angelo
from zeus.events.suspension.diablo import Diablo
from zeus.events.suspension.interface import Product
from zeus.events.suspension.legacy import Legacy
from zeus.events.suspension.mwp_one import MWPOne
from zeus.events.suspension.vertigo import Vertigo


class Suspension(Product):
    UNSUPPORTED_PRODUCT = 'Unsupported Product {}'
    UNSUPPORTED_OPERATION = 'Unsupported Operation {}'

    def __init__(self, app_settings):
        self._products = {'diablo': Diablo(app_settings),
                          'wpaas': MWPOne(app_settings),
                          'angelo': Angelo(app_settings),
                          'vertigo': Vertigo(app_settings),
                          'legacy': Legacy(app_settings)}

    def suspend(self, product, identifier, data):
        product = product.lower()
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        self._products[product].suspend(identifier, data)

    def reinstate(self, product, identifier, data):
        product = product.lower()
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        self._products[product].reinstate(identifier, data)

    def cancel(self, product, identifier):
        product = product.lower()
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('cancel')

    def block_content(self, product, identifier):
        product = product.lower()
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('block_content')

    def unblock_content(self, product, identifier):
        product = product.lower()
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('unblock_content')

    def delete_content(self, product, identifier):
        product = product.lower()
        if product not in self._products:
            return self.UNSUPPORTED_PRODUCT.format(product)
        return self.UNSUPPORTED_OPERATION.format('delete_content')
