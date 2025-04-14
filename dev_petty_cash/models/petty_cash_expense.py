# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class petty_cash_expense(models.Model):
    _name = 'petty.cash.expense'
    _description = 'Petty Cash expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    
    @api.model
    def _get_request_by(self):
        employee_id =self.env['hr.employee'].search([('user_id','=',self.env.user.id)])
        return employee_id.id or False
    
    name = fields.Char('Name', default='/', tracking=1)
    employee_id = fields.Many2one('hr.employee', string='Employee', default=_get_request_by, tracking=2)
    petty_journal_id = fields.Many2one('account.journal',  string='From (Petty Cash Journal)', tracking=2)
    payment_journal_id = fields.Many2one('account.journal', string='To (Payment Journal)')
    date = fields.Date('Date', copy=False, default=fields.Datetime.now)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self:self.env.company.currency_id)
    user_id = fields.Many2one('res.users', string='User', default=lambda self:self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self:self.env.company)
    state = fields.Selection(string='State', selection=[('draft', 'Draft'),
                                                        ('confirm', 'Confirm'),
                                                        ('payment', 'Process Payment'),
                                                        ('done', 'Done'),
                                                        ('cancel','Cancel')], default='draft', tracking=4)
    expense_lines = fields.One2many('petty.expense.lines','expense_id', string='Expense Lines')
    payment_ids = fields.Many2many('account.payment', string='Payments', copy=False)
    balance = fields.Monetary('Balance', compute='_get_balance')
    expense_amount = fields.Monetary('Expense Amount', compute='_get_expense_amount', tracking=3)
    request_ids = fields.Many2many('petty.cash.request', string='Requests')
    remaining_balace = fields.Monetary('Reaming Amount', compute='_get_expense_amount')
    note = fields.Text('Notes')
    payment_count = fields.Integer('Payment Count', compute='_count_payment')
    
    def action_view_payment(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        action['context']={}
        action['domain'] = [('id','in',self.payment_ids.ids)]
        return action
    
    @api.depends('payment_ids')
    def _count_payment(self):
        for expense in self:
            expense.payment_count = len(expense.payment_ids)
            
    @api.depends('expense_lines')
    def _get_expense_amount(self):
        for expense in self:
            amount = 0
            for line in expense.expense_lines:
                amount += line.amount
            expense.expense_amount = amount
            expense.remaining_balace = expense.balance - expense.expense_amount 
            
                    
    
    @api.depends('employee_id','petty_journal_id','currency_id')
    def _get_balance(self):
        for expense in self:
            request_ids = expense.env['petty.cash.request'].search([('request_by','=',expense.employee_id.id),
                                                                 ('petty_journal_id','=',expense.petty_journal_id.id),
                                                                 ('state','=','approve'),
                                                                 ('request_amount','>',0)])
            amount = 0
            for request in request_ids:
                if request.request_amount and request.request_amount > 0:
                    if request.currency_id.id != expense.currency_id.id:
                        currency_id = request.currency_id.with_context(date=request.date)
                        amount  += currency_id.compute(abs(request.request_amount), expense.currency_id)
                    else:
                        amount += abs(request.request_amount)
            expense.balance = amount
        
    
    def create_payment(self):
        payment_method_id = self.env['account.payment.method'].search([('name', '=', 'Manual')], limit=1)
        if not payment_method_id:
            payment_method_id = self.env['account.payment.method'].search([], limit=1)
        vals = {
            'payment_type': 'outbound',
            'is_internal_transfer': True,
            'company_id': self.company_id and self.company_id.id or False,
            'amount': self.expense_amount or 0.0,
            'currency_id': self.currency_id and self.currency_id.id or False,
            'journal_id': self.petty_journal_id and self.petty_journal_id.id or False,
            'destination_journal_id': self.payment_journal_id and self.payment_journal_id.id or False,
            'payment_method_line_id': payment_method_id and payment_method_id.id or False,
        }
        payment_id = self.env['account.payment'].sudo().create(vals)
        payment_id.action_post()
        self.payment_ids = [(6, 0, [payment_id.id])]

    def reconcile_payment(self):
        request_ids = self.env['petty.cash.request'].search([('request_by','=',self.employee_id.id),
                                                                 ('petty_journal_id','=',self.petty_journal_id.id),
                                                                 ('state','=','approve'),
                                                                 ('balance','>',0)])
        credit_move_lines = self.env['account.move.line']
        debit_move_lines = self.env['account.move.line']
        account_id = self.petty_journal_id.default_account_id
        for request in request_ids:
            if request.payment_id and request.payment_id.move_id:
                credit_line = request.payment_id.move_id.line_ids.filtered(lambda t: t.account_id.id == account_id.id)
                credit_res_amount = abs(credit_line.amount_residual_currency)
                if credit_res_amount:
                    credit_move_lines += credit_line
        for payment in self.payment_ids:
            if payment.move_id:
                d_line = payment.move_id.line_ids.filtered(lambda t: t.account_id.id == account_id.id)
                res_amount = abs(d_line.amount_residual_currency)
                if res_amount:
                    debit_move_lines += d_line
        
        if debit_move_lines and credit_move_lines:
            (credit_move_lines + debit_move_lines).reconcile()
        return True
                
            
                                                                 
        
    
    def action_cofirm(self):
        if self.balance <= self.expense_amount:
            raise ValidationError(_("In Petty Cash have only %s balance")%(self.balance))
        self.state = 'confirm'
        
    def action_create_payment(self):
        self.create_payment()
        self.state = 'payment'
        
    def action_reconcile(self):
        self.reconcile_payment()
        self.state = 'done'
        
    def action_cancel(self):
        self.state = 'cancel'
        
    def action_draft(self):
        self.state = 'draft'
        
    def unlink(self):
        for request in self:
            if request.state != 'draft':
                raise ValidationError(_("You can delete expense in draft state only."))
        return super(petty_cash_expense, self).unlink()
        
    @api.model
    def create(self, vals):
        vals.update({
            'name': self.env['ir.sequence'].next_by_code('petty.cash.expense') or '/',
			
        })
        return super(petty_cash_expense, self).create(vals)
        

class petty_expense_lines(models.Model):
    _name ='petty.expense.lines'
    _description = 'Petty Expense Lines'
    
    product_id = fields.Many2one('product.product', string='Particulars')
    account_id = fields.Many2one('account.account', string='Account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency', string='Currency')
    expense_id = fields.Many2one('petty.cash.expense', string='Expense', ondelete='cascade')
    
    
    @api.onchange('product_id')
    def onchange_product(self):
        self.ensure_one()
        self = self.with_company(self.expense_id.company_id)
        if self.product_id:
            accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=False)
            account_id = accounts['expense'] or False
            self.account_id = account_id and account_id.id or False
            self.amount = self.product_id.standard_price or 0.0
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
