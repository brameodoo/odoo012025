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


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    emp_seq = fields.Char("Employee Sequence", required=True, readonly=True, copy=False, default='/')

    # Sobrescribir método para excluir 'emp_seq' de campos privados
    def _get_private_fields(self):
        private_fields = super()._get_private_fields()
        # Excluir 'emp_seq' de la lista de campos privados
        if 'emp_seq' in private_fields:
            private_fields.remove('emp_seq')
        return private_fields
   
    
    @api.model
    def create(self, vals):
        if vals.get('emp_seq',  '/') == '/':
            vals['emp_seq'] = self.env['ir.sequence'].next_by_code(
                'hr.employee') or '/'
        return super(hr_employee, self).create(vals)
        
        
    def copy(self, default=None):
        if default is None:
            default = {}
        default['emp_seq'] = '/'
        return super(hr_employee, self).copy(default=default)
        
        
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
