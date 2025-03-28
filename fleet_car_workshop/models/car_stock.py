from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    car_workshop_id = fields.Many2one(
        'car.workshop',
        string='Orden de Taller',
        readonly=True,  # Opcional: Si solo quieres mostrar, no editar
        store=True,       # Importante para que se pueda buscar y filtrar
        index=True,      # Importante para mejorar el rendimiento de las búsquedas
    )
