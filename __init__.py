# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool

from . import configuration, party, purchase

def register():
    Pool.register(
        purchase.Purchase,
        party.Party,
        party.PartyPurchaseInvoiceGroupingMethod,
        configuration.Configuration,
        configuration.ConfigurationPurchaseMethod,
        module='purchase_invoice_grouping', type_='model')
