from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class WorkshopRequest(models.Model):
    _name = 'workshop.request'
    _description = 'Solicitud de Ingreso al Taller'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Número de Solicitud', required=True, readonly=True, default=lambda self: _('Nuevo'))
    workshop_id = fields.Many2one('car.workshop', string='Taller', help='Taller al que se refiere esta solicitud')
    analyst_id = fields.Many2one('res.users', string='Analista', default=lambda self: self.env.user, readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', required=True)
    reported_fault = fields.Text(string='Falla Reportada', required=True)
    assignment_date = fields.Date(string='Fecha de Asignación', readonly=True, store=True)
    request_date = fields.Datetime(string='Fecha de Solicitud', readonly=True, default=fields.Datetime.now) #AGREGA ESTE CAMPO
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('waiting_assignment', 'Esperando Asignación'),
        ('confirmed', 'Confirmada'),
        ('done', 'Realizada'),
        ('cancel', 'Cancelada'),
    ], string='Estado', default='draft', tracking=True)
    workshop_order_id = fields.Many2one('car.workshop', string='Orden de Taller', readonly=True, copy=False)
    is_analyst = fields.Boolean(string='Es Analista', compute='_compute_is_analyst', store=False)

    @api.depends('analyst_id')
    def _compute_is_analyst(self):
        #Computa si el usuario actual es el analista de la solicitud
        for rec in self:
            rec.is_analyst = self.env.user == rec.analyst_id

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('workshop.request.sequence') or _('Nuevo')
        return super(WorkshopRequest, self).create(vals)

    def action_register_request(self):
        self.state = 'waiting_assignment'

    def action_confirm_request(self):
        if not self.assignment_date:
            raise UserError(_('Debe asignar una fecha antes de confirmar.'))

        self.state = 'confirmed'
        #Crea la orden de taller automaticamente al confirmar la solicitud
        self.workshop_order_id = self.env['car.workshop'].create({
                                                                    'vehicle_id': self.vehicle_id.id,
                                                                    'name': f'{self.name} - {self.vehicle_id.name}',
                                                                    'date_assign':self.assignment_date
                                                                    })

        template_id = self.env.ref('fleet_car_workshop_request.email_template_workshop_request_confirmation')
        self.message_post_with_template(
            template_id=template_id.id,
            composition_mode='comment',
            force_send=True,
            model='workshop.request',
            res_id=self.id
        )

    def action_set_done(self):
        self.state = 'done'

    def action_cancel_request(self):
        self.state = 'cancel'

    def unlink(self):
        #No permite borrar si ya se confirmo
        for rec in self:
            if rec.state == 'confirmed':
                raise UserError(_("No se puede borrar una solicitud confirmada."))
        return super(WorkshopRequest, self).unlink()
