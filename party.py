# This file is part of Tryton.  The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta
from trytond.modules.company.model import CompanyValueMixin


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
    group_by_warehouse = fields.MultiValue(fields.Boolean('Group by Warehouse'))
    group_by_warehouses = fields.One2Many(
        'party.party.purchase_invoice_grouping_method', 'party',
        "Purchased Invoice Group by Warehouse")

    @classmethod
    def default_purchase_invoice_grouping_method(cls, **pattern):
        pool = Pool()
        Configuration = pool.get('purchase.configuration')
        return Configuration(1).get_multivalue(
            'purchase_invoice_grouping_method', **pattern)

    @classmethod
    def default_group_by_warehouse(cls, **pattern):
        return True

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'group_by_warehouse':
            return pool.get('party.party.purchase_invoice_grouping_method')

        return super().multivalue_model(field)



class PartyPurchaseInvoiceGroupingMethod(ModelSQL, CompanyValueMixin):
    "Party Sale Invoice Grouping Method"
    __name__ = 'party.party.purchase_invoice_grouping_method'
    party = fields.Many2One(
        'party.party', "Party", ondelete='CASCADE',
        context={
            'company': Eval('company', -1),
            },
        depends={'company'})
    purchase_invoice_grouping_method = fields.Selection(
        'get_purchase_invoice_grouping_methods', "Purchase Invoice Grouping Method")
    group_by_warehouse = fields.Boolean('Group by Warehouse')

    @classmethod
    def get_purchase_invoice_grouping_methods(cls):
        pool = Pool()
        Party = pool.get('party.party')
        field_name = 'purchase_invoice_grouping_method'
        return Party.fields_get([field_name])[field_name]['selection']
