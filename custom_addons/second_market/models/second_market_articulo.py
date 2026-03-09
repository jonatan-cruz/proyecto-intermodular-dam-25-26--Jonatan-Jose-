# -*- coding: utf-8 -*-

"""
Módulo de gestión de artículos de segunda mano.

Define el modelo :class:`ArticuloSegundaMano` que representa los productos
publicados por los usuarios en la plataforma Second Market.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ArticuloSegundaMano(models.Model):
    """Modelo que representa un artículo de segunda mano publicado en la plataforma.

    Hereda de ``mail.thread`` y ``mail.activity.mixin`` para soporte de
    seguimiento de cambios y actividades programadas.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _inherit: Mixins heredados para chatter y actividades.
    :cvar _order: Orden por defecto (más reciente primero).
    :cvar _rec_name: Campo utilizado como nombre representativo del registro.
    """

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
        'second_market.user',
        string='Propietario',
        required=True,
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
        'id_articulo',
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

    def action_publicar(self):
        """Pasar el artículo al estado *publicado*.

        Solo se pueden publicar artículos que se encuentren en estado ``borrador``.

        :raises UserError: Si el artículo no está en estado ``borrador``.
        :return: ``True`` si la operación se realizó correctamente.
        :rtype: bool
        """
        for articulo in self:
            if articulo.estado_publicacion == 'borrador':
                articulo.write({'estado_publicacion': 'publicado'})
            else:
                raise UserError(_('Solo se pueden publicar artículos en estado borrador.'))
        return True

    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================

    @api.depends('ids_imagenes')
    def _computar_conteo_imagenes(self):
        """Calcular el número total de imágenes asociadas al artículo.

        Recalcula cuando cambia el campo ``ids_imagenes``.
        Almacena el resultado en :attr:`conteo_imagenes`.
        """
        for articulo in self:
            articulo.conteo_imagenes = len(articulo.ids_imagenes)

    @api.depends('ids_imagenes.image')
    def _computar_imagen_principal(self):
        """Obtener la imagen principal del artículo.

        Selecciona la primera imagen de la lista ``ids_imagenes`` (menor
        secuencia o primera creada). Almacena el resultado en
        :attr:`imagen_principal`.
        """
        for articulo in self:
            if articulo.ids_imagenes:
                articulo.imagen_principal = articulo.ids_imagenes[0].image
            else:
                articulo.imagen_principal = False

    @api.depends('ids_etiquetas')
    def _computar_conteo_etiquetas(self):
        """Calcular el número de etiquetas asignadas al artículo.

        Almacena el resultado en :attr:`conteo_etiquetas`.
        """
        for articulo in self:
            articulo.conteo_etiquetas = len(articulo.ids_etiquetas)

    @api.depends('ids_comentarios')
    def _computar_conteo_comentarios(self):
        """Contar los comentarios activos del artículo.

        Solo cuenta comentarios cuyo campo ``activo`` sea ``True``.
        Almacena el resultado en :attr:`conteo_comentarios`.
        """
        for articulo in self:
            articulo.conteo_comentarios = len(articulo.ids_comentarios.filtered(lambda c: c.activo))

    def _computar_reportado(self):
        """Indicar si el artículo tiene denuncias pendientes.

        .. note::
            Implementación temporal: siempre devuelve ``False`` hasta que
            se implemente el sistema de denuncias.
        """
        for articulo in self:
            articulo.reportado = False

    def _computar_conteo_favoritos(self):
        """Contar el número de usuarios que han marcado el artículo como favorito.

        .. note::
            Implementación temporal: siempre devuelve ``0`` hasta que se
            implemente el sistema de favoritos.
        """
        for articulo in self:
            articulo.conteo_favoritos = 0

    def _computar_conteo_chats(self):
        """Contar los chats activos vinculados al artículo.

        Solo cuenta chats cuyo campo ``activo`` sea ``True``.
        Almacena el resultado en :attr:`conteo_chats`.
        """
        for articulo in self:
            articulo.conteo_chats = len(articulo.ids_chats.filtered(lambda c: c.activo))

    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================

    @api.constrains('ids_imagenes')
    def _check_conteo_imagenes(self):
        """Validar que el artículo tenga entre 1 y 10 imágenes.

        :raises ValidationError: Si hay menos de 1 imagen o más de 10.
        """
        for articulo in self:
            if len(articulo.ids_imagenes) < 1:
                raise ValidationError(_('Debes subir al menos 1 imagen.'))
            if len(articulo.ids_imagenes) > 10:
                raise ValidationError(_('No puedes subir más de 10 imágenes.'))

    @api.constrains('ids_etiquetas')
    def _check_conteo_etiquetas(self):
        """Validar que el artículo no tenga más de 5 etiquetas.

        :raises ValidationError: Si se asignan más de 5 etiquetas.
        """
        for articulo in self:
            if len(articulo.ids_etiquetas) > 5:
                raise ValidationError(_('No puedes asignar más de 5 etiquetas.'))

    @api.constrains('precio')
    def _check_precio(self):
        """Validar que el precio sea un valor positivo mayor que 0.

        :raises ValidationError: Si el precio es negativo o igual a 0.
        """
        for articulo in self:
            if articulo.precio < 0:
                raise ValidationError(_('El precio no puede ser negativo.'))
            if articulo.precio == 0:
                raise ValidationError(_('El precio debe ser mayor que 0.'))

    @api.constrains('antiguedad')
    def _check_antiguedad(self):
        """Validar que la antigüedad no sea un valor negativo.

        :raises ValidationError: Si la antigüedad es un número negativo.
        """
        for articulo in self:
            if articulo.antiguedad < 0:
                raise ValidationError(_('La antigüedad no puede ser negativa.'))

    @api.constrains('nombre')
    def _check_nombre_length(self):
        """Validar que el nombre del artículo no supere 50 caracteres.

        :raises ValidationError: Si el nombre tiene más de 50 caracteres.
        """
        for articulo in self:
            if len(articulo.nombre) > 50:
                raise ValidationError(_('El nombre no puede tener más de 50 caracteres.'))

    @api.constrains('descripcion')
    def _check_descripcion_length(self):
        """Validar que la descripción no supere 100 caracteres.

        :raises ValidationError: Si la descripción tiene más de 100 caracteres.
        """
        for articulo in self:
            if articulo.descripcion and len(articulo.descripcion) > 100:
                raise ValidationError(_('La descripción no puede tener más de 100 caracteres.'))
