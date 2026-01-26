# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class SecondMarketComment(models.Model):
    _name = 'second_market.comment'
    _description = 'Comentario de Second Market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_hora desc'
    
    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================
    
    id_mensaje = fields.Char(
        string='ID Mensaje',
        size=7,
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
        help='Código único de 7 dígitos para el mensaje'
    )
    
    id_emisor = fields.Many2one(
        'second_market.user',
        string='Emisor',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Usuario que envía el comentario'
    )
    
    id_receptor = fields.Many2one(
        'second_market.user',
        string='Receptor',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Usuario que recibe el comentario'
    )
    
    texto = fields.Text(
        string='Comentario',
        required=True,
        help='Contenido del comentario'
    )
    
    fecha_hora = fields.Datetime(
        string='Fecha y Hora',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
        help='Fecha y hora de envío del comentario'
    )
    
    # ============================================
    # RELACIONES
    # ============================================
    
    id_articulo = fields.Many2one(
        'second_market.article',
        string='Artículo',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Artículo al que pertenece el comentario'
    )
    
    # ============================================
    # CAMPOS DE ESTADO
    # ============================================
    
    leido = fields.Boolean(
        string='Leído',
        default=False,
        tracking=True,
        help='Indica si el comentario ha sido leído por el receptor'
    )
    
    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, el comentario está eliminado'
    )
    
    fecha_lectura = fields.Datetime(
        string='Fecha de Lectura',
        readonly=True,
        help='Fecha y hora en que se leyó el comentario'
    )
    
    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================
    
    nombre_emisor = fields.Char(
        string='Nombre Emisor',
        related='id_emisor.name',
        store=True,
        readonly=True
    )
    
    nombre_receptor = fields.Char(
        string='Nombre Receptor',
        related='id_receptor.name',
        store=True,
        readonly=True
    )
    
    nombre_articulo = fields.Char(
        string='Artículo',
        related='id_articulo.nombre',
        store=True,
        readonly=True
    )
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    @api.constrains('id_emisor', 'id_receptor')
    def _check_emisor_receptor(self):
        """Validar que emisor y receptor no sean el mismo usuario"""
        for comentario in self:
            if comentario.id_emisor == comentario.id_receptor:
                raise ValidationError(_('El emisor y el receptor no pueden ser el mismo usuario.'))
    
    @api.constrains('texto')
    def _check_texto(self):
        """Validar que el texto no esté vacío"""
        for comentario in self:
            if not comentario.texto or not comentario.texto.strip():
                raise ValidationError(_('El comentario no puede estar vacío.'))
            if len(comentario.texto) > 500:
                raise ValidationError(_('El comentario no puede tener más de 500 caracteres.'))
    
    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar ID único al crear"""
        for vals in vals_list:
            if vals.get('id_mensaje', _('Nuevo')) == _('Nuevo'):
                vals['id_mensaje'] = self.env['ir.sequence'].next_by_code('second_market.comment') or _('Nuevo')
        
        comentarios = super(SecondMarketComment, self).create(vals_list)
        
        # Notificar al receptor (opcional)
        for comentario in comentarios:
            comentario._notificar_nuevo_comentario()
        
        return comentarios
    
    def write(self, vals):
        """Tracking de cambios importantes"""
        if 'leido' in vals and vals['leido'] and not self.leido:
            vals['fecha_lectura'] = fields.Datetime.now()
        
        return super(SecondMarketComment, self).write(vals)
    
    # ============================================
    # MÉTODOS PRINCIPALES (FUNCIONES REQUERIDAS)
    # ============================================
    
    def enviar(self):
        """Enviar el comentario"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('No puedes enviar un comentario eliminado.'))
        
        if self.leido:
            raise UserError(_('Este comentario ya ha sido enviado y leído.'))
        
        # Actualizar fecha y hora de envío
        self.write({
            'fecha_hora': fields.Datetime.now()
        })
        
        # Notificar
        self._notificar_nuevo_comentario()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Comentario Enviado!'),
                'message': _('Tu comentario ha sido enviado correctamente.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def leer(self):
        """Marcar comentario como leído"""
        self.ensure_one()
        
        # Verificar que el usuario actual sea el receptor
        # (Esto requiere integración con res.users)
        
        if self.leido:
            raise UserError(_('Este comentario ya fue marcado como leído.'))
        
        self.write({
            'leido': True,
            'fecha_lectura': fields.Datetime.now()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Comentario Leído'),
                'message': _('El comentario ha sido marcado como leído.'),
                'type': 'info',
                'sticky': False,
            }
        }
    
    def eliminar(self):
        """Eliminar comentario (borrado lógico)"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Este comentario ya está eliminado.'))
        
        # Verificar que el usuario sea el emisor o tenga permisos
        # (Esto requiere verificación de permisos adicional)
        
        self.write({
            'activo': False
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Comentario Eliminado'),
                'message': _('El comentario ha sido eliminado correctamente.'),
                'type': 'warning',
                'sticky': False,
            }
        }
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    def _notificar_nuevo_comentario(self):
        """Notificar al receptor sobre el nuevo comentario"""
        self.ensure_one()
        try:
            # Cuerpo del mensaje
            body = _(
                "¡Tienes un nuevo comentario en tu artículo <b>%s</b>!<br/><br/>"
                "<b>%s:</b> %s"
            ) % (self.id_articulo.nombre, self.id_emisor.name, self.texto)
            
            # Postear mensaje en el artículo para que el propietario reciba la notificación (si está siguiendo)
            self.id_articulo.message_post(
                body=body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
            
            # También notificar al receptor directamente
            self.id_receptor.message_post(
                body=body,
                message_type='notification'
            )
        except Exception as e:
            # Importar logger si no está disponible, aunque debería estar en el nivel de módulo
            from odoo import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Error al enviar notificación de comentario: %s", str(e))
    
    def action_ver_articulo(self):
        """Abrir el artículo relacionado"""
        self.ensure_one()
        return {
            'name': _('Artículo'),
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.article',
            'view_mode': 'form',
            'res_id': self.id_articulo.id,
            'target': 'current',
        }
    
    def action_responder(self):
        """Crear un nuevo comentario como respuesta"""
        self.ensure_one()
        return {
            'name': _('Responder Comentario'),
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.comment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_id_articulo': self.id_articulo.id,
                'default_id_receptor': self.id_emisor.id,
                # El emisor será el usuario actual
            }
        }