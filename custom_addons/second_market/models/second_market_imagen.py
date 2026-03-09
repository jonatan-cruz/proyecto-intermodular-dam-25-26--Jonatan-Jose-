# -*- coding: utf-8 -*-

"""
Módulo de gestión de imágenes de artículos.

Define el modelo :class:`ImagenArticulo` que almacena las imágenes
asociadas a cada artículo de la plataforma Second Market.
"""

from odoo import models, fields, api, _


class ImagenArticulo(models.Model):
    """Modelo que representa una imagen vinculada a un artículo de segunda mano.

    Cada artículo puede tener entre 1 y 10 imágenes. El orden de visualización
    se controla mediante el campo ``sequence``.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _order: Ordenación por ``sequence`` y luego por ``id``.
    """

    _name = 'second_market.image'
    _description = 'Imagen de Artículo'
    _order = 'sequence, id'

    name = fields.Char(
        string='Descripción',
        help='Pequeña descripción de la imagen'
    )

    image = fields.Binary(
        string='Imagen',
        required=True,
        help='Archivo de imagen'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de aparición de la imagen (menor número = primera posición)'
    )

    article_id = fields.Many2one(
        'second_market.article',
        string='Artículo',
        ondelete='cascade',
        required=True,
        help='Artículo al que pertenece esta imagen'
    )
