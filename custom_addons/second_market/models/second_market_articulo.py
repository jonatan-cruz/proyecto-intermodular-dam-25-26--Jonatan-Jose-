# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ArticuloSegundaMano(models.Model):
    _name = 'second.market.article'
    _description = 'Artículo de Segunda Mano'
    _inherit = ['mail.thread', 'mail.activity.mixin'] 
    _order = 'create_date desc'
    
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
        'second.market.category',
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
    # IMÁGENES
    # ============================================
    
    # ids_imagenes = fields.Many2many(
    #     'ir.attachment',
    #     'second_market_article_image_rel',
    #     'article_id',
    #     'attachment_id',
    #     string='Imágenes',
    #     help='Entre 1 y 10 imágenes del producto'
    # )
    
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
    
    # ============================================
    # ETIQUETAS
    # ============================================
    
    # ids_etiquetas = fields.Many2many(
    #     'second.market.tag',
    #     'second_market_article_tag_rel', 
    #     'article_id',
    #     'tag_id',
    #     string='Etiquetas',
    #     help='Máximo 5 etiquetas'
    # )
    
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
    
    #conteo_chats = fields.Integer(  # ← FALTABA ESTE CAMPO
    #    string='Chats',
    #    compute='_computar_conteo_chats',
    #    store=True
    #)
    
    # ============================================
    # RELACIONES CON OTROS MODELOS
    # ============================================
    
    # ids_comentarios = fields.One2many(
    #     'second.market.comment',
    #     'id_articulo',  # ← Campo que debe existir en second.market.comment
    #     string='Comentarios'
    # )
    
    # ids_chats = fields.One2many(
    #     'second.market.chat',
    #     'id_articulo',  # ← Campo que debe existir en second.market.chat
    #     string='Conversaciones'
    # )
    
    # id_transaccion = fields.Many2one(
    #     'second.market.transaction',
    #     string='Transacción',
    #     readonly=True,
    #     help='Transacción de venta asociada'
    # )
    
    # ids_denuncias = fields.One2many(
    #     'second.market.report',  # ← CORREGIDO: estaba duplicado "secondsecond"
    #     'id_articulo',  # ← Campo que debe existir en second.market.report
    #     string='Denuncias'
    # )
    
    reportado = fields.Boolean(
        string='Reportado',
        compute='_computar_reportado',
        store=True,
        help='El artículo tiene denuncias pendientes'
    )
    
    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================
    
    def _computar_conteo_imagenes(self):
        """Temporal: devuelve 0 hasta implementar imágenes"""
        for articulo in self:
            articulo.conteo_imagenes = 0
    
    def _computar_imagen_principal(self):
        """Temporal: devuelve False hasta implementar imágenes"""
        for articulo in self:
            articulo.imagen_principal = False
    
    def _computar_conteo_etiquetas(self):
        """Temporal: devuelve 0 hasta implementar etiquetas"""
        for articulo in self:
            articulo.conteo_etiquetas = 0
    
    def _computar_conteo_comentarios(self):
        """Temporal: devuelve 0 hasta implementar comentarios"""
        for articulo in self:
            articulo.conteo_comentarios = 0
    
    def _computar_reportado(self):
        """Temporal: devuelve False hasta implementar denuncias"""
        for articulo in self:
            articulo.reportado = False
    
    def _computar_conteo_favoritos(self):
        """Temporal: devuelve 0 hasta implementar favoritos"""
        for articulo in self:
            articulo.conteo_favoritos = 0
    
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    # @api.constrains('ids_imagenes')
    # def _check_conteo_imagenes(self):
    #     for articulo in self:
    #         if len(articulo.ids_imagenes) < 1:
    #             raise ValidationError(_('Debes subir al menos 1 imagen.'))
    #         if len(articulo.ids_imagenes) > 10:
    #             raise ValidationError(_('No puedes subir más de 10 imágenes.'))
    
    # @api.constrains('ids_etiquetas')
    # def _check_conteo_etiquetas(self):
    #     for articulo in self:
    #         if len(articulo.ids_etiquetas) > 5:
    #             raise ValidationError(_('No puedes asignar más de 5 etiquetas.'))
    
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
    
    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================
    
    # @api.model
    # def create(self, vals):
    #     # Generar código único de 7 dígitos
    #     if vals.get('codigo', _('Nuevo')) == _('Nuevo'):
    #         vals['codigo'] = self.env['ir.sequence'].next_by_code('second.market.article') or _('Nuevo')
        
    #     # Establecer estado inicial
    #     if not vals.get('estado_publicacion'):
    #         vals['estado_publicacion'] = 'borrador'
        
    #     articulo = super(ArticuloSegundaMano, self).create(vals)
        
    #     # Enviar notificación si se publica directamente
    #     if articulo.estado_publicacion == 'publicado':
    #         articulo._notificar_seguidores()
        
    #     return articulo
    
    # def write(self, vals):
    #     # Tracking de cambio de estado
    #     if 'estado_publicacion' in vals:
    #         for articulo in self:
    #             if vals['estado_publicacion'] == 'publicado' and articulo.estado_publicacion == 'borrador':
    #                 articulo._notificar_seguidores()
    #             elif vals['estado_publicacion'] == 'vendido' and articulo.estado_publicacion != 'vendido':
    #                 articulo._notificar_venta()
        
    #     return super(ArticuloSegundaMano, self).write(vals)
    
    # ============================================
    # MÉTODOS DE ACCIÓN
    # ============================================
    
    # def accion_publicar(self):
    #     """Publicar artículo"""
    #     self.ensure_one()
    #     if self.estado_publicacion != 'borrador':
    #         raise UserError(_('Solo puedes publicar artículos en borrador.'))
        
    #     # Validar que tenga al menos una imagen
    #     if not self.ids_imagenes:
    #         raise UserError(_('Debes subir al menos una imagen antes de publicar.'))
        
    #     self.write({'estado_publicacion': 'publicado'})
        
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _('¡Artículo Publicado!'),
    #             'message': _('Tu artículo está ahora visible para otros usuarios.'),
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }
    
    # def accion_despublicar(self):
    #     """Despublicar artículo (volver a borrador)"""
    #     self.ensure_one()
    #     if self.estado_publicacion not in ['publicado', 'reservado']:
    #         raise UserError(_('Solo puedes despublicar artículos publicados o reservados.'))
        
    #     self.write({'estado_publicacion': 'borrador'})
    #     return True
    
    # def accion_marcar_vendido(self):
    #     """Marcar como vendido"""
    #     self.ensure_one()
    #     if self.estado_publicacion == 'vendido':
    #         raise UserError(_('El artículo ya está marcado como vendido.'))
        
    #     self.write({'estado_publicacion': 'vendido'})
        
    #     # Actualizar estadísticas del propietario
    #     # TODO: Implementar cuando extiendas res.partner
        
    #     return True
    
    # def accion_eliminar(self):
    #     """Eliminar artículo (solo moderadores)"""
    #     self.ensure_one()
        
    #     # Verificar permisos
    #     if not self.env.user.has_group('second_market.group_second_market_moderator'):
    #         raise UserError(_('No tienes permisos para eliminar artículos.'))
        
    #     self.write({
    #         'estado_publicacion': 'eliminado',
    #         'activo': False
    #     })
        
    #     # Notificar al propietario
    #     self._notificar_eliminacion()
        
    #     return True
    
    # def accion_ver_chats(self):
    #     """Abrir vista de chats del artículo"""
    #     self.ensure_one()
    #     return {
    #         'name': _('Chats del Artículo'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'second.market.chat',
    #         'view_mode': 'tree,form',
    #         'domain': [('id_articulo', '=', self.id)],
    #         'context': {'default_id_articulo': self.id}
    #     }
    
    # def accion_ver_comentarios(self):
    #     """Abrir vista de comentarios del artículo"""
    #     self.ensure_one()
    #     return {
    #         'name': _('Comentarios del Artículo'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'second.market.comment',
    #         'view_mode': 'tree,form',
    #         'domain': [('id_articulo', '=', self.id)],
    #         'context': {'default_id_articulo': self.id}
    #     }
    
    # def accion_incrementar_vistas(self):
    #     """Incrementar contador de visualizaciones"""
    #     self.ensure_one()
    #     self.conteo_vistas += 1
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    # def _notificar_seguidores(self):
    #     """Notificar a seguidores cuando se publica"""
    #     self.ensure_one()
    #     # TODO: implementar sistema de followers/notificaciones
    #     pass
    
    # def _notificar_venta(self):
    #     """Notificar venta del artículo"""
    #     self.ensure_one()
    #     # TODO: enviar emails a interesados
    #     pass
    
    # def _notificar_eliminacion(self):
    #     """Notificar al propietario que su artículo fue eliminado"""
    #     self.ensure_one()
    #     # TODO: enviar email al propietario
    #     pass