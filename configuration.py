# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta

purchase_invoice_grouping_method = fields.Selection(
    'get_purchase_invoice_grouping_methods', "purchase Invoice Grouping Method",
    help="The default invoice grouping method for new customers.")


@classmethod
def get_purchase_invoice_grouping_methods(cls):
    pool = Pool()
    Party = pool.get('party.party')
    field_name = 'purchase_invoice_grouping_method'
    return Party.fields_get([field_name])[field_name]['selection']


class Configuration(metaclass=PoolMeta):
    __name__ = 'purchase.configuration'

    purchase_invoice_grouping_method = fields.MultiValue(
        purchase_invoice_grouping_method)
    get_purchase_invoice_grouping_methods = get_purchase_invoice_grouping_methods

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'purchase_invoice_grouping_method':
            return pool.get('purchase.configuration.purchase_method')
        return super(Configuration, cls).multivalue_model(field)


class ConfigurationPurchaseMethod(metaclass=PoolMeta):
    __name__ = 'purchase.configuration.purchase_method'

    purchase_invoice_grouping_method = purchase_invoice_grouping_method
    get_purchase_invoice_grouping_methods = get_purchase_invoice_grouping_methods

