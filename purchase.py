# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from itertools import groupby

from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction


class Purchase(metaclass=PoolMeta):
    __name__ = 'purchase.purchase'

    @property
    def invoice_grouping_method(self):
        party = self.invoice_party or self.party
        return party.purchase_invoice_grouping_method

    @property
    def _invoice_grouping_fields(self):
        return ('state', 'company', 'type', 'journal', 'party',
            'invoice_address', 'currency', 'account', 'payment_term')

    def _get_grouped_invoice_order(self):
        "Returns the order clause used to find invoice that should be grouped"
        return None

    def _get_grouped_invoice_domain(self, invoice):
        "Returns a domain that will find invoices that should be grouped"
        Invoice = invoice.__class__
        invoice_domain = [
            ('lines.origin', 'like', 'purchase.line,%'),
            ]
        if invoice and invoice.party and invoice.party.group_by_warehouse:
            invoice_domain.append(('purchases.warehouse', '=',
                self.warehouse.id))

        defaults = Invoice.default_get(self._invoice_grouping_fields,
            with_rec_name=False)
        for field in self._invoice_grouping_fields:
            # Avoid payment_type field to control payable/receivable kind
            # depend untaxed amount
            if field == 'payment_type':
                continue
            invoice_domain.append(
                (field, '=', getattr(invoice, field, defaults.get(field)))
                )
        return invoice_domain

    def _get_invoice(self):
        pool = Pool()
        Configuration = pool.get('purchase.configuration')
        config = Configuration(1)
        transaction = Transaction()
        context = transaction.context
        invoice = super()._get_invoice()
        if (not context.get('skip_grouping', False)
                and self.invoice_grouping_method):
            with transaction.set_context(skip_grouping=True):
                invoice = self._get_invoice()
            Invoice = invoice.__class__
            domain = self._get_grouped_invoice_domain(invoice)
            order = self._get_grouped_invoice_order()
            grouped_invoices = Invoice.search(domain, order=order, limit=1)
            if grouped_invoices:
                invoice, = grouped_invoices

        if config.default_in_journal:
            invoice.journal = config.default_in_journal
        return invoice

    @classmethod
    def _process_invoice(cls, purchases):
        for method, purchases in groupby(
                purchases, lambda s: s.invoice_grouping_method):
            if method:
                for purchase in purchases:
                    super()._process_invoice([purchase])
            else:
                super()._process_invoice(list(purchases))
