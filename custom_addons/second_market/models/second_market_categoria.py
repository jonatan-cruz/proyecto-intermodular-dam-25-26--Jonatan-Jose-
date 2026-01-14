# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CategoriaSegundaMano(models.Model):
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
    
    # Relación con artículos
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
    
    @api.depends('articulos_ids')
    def _compute_conteo_articulos(self):
        for categoria in self:
            categoria.conteo_articulos = len(categoria.articulos_ids.filtered(
                lambda a: a.estado_publicacion == 'publicado'
            ))
    
    @api.constrains('name')
    def _check_name_unique(self):
        for categoria in self:
            if self.search_count([('name', '=ilike', categoria.name), ('id', '!=', categoria.id)]) > 0:
                raise ValidationError(_('Ya existe una categoría con este nombre.'))
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'El nombre de la categoría debe ser único.')
    ]
