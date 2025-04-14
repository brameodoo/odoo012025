# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class WorkshopRequest(models.Model):
    """ Model for workshop request """
    _name = 'workshop.request'
    _description = "Workshop Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    def _default_employee_id(self):
        return self.env.user.employee_id

    name = fields.Char(string='Request Ref', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Requested By',
                                   default=_default_employee_id, required=True,
                                   help="Employee who requested the service")
    department_id = fields.Many2one('hr.department', string='Department',
                                    related='employee_id.department_id', readonly=True,
                                    help="Department of the employee")
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle', required=True,
                                 domain="[('driver_id', '=', employee_id)]",
                                 help="Vehicle for which the service is requested")
    request_date = fields.Date(string='Request Date', default=date.today(),
                               required=True, help="Date of the request")
    description = fields.Text(string='Description', required=True,
                              help="Detailed description of the request")
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High')
    ], default='0', string='Priority', help="Priority of the request")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True,
        help="Status of the workshop request")
    approver_id = fields.Many2one('res.users', string='Approver',
                                  help="User who approved the request")
    approval_date = fields.Date(string='Approval Date', readonly=True,
                                 help="Date when the request was approved")
    workshop_id = fields.Many2one('car.workshop', string='Workshop Order',
                                 readonly=True, copy=False,
                                 help="Related workshop order")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('workshop.request') or _('New')
        res = super(WorkshopRequest, self).create(vals)
        return res

    def action_submit(self):
        self.state = 'to_approve'

    def action_approve(self):
        self.state = 'approved'
        self.approver_id = self.env.user.id
        self.approval_date = fields.Date.today()

    def action_reject(self):
        self.state = 'rejected'

    def action_cancel(self):
        self.state = 'cancel'
        if self.workshop_id:
            self.workshop_id.state = 'cancel'

    def action_done(self):
        self.state = 'done'

    def action_create_workshop(self):
        self.ensure_one()
        if self.workshop_id:
            raise UserError(_("A workshop order has already been created for this request: %s") % self.workshop_id.name)
        vals = {
            'vehicle_id': self.vehicle_id.id,
            'name': _('New'),  # El nombre se generará automáticamente en car.workshop
            'description': self.description,
            'priority': self.priority,
        }
        workshop = self.env['car.workshop'].create(vals)
        self.workshop_id = workshop.id
        return {
            'name': _('Workshop Order'),
            'view_mode': 'form',
            'res_model': 'car.workshop',
            'res_id': workshop.id,
            'type': 'ir.actions.act_window',
            'context': {'default_workshop_request_id': self.id}
        }
