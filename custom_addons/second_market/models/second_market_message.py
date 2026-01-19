# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MensajeChat(models.Model):
    _name = 'second_market.message'
    _description = 'Mensaje de Chat'
    _order = 'fecha_envio asc'
    
    # ============================================
    # CAMPOS BÁSICOS
    # ============================================
    
    id_chat = fields.Many2one(
        'second_market.chat',
        string='Chat',
        required=True,
        ondelete='cascade',
        help='Chat al que pertenece este mensaje'
    )
    
    id_usuario = fields.Many2one(
        'second_market.user',
        string='Usuario',
        required=True,
        help='Usuario que envía el mensaje'
    )
    
    contenido = fields.Text(
        string='Mensaje',
        required=True,
        help='Contenido del mensaje (máximo 500 caracteres)'
    )
    
    fecha_envio = fields.Datetime(
        string='Fecha de Envío',
        default=fields.Datetime.now,
        readonly=True,
        help='Fecha y hora de envío del mensaje'
    )
    
    leido = fields.Boolean(
        string='Leído',
        default=False,
        help='Indica si el mensaje ha sido leído por el destinatario'
    )
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    @api.constrains('contenido')
    def _check_contenido_length(self):
        """Validar que el contenido no exceda 500 caracteres"""
        for mensaje in self:
            if mensaje.contenido and len(mensaje.contenido) > 500:
                raise ValidationError(_(
                    'El mensaje no puede tener más de 500 caracteres. '
                    'Actualmente tiene %d caracteres.'
                ) % len(mensaje.contenido))
    
    @api.constrains('contenido')
    def _check_contenido_no_vacio(self):
        """Validar que el contenido no esté vacío"""
        for mensaje in self:
            if not mensaje.contenido or not mensaje.contenido.strip():
                raise ValidationError(_('El mensaje no puede estar vacío.'))
    
    # ============================================
    # MÉTODOS
    # ============================================
    
    def name_get(self):
        """Mostrar preview del mensaje"""
        result = []
        for mensaje in self:
            preview = mensaje.contenido[:30] + '...' if len(mensaje.contenido) > 30 else mensaje.contenido
            name = _('%s: %s') % (mensaje.id_usuario.name, preview)
            result.append((mensaje.id, name))
        return result
    
    @api.model_create_multi
    def create(self, vals_list):
        """Al crear mensajes, el campo de último mensaje del chat se actualizará automáticamente"""
        mensajes = super(MensajeChat, self).create(vals_list)
        return mensajes
