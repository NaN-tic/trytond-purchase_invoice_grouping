# This file is part of Tryton.  The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.
from trytond import backend
from trytond.model import ModelSQL, ValueMixin, fields
from trytond.pool import Pool, PoolMeta
from trytond.tools.multivalue import migrate_property


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    purchase_invoice_grouping_method = fields.MultiValue(fields.Selection([
                (None, 'None'),
                ('standard', 'Standard'),
                ],
            'Purchase Invoice Grouping Method'))
    purchase_invoice_grouping_methods = fields.One2Many(
        'party.party.purchase_invoice_grouping_method', 'party',
        "Purchased Invoice Grouping Methods")

    @classmethod
    def default_purchase_invoice_grouping_method(cls, **pattern):
        pool = Pool()
        Configuration = pool.get('purchase.configuration')
        return Configuration(1).get_multivalue(
            'purchase_invoice_grouping_method', **pattern)


class PartyPurchaseInvoiceGroupingMethod(ModelSQL, ValueMixin):
    "Party Sale Invoice Grouping Method"
    __name__ = 'party.party.purchase_invoice_grouping_method'
    party = fields.Many2One(
        'party.party', "Party", ondelete='CASCADE', select=True)
    purchase_invoice_grouping_method = fields.Selection(
        'get_purchase_invoice_grouping_methods', "Purchase Invoice Grouping Method")


    @classmethod
    def get_purchase_invoice_grouping_methods(cls):
        pool = Pool()
        Party = pool.get('party.party')
        field_name = 'purchase_invoice_grouping_method'
        return Party.fields_get([field_name])[field_name]['selection']
