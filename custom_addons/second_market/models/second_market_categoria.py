# -*- coding: utf-8 -*-

"""
Módulo de gestión de categorías de artículos.

Define el modelo :class:`CategoriaSegundaMano` que agrupa los artículos
de la plataforma Second Market en categorías temáticas.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CategoriaSegundaMano(models.Model):
    """Modelo que representa una categoría de artículos de segunda mano.

    Las categorías permiten clasificar los artículos para facilitar
    su búsqueda y filtrado en la plataforma.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _order: Orden alfabético por nombre.
    """

    _name = 'second_market.category'
    _description = 'Categoría de Artículos de Segunda Mano'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        size=50,
        help='Nombre de la categoría'
    )

    descripcion = fields.Text(
        string='Descripción',
        help='Descripción de la categoría'
    )

    imagen = fields.Binary(
        string='Imagen',
        help='Imagen representativa de la categoría'
    )

    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, la categoría no aparecerá en las opciones'
    )

    color = fields.Integer(
        string='Color',
        help='Color para visualización en Kanban'
    )

    icono = fields.Char(
        string='Icono',
        help='Nombre del icono Font Awesome (ej: fa-laptop)'
    )

    articulos_ids = fields.One2many(
        'second_market.article',
        'id_categoria',
        string='Artículos'
    )

    conteo_articulos = fields.Integer(
        string='Número de Artículos',
        compute='_compute_conteo_articulos',
        store=True
    )

    @api.depends('articulos_ids', 'articulos_ids.estado_publicacion', 'articulos_ids.activo')
    def _compute_conteo_articulos(self):
        """Contar los artículos publicados que pertenecen a la categoría.

        Solo se contabilizan artículos cuyo ``estado_publicacion`` sea
        ``'publicado'``. Almacena el resultado en :attr:`conteo_articulos`.

        .. note::
            Si ocurre un error durante el cálculo, asigna ``0`` y registra
            una advertencia en el log del servidor.
        """
        for categoria in self:
            try:
                if categoria.articulos_ids:
                    articulos_publicados = categoria.articulos_ids.filtered(
                        lambda a: a.estado_publicacion == 'publicado'
                    )
                    categoria.conteo_articulos = len(articulos_publicados)
                else:
                    categoria.conteo_articulos = 0
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando conteo de artículos para categoría {categoria.id}: {str(e)}")
                categoria.conteo_articulos = 0

    @api.constrains('name')
    def _check_name_unique(self):
        """Validar que el nombre de la categoría sea único (insensible a mayúsculas).

        :raises ValidationError: Si ya existe otra categoría con el mismo nombre.
        """
        for categoria in self:
            if self.search_count([('name', '=ilike', categoria.name), ('id', '!=', categoria.id)]) > 0:
                raise ValidationError(_('Ya existe una categoría con este nombre.'))

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'El nombre de la categoría debe ser único.')
    ]
