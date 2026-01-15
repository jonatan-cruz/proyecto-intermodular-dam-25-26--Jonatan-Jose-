# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ChatSegundaMano(models.Model):
    _name = 'second_market.chat'
    _description = 'Chat de Conversación sobre Artículo'
    _order = 'fecha_ultimo_mensaje desc, id desc'
    
    # ============================================
    # CAMPOS BÁSICOS
    # ============================================
    
    id_articulo = fields.Many2one(
        'second_market.article',
        string='Artículo',
        required=True,
        ondelete='cascade',
        help='Artículo sobre el que se conversa'
    )
    
    id_comprador = fields.Many2one(
        'res.partner',
        string='Comprador Interesado',
        required=True,
        ondelete='cascade',
        help='Usuario interesado en el artículo'
    )
    
    id_vendedor = fields.Many2one(
        'res.partner',
        string='Vendedor',
        related='id_articulo.id_propietario',
        store=True,
        readonly=True,
        help='Propietario del artículo'
    )
    
    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, el chat está archivado'
    )
    
    # ============================================
    # MENSAJES
    # ============================================
    
    ids_mensajes = fields.One2many(
        'second_market.message',
        'id_chat',
        string='Mensajes'
    )
    
    conteo_mensajes = fields.Integer(
        string='Número de Mensajes',
        compute='_compute_conteo_mensajes',
        store=True
    )
    
    ultimo_mensaje = fields.Char(
        string='Último Mensaje',
        compute='_compute_ultimo_mensaje',
        store=True
    )
    
    fecha_ultimo_mensaje = fields.Datetime(
        string='Fecha Último Mensaje',
        compute='_compute_ultimo_mensaje',
        store=True
    )
    
    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================
    
    @api.depends('ids_mensajes')
    def _compute_conteo_mensajes(self):
        for chat in self:
            chat.conteo_mensajes = len(chat.ids_mensajes)
    
    @api.depends('ids_mensajes.fecha_envio', 'ids_mensajes.contenido')
    def _compute_ultimo_mensaje(self):
        for chat in self:
            if chat.ids_mensajes:
                # Obtener el mensaje más reciente
                ultimo = chat.ids_mensajes.sorted('fecha_envio', reverse=True)[0]
                chat.ultimo_mensaje = ultimo.contenido[:50] + '...' if len(ultimo.contenido) > 50 else ultimo.contenido
                chat.fecha_ultimo_mensaje = ultimo.fecha_envio
            else:
                chat.ultimo_mensaje = _('Sin mensajes')
                chat.fecha_ultimo_mensaje = False
    
    # ============================================
    # CONSTRAINTS
    # ============================================
    
    @api.constrains('id_articulo', 'id_comprador')
    def _check_chat_unico(self):
        """Evitar chats duplicados para el mismo artículo y comprador"""
        for chat in self:
            domain = [
                ('id_articulo', '=', chat.id_articulo.id),
                ('id_comprador', '=', chat.id_comprador.id),
                ('id', '!=', chat.id)
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_(
                    'Ya existe un chat entre este comprador y vendedor para este artículo.'
                ))
    
    @api.constrains('id_comprador', 'id_articulo')
    def _check_comprador_no_es_vendedor(self):
        """El comprador no puede ser el propietario del artículo"""
        for chat in self:
            if chat.id_comprador == chat.id_articulo.id_propietario:
                raise ValidationError(_(
                    'No puedes crear un chat contigo mismo. El comprador debe ser diferente al vendedor.'
                ))
    
    # ============================================
    # MÉTODOS
    # ============================================
    
    def name_get(self):
        """Mostrar nombre descriptivo del chat"""
        result = []
        for chat in self:
            name = _('Chat: %s - %s ↔ %s') % (
                chat.id_articulo.nombre,
                chat.id_comprador.name,
                chat.id_vendedor.name
            )
            result.append((chat.id, name))
        return result
    
    _sql_constraints = [
        (
            'unique_chat_articulo_comprador',
            'unique(id_articulo, id_comprador)',
            'Ya existe un chat para este artículo con este comprador.'
        )
    ]
