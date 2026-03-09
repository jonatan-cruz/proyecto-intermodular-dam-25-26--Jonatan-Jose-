# -*- coding: utf-8 -*-

"""
Módulo de gestión de chats entre usuarios.

Define el modelo :class:`ChatSegundaMano` que representa las conversaciones
que se producen entre un comprador interesado y el vendedor de un artículo
en la plataforma Second Market.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ChatSegundaMano(models.Model):
    """Modelo que representa una conversación entre comprador y vendedor.

    Cada chat está vinculado a un artículo concreto y solo puede existir
    un chat por par (artículo, comprador). El vendedor se obtiene
    automáticamente del propietario del artículo.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _order: Ordenación por fecha del último mensaje (más reciente primero).
    """

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
        'second_market.user',
        string='Comprador Interesado',
        required=True,
        ondelete='cascade',
        help='Usuario interesado en el artículo'
    )

    id_vendedor = fields.Many2one(
        'second_market.user',
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
        """Calcular el número total de mensajes en el chat.

        Almacena el resultado en :attr:`conteo_mensajes`.
        """
        for chat in self:
            chat.conteo_mensajes = len(chat.ids_mensajes)

    @api.depends('ids_mensajes.fecha_envio', 'ids_mensajes.contenido')
    def _compute_ultimo_mensaje(self):
        """Obtener el contenido y fecha del mensaje más reciente del chat.

        Muestra un máximo de 50 caracteres del contenido. Si no hay mensajes,
        establece el texto "Sin mensajes" y ``fecha_ultimo_mensaje`` a ``False``.

        Almacena los resultados en :attr:`ultimo_mensaje` y
        :attr:`fecha_ultimo_mensaje`.
        """
        for chat in self:
            if chat.ids_mensajes:
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
        """Evitar chats duplicados para el mismo artículo y comprador.

        Solo puede existir un chat por combinación de ``id_articulo`` e
        ``id_comprador``.

        :raises ValidationError: Si ya existe un chat entre el comprador y
            el vendedor para el mismo artículo.
        """
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
        """Validar que el comprador no sea el propietario del artículo.

        Un usuario no puede iniciar un chat consigo mismo sobre su propio artículo.

        :raises ValidationError: Si el comprador es también el vendedor del artículo.
        """
        for chat in self:
            if chat.id_comprador == chat.id_articulo.id_propietario:
                raise ValidationError(_(
                    'No puedes crear un chat contigo mismo. El comprador debe ser diferente al vendedor.'
                ))

    # ============================================
    # MÉTODOS
    # ============================================

    def name_get(self):
        """Devolver el nombre representativo del chat para listas desplegables.

        El formato es: ``Chat: <artículo> - <comprador> ↔ <vendedor>``.

        :return: Lista de tuplas ``(id, nombre)`` para cada chat.
        :rtype: list[tuple[int, str]]
        """
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
