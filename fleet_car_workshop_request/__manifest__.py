# -*- coding: utf-8 -*-
{
    'name': 'Fleet Car Workshop Request',
    'summary': 'Gestiona las solicitudes de ingreso al taller',
    'version': '1.0',
    'category': 'Fleet',
    'depends': ['fleet', 'fleet_car_workshop'],  # Dependencia del módulo fleet_car_workshop
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/workshop_request_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
