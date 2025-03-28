from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPickingWizard(models.TransientModel):
    _name = 'stock.picking.wizard'
    _description = 'Wizard para Crear Stock Picking'

    workshop_id = fields.Many2one('car.workshop', string="Orden de Taller", required=True)
    picking_type_id = fields.Many2one('stock.picking.type', string="Tipo de Picking", required=True)
    location_id = fields.Many2one('stock.location', string="Ubicación de Origen", required=True)
    location_dest_id = fields.Many2one('stock.location', string="Ubicación de Destino", required=True)
    product_lines = fields.One2many('stock.picking.wizard.line', 'wizard_id', string="Productos")

    def action_create_picking(self):
        """ Crea el stock picking basado en los materiales del taller """
        if not self.product_lines:
            raise UserError("Debe agregar al menos un producto.")

        picking_vals = {
            'partner_id': self.workshop_id.partner_id.id,
            'origin': self.workshop_id.name,
            'move_type': 'direct',
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_dest_id.id,
            'car_workshop_id': self.workshop_id.id,  # ASIGNAR EL ID DEL TALLER            
            'move_ids': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'quantity': line.quantity,  # Cantidad realizada                 
                'product_uom': line.product_id.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
            }) for line in self.product_lines],
        }

        picking = self.env['stock.picking'].create(picking_vals)
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()

        return {'type': 'ir.actions.act_window_close'}

class StockPickingWizardLine(models.TransientModel):
    _name = 'stock.picking.wizard.line'
    _description = 'Línea de Productos en Wizard'

    wizard_id = fields.Many2one('stock.picking.wizard', string="Wizard")
    product_id = fields.Many2one('product.product', string="Producto", required=True)
    quantity = fields.Float(string="Cantidad", required=True, default=1.0)
