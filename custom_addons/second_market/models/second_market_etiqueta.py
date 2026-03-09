# -*- coding: utf-8 -*-

"""
Módulo de gestión de etiquetas de artículos.

Define el modelo :class:`EtiquetaSegundaMano` que permite asignar
etiquetas descriptivas a los artículos de la plataforma.
"""

from odoo import models, fields, api, _


class EtiquetaSegundaMano(models.Model):
    """Modelo que representa una etiqueta para artículos de segunda mano.

    Las etiquetas permiten describir características adicionales de un artículo.
    Cada artículo puede tener un máximo de 5 etiquetas.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    """

    _name = 'second_market.tag'
    _description = 'Etiqueta de Artículos'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre único de la etiqueta'
    )

    color = fields.Integer(
        string='Color Index',
        help='Índice de color para visualización en la interfaz'
    )

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'El nombre de la etiqueta debe ser único.'),
    ]
