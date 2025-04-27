import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules, set_user


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Activate modules
        activate_modules('purchase_invoice_grouping')

        # Create company
        _ = create_company()
        company = get_company()

        # Create purchase user
        User = Model.get('res.user')
        Group = Model.get('res.group')
        purchase_user = User()
        purchase_user.name = 'Purchase'
        purchase_user.login = 'purchase'
        purchase_group, = Group.find([('name', '=', 'Purchase')])
        purchase_user.groups.append(purchase_group)
        stock_group, = Group.find([('name', '=', 'Stock')])
        purchase_user.groups.append(stock_group)
        purchase_user.save()

        # Create account user
        account_user = User()
        account_user.name = 'Account'
        account_user.login = 'account'
        account_group, = Group.find([('name', '=', 'Accounting')])
        account_user.groups.append(account_group)
        account_user.save()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()
        customer_grouped = Party(name='Customer Grouped',
                                 purchase_invoice_grouping_method='standard')
        customer_grouped.save()
        customer_ship_grouped = Party(
            name='Customer Ship Grouped',
            purchase_invoice_grouping_method='standard')
        customer_ship_grouped.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.purchasable = True
        template.list_price = Decimal('10')
        template.account_category = account_category
        template.save()
        product, = template.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # purchase some products
        set_user(purchase_user)
        Purchase = Model.get('purchase.purchase')
        purchase = Purchase()
        purchase.party = customer
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.unit_price = Decimal('5.0000')
        purchase_line.quantity = 2.0
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')

        # Make another purchase
        purchase, = Purchase.duplicate([purchase])
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')

        # Check the invoices
        set_user(account_user)
        Invoice = Model.get('account.invoice')
        invoices = Invoice.find([('party', '=', customer.id)])
        self.assertEqual(len(invoices), 2)
        invoice = invoices[0]
        self.assertEqual(invoice.type, 'in')

        # Now we'll use the same scenario with the grouped customer
        set_user(purchase_user)
        purchase = Purchase()
        purchase.party = customer_grouped
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 1.0
        purchase_line.unit_price = Decimal('5.0000')
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')

        # Make another purchase
        purchase = Purchase()
        purchase.party = customer_grouped
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 2.0
        purchase_line.unit_price = Decimal('5.0000')
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')

        # Check the invoices
        set_user(account_user)
        invoices = Invoice.find([
            ('party', '=', customer_grouped.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 1)
        invoice, = invoices
        self.assertEqual(len(invoice.lines), 2)
        self.assertEqual(invoice.lines[0].quantity, 1.0)
        self.assertEqual(invoice.lines[1].quantity, 2.0)

        # Create a manual invoice
        manual_invoice = Invoice()
        manual_invoice.party = customer_grouped
        manual_invoice.payment_term = payment_term
        manual_invoice.save()

        # Check that a new Purchase won't be grouped with the manual invoice
        set_user(purchase_user)
        purchase = Purchase()
        purchase.party = customer_grouped
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 3.0
        purchase_line.unit_price = Decimal('5.0000')
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')

        # Check the invoices
        set_user(account_user)
        invoices = Invoice.find([
            ('party', '=', customer_grouped.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 2)

        # Now we'll use the same scenario with the grouped customer but shipment method
        set_user(purchase_user)
        purchase = Purchase()
        purchase.party = customer_ship_grouped
        purchase.payment_term = payment_term
        purchase.invoice_method = 'shipment'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 1.0
        purchase_line.unit_price = Decimal('5.0000')
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')

        # Check no invoices are created
        set_user(account_user)
        invoices = Invoice.find([
            ('party', '=', customer_ship_grouped.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 0)
        set_user(purchase_user)

        # Validate Shipments
        Move = Model.get('stock.move')
        ShipmentIn = Model.get('stock.shipment.in')
        shipment = ShipmentIn()
        shipment.supplier = customer_ship_grouped

        for move in purchase.moves:
            incoming_move = Move(id=move.id)
            shipment.incoming_moves.append(incoming_move)

        shipment.save()
        self.assertEqual(shipment.origins, purchase.rec_name)
        shipment.click('receive')
        shipment.click('do')
        purchase.reload()
        self.assertEqual(purchase.shipment_state, 'received')
        self.assertEqual(len(purchase.shipments), 1)

        self.assertEqual(len(purchase.shipment_returns), 0)

        # Check one Invoice are created
        set_user(account_user)
        invoices = Invoice.find([
            ('party', '=', customer_ship_grouped.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 1)
        set_user(purchase_user)

        # Make another purchase
        purchase = Purchase()
        purchase.party = customer_ship_grouped
        purchase.payment_term = payment_term
        purchase.invoice_method = 'shipment'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 2.0
        purchase_line.unit_price = Decimal('5.0000')
        purchase.click('quote')
        purchase.click('confirm')
        self.assertEqual(purchase.state, 'processing')

        # Validate Shipments
        Move = Model.get('stock.move')
        ShipmentIn = Model.get('stock.shipment.in')
        shipment = ShipmentIn()
        shipment.supplier = customer_ship_grouped

        for move in purchase.moves:
            incoming_move = Move(id=move.id)
            shipment.incoming_moves.append(incoming_move)

        shipment.save()
        self.assertEqual(shipment.origins, purchase.rec_name)
        shipment.click('receive')
        shipment.click('do')
        purchase.reload()
        self.assertEqual(purchase.shipment_state, 'received')
        self.assertEqual(len(purchase.shipments), 1)

        self.assertEqual(len(purchase.shipment_returns), 0)

        # Check still one Invoice are created
        set_user(account_user)
        invoices = Invoice.find([
            ('party', '=', customer_ship_grouped.id),
            ('state', '=', 'draft'),
        ])
        self.assertEqual(len(invoices), 1)
        set_user(purchase_user)
