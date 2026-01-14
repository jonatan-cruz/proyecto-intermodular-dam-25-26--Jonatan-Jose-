# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ImagenArticulo(models.Model):
    _name = 'second_market.image'
    _description = 'Imagen de Artículo'
    _order = 'sequence, id'

    name = fields.Char(string='Descripción', help='Pequeña descripción de la imagen')
    image = fields.Binary(string='Imagen', required=True, help='Archivo de imagen')
    sequence = fields.Integer(string='Secuencia', default=10)
    
    article_id = fields.Many2one(
        'second_market.article', 
        string='Artículo', 
        ondelete='cascade',
        required=True
    )
