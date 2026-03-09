# -*- coding: utf-8 -*-

"""
Módulo de gestión de mensajes de chat.

Define el modelo :class:`MensajeChat` que almacena los mensajes individuales
dentro de una conversación entre usuarios de la plataforma Second Market.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MensajeChat(models.Model):
    """Modelo que representa un mensaje dentro de un chat.

    Los mensajes aparecen ordenados cronológicamente (más antiguo primero)
    dentro del chat al que pertenecen. Cada mensaje tiene un límite de
    500 caracteres.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _order: Orden cronológico ascendente por fecha de envío.
    """

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
        """Validar que el contenido del mensaje no supere 500 caracteres.

        :raises ValidationError: Si el mensaje supera los 500 caracteres,
            indicando el número actual de caracteres.
        """
        for mensaje in self:
            if mensaje.contenido and len(mensaje.contenido) > 500:
                raise ValidationError(_(
                    'El mensaje no puede tener más de 500 caracteres. '
                    'Actualmente tiene %d caracteres.'
                ) % len(mensaje.contenido))

    @api.constrains('contenido')
    def _check_contenido_no_vacio(self):
        """Validar que el mensaje no esté vacío ni contenga solo espacios.

        :raises ValidationError: Si el contenido está vacío o es solo espacios en blanco.
        """
        for mensaje in self:
            if not mensaje.contenido or not mensaje.contenido.strip():
                raise ValidationError(_('El mensaje no puede estar vacío.'))

    # ============================================
    # MÉTODOS
    # ============================================

    def name_get(self):
        """Devolver un preview del mensaje para listas desplegables.

        Muestra el nombre del usuario seguido de los primeros 30 caracteres
        del contenido del mensaje.

        :return: Lista de tuplas ``(id, nombre)`` para cada mensaje.
        :rtype: list[tuple[int, str]]
        """
        result = []
        for mensaje in self:
            preview = mensaje.contenido[:30] + '...' if len(mensaje.contenido) > 30 else mensaje.contenido
            name = _('%s: %s') % (mensaje.id_usuario.name, preview)
            result.append((mensaje.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Crear uno o varios mensajes de chat.

        Al crear mensajes, los campos computados del chat relacionado
        (``ultimo_mensaje``, ``fecha_ultimo_mensaje``) se actualizan
        automáticamente gracias al mecanismo ``@api.depends`` de Odoo.

        :param vals_list: Lista de diccionarios con los valores de cada mensaje.
        :type vals_list: list[dict]
        :return: Recordset con los mensajes creados.
        :rtype: second_market.message
        """
        mensajes = super(MensajeChat, self).create(vals_list)
        return mensajes
