# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class EtiquetaSegundaMano(models.Model):
    _name = 'second_market.tag'
    _description = 'Etiqueta de Artículos'
    
    name = fields.Char(string='Nombre', required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'El nombre de la etiqueta debe ser único.'),
    ]
