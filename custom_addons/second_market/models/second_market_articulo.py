# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ArticuloSegundaMano(models.Model):
    _name = 'second_market.article'
    _description = 'Artículo de Segunda Mano'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _order = 'create_date desc'
    _rec_name = 'nombre'
    
    # ============================================
    # CAMPOS BÁSICOS
    # ============================================
    
    nombre = fields.Char(
        string='Nombre del Producto',
        required=True,
        size=50,
        tracking=True,
        help='Nombre descriptivo del artículo'
    )
    
    codigo = fields.Char(
        string='Código',
        size=7,
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
        help='Código único de 7 dígitos'
    )
    
    descripcion = fields.Text(
        string='Descripción',
        tracking=True,
        help='Descripción detallada del artículo (máx 100 caracteres)'
    )
    
    # ============================================
    # RELACIONES
    # ============================================
    
    id_propietario = fields.Many2one(
        'res.partner',
        string='Propietario',
        required=True,
        default=lambda self: self.env.user.partner_id,
        tracking=True,
        ondelete='restrict',
        help='Usuario que publica el artículo'
    )
    
    id_categoria = fields.Many2one(
        'second_market.category',
        string='Categoría',
        required=True,
        tracking=True,
        ondelete='restrict',
        help='Categoría del producto'
    )
    
    # ============================================
    # INFORMACIÓN DEL PRODUCTO
    # ============================================
    
    antiguedad = fields.Integer(
        string='Antigüedad (años)',
        default=0,
        tracking=True,
        help='Años de antigüedad del producto'
    )
    
    estado_producto = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('como_nuevo', 'Como Nuevo'),
        ('buen_estado', 'Buen Estado'),
        ('aceptable', 'Estado Aceptable'),
        ('necesita_reparacion', 'Necesita Reparación')
    ], 
        string='Estado del Producto',
        required=True,
        default='buen_estado',
        tracking=True
    )
    
    precio = fields.Float(
        string='Precio (€)',
        required=True,
        digits=(10, 2),
        tracking=True,
        help='Precio de venta en euros'
    )
    
    # ============================================
    # UBICACIÓN
    # ============================================
    
    localidad = fields.Char(
        string='Ubicación',
        required=True,
        tracking=True,
        help='Ciudad o ubicación del artículo'
    )
    
    latitud = fields.Float(
        string='Latitud',
        digits=(10, 6)
    )
    
    longitud = fields.Float(
        string='Longitud',
        digits=(10, 6)
    )
    
    # ============================================
    # IMÁGENES Y ETIQUETAS
    # ============================================
    
    ids_imagenes = fields.One2many(
        'second_market.image',
        'article_id',
        string='Imágenes',
        help='Entre 1 y 10 imágenes del producto'
    )
    
    ids_etiquetas = fields.Many2many(
        'second_market.tag',
        'second_market_article_tag_rel', 
        'article_id',
        'tag_id',
        string='Etiquetas',
        help='Máximo 5 etiquetas'
    )

    conteo_imagenes = fields.Integer(
        string='Número de Imágenes',
        compute='_computar_conteo_imagenes',
        store=True
    )
    
    imagen_principal = fields.Binary(
        string='Imagen Principal',
        compute='_computar_imagen_principal',
        store=False
    )
    
    conteo_etiquetas = fields.Integer(
        string='Número de Etiquetas',
        compute='_computar_conteo_etiquetas',
        store=True
    )
    
    # ============================================
    # ESTADO DE PUBLICACIÓN
    # ============================================
    
    estado_publicacion = fields.Selection([
        ('borrador', 'Borrador'),
        ('publicado', 'Publicado'),
        ('reservado', 'Reservado'),
        ('vendido', 'Vendido'),
        ('eliminado', 'Eliminado')
    ],
        string='Estado',
        default='borrador',
        required=True,
        tracking=True
    )
    
    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, el artículo no aparecerá en búsquedas'
    )
    
    # ============================================
    # ESTADÍSTICAS
    # ============================================
    
    conteo_vistas = fields.Integer(
        string='Visualizaciones',
        default=0,
        readonly=True,
        help='Número de veces que se ha visto el artículo'
    )
    
    conteo_favoritos = fields.Integer(
        string='Favoritos',
        compute='_computar_conteo_favoritos',
        store=True
    )
    
    conteo_comentarios = fields.Integer(
        string='Comentarios',
        compute='_computar_conteo_comentarios',
        store=True
    )
    
    conteo_chats = fields.Integer(
        string='Chats',
        compute='_computar_conteo_chats',
        store=True
    )
    
    # ============================================
    # RELACIONES CON OTROS MODELOS
    # ============================================
    
    ids_comentarios = fields.One2many(
        'second_market.comment',
        'id_articulo',  # ← Campo que debe existir en second.market.comment
        string='Comentarios'
    )
    
    ids_chats = fields.One2many(
        'second_market.chat',
        'id_articulo',
        string='Conversaciones'
    )
    
    reportado = fields.Boolean(
        string='Reportado',
        compute='_computar_reportado',
        store=True,
        help='El artículo tiene denuncias pendientes'
    )
    
    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================
    
    @api.depends('ids_imagenes')
    def _computar_conteo_imagenes(self):
        for articulo in self:
            articulo.conteo_imagenes = len(articulo.ids_imagenes)
    
    @api.depends('ids_imagenes.image')
    def _computar_imagen_principal(self):
        for articulo in self:
            if articulo.ids_imagenes:
                # Tomamos la imagen con menor secuencia o la primera creada
                articulo.imagen_principal = articulo.ids_imagenes[0].image
            else:
                articulo.imagen_principal = False
    
    @api.depends('ids_etiquetas')
    def _computar_conteo_etiquetas(self):
        for articulo in self:
            articulo.conteo_etiquetas = len(articulo.ids_etiquetas)
    
    @api.depends('ids_comentarios')
    def _computar_conteo_comentarios(self):
        """Contar comentarios del artículo"""
        for articulo in self:
            articulo.conteo_comentarios = len(articulo.ids_comentarios.filtered(lambda c: c.activo))
    
    def _computar_reportado(self):
        """Temporal: devuelve False hasta implementar denuncias"""
        for articulo in self:
            articulo.reportado = False
    
    def _computar_conteo_favoritos(self):
        """Temporal: devuelve 0 hasta implementar favoritos"""
        for articulo in self:
            articulo.conteo_favoritos = 0
    
    def _computar_conteo_chats(self):
        """Contar chats activos del artículo"""
        for articulo in self:
            articulo.conteo_chats = len(articulo.ids_chats.filtered(lambda c: c.activo))
    
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    @api.constrains('ids_imagenes')
    def _check_conteo_imagenes(self):
        for articulo in self:
            if len(articulo.ids_imagenes) < 1:
                raise ValidationError(_('Debes subir al menos 1 imagen.'))
            if len(articulo.ids_imagenes) > 10:
                raise ValidationError(_('No puedes subir más de 10 imágenes.'))
    
    @api.constrains('ids_etiquetas')
    def _check_conteo_etiquetas(self):
        for articulo in self:
            if len(articulo.ids_etiquetas) > 5:
                raise ValidationError(_('No puedes asignar más de 5 etiquetas.'))
    
    @api.constrains('precio')
    def _check_precio(self):
        for articulo in self:
            if articulo.precio < 0:
                raise ValidationError(_('El precio no puede ser negativo.'))
            if articulo.precio == 0:
                raise ValidationError(_('El precio debe ser mayor que 0.'))
    
    @api.constrains('antiguedad')
    def _check_antiguedad(self):
        for articulo in self:
            if articulo.antiguedad < 0:
                raise ValidationError(_('La antigüedad no puede ser negativa.'))
    
    @api.constrains('nombre')
    def _check_nombre_length(self):
        for articulo in self:
            if len(articulo.nombre) > 50:
                raise ValidationError(_('El nombre no puede tener más de 50 caracteres.'))
    
    @api.constrains('descripcion')
    def _check_descripcion_length(self):
        for articulo in self:
            if articulo.descripcion and len(articulo.descripcion) > 100:
                raise ValidationError(_('La descripción no puede tener más de 100 caracteres.'))
