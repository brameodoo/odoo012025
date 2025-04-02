##
# -*- coding: utf-8 -*-
# models/fleet_vehicle_inherit.py

from odoo import models, fields, api

class FleetVehicleInherit(models.Model):
    _inherit = 'fleet.vehicle'

    vin_sn = fields.Char(string='VIN/SN', track_visibility='onchange')
    manager_id = fields.Many2one('res.users', string='Manager', track_visibility='onchange')
    location = fields.Char(string='Location', track_visibility='onchange')