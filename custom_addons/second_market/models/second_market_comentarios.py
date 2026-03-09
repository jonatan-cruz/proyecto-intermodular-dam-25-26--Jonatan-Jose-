# -*- coding: utf-8 -*-

"""
Módulo de gestión de comentarios entre usuarios.

Define el modelo :class:`SecondMarketComment` que representa los comentarios
que los usuarios pueden enviarse mutuamente sobre un artículo en la
plataforma Second Market.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class SecondMarketComment(models.Model):
    """Modelo que representa un comentario de un usuario sobre un artículo.

    Los comentarios están asociados a un artículo concreto y tienen un
    emisor y un receptor. Admiten marcado de lectura y borrado lógico.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _inherit: Mixins heredados para chatter y actividades.
    :cvar _order: Ordenación por fecha de envío (más reciente primero).
    """

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
        """Validar que el emisor y el receptor no sean el mismo usuario.

        :raises ValidationError: Si ``id_emisor`` e ``id_receptor`` son el mismo usuario.
        """
        for comentario in self:
            if comentario.id_emisor == comentario.id_receptor:
                raise ValidationError(_('El emisor y el receptor no pueden ser el mismo usuario.'))

    @api.constrains('texto')
    def _check_texto(self):
        """Validar que el texto del comentario no esté vacío y no supere 500 caracteres.

        :raises ValidationError: Si el texto está vacío o supera los 500 caracteres.
        """
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
        """Crear uno o varios comentarios generando el ID único de cada uno.

        Asigna un código secuencial desde la secuencia ``second_market.comment``
        y notifica al receptor sobre el nuevo comentario.

        :param vals_list: Lista de diccionarios con los valores de cada comentario.
        :type vals_list: list[dict]
        :return: Recordset con los comentarios creados.
        :rtype: second_market.comment
        """
        for vals in vals_list:
            if vals.get('id_mensaje', _('Nuevo')) == _('Nuevo'):
                vals['id_mensaje'] = self.env['ir.sequence'].next_by_code('second_market.comment') or _('Nuevo')

        comentarios = super(SecondMarketComment, self).create(vals_list)
        for comentario in comentarios:
            comentario._notificar_nuevo_comentario()
        return comentarios

    def write(self, vals):
        """Actualizar un comentario registrando la fecha de lectura si se marca como leído.

        Si se establece ``leido = True`` y el comentario no estaba leído,
        se asigna automáticamente ``fecha_lectura`` con la fecha y hora actuales.

        :param vals: Diccionario con los campos a actualizar.
        :type vals: dict
        :return: Resultado de la operación de escritura.
        :rtype: bool
        """
        if 'leido' in vals and vals['leido'] and not self.leido:
            vals['fecha_lectura'] = fields.Datetime.now()
        return super(SecondMarketComment, self).write(vals)

    # ============================================
    # MÉTODOS PRINCIPALES
    # ============================================

    def enviar(self):
        """Enviar el comentario actualizando su fecha de envío y notificando al receptor.

        :raises UserError: Si el comentario está eliminado o ya fue enviado y leído.
        :return: Notificación de éxito en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('No puedes enviar un comentario eliminado.'))
        if self.leido:
            raise UserError(_('Este comentario ya ha sido enviado y leído.'))

        self.write({'fecha_hora': fields.Datetime.now()})
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
        """Marcar el comentario como leído registrando la fecha de lectura.

        :raises UserError: Si el comentario ya estaba marcado como leído.
        :return: Notificación informativa en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if self.leido:
            raise UserError(_('Este comentario ya fue marcado como leído.'))

        self.write({'leido': True, 'fecha_lectura': fields.Datetime.now()})

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
        """Realizar un borrado lógico del comentario (``activo = False``).

        :raises UserError: Si el comentario ya estaba eliminado.
        :return: Notificación de advertencia en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Este comentario ya está eliminado.'))

        self.write({'activo': False})

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
        """Notificar al receptor sobre el nuevo comentario publicado en el artículo.

        Publica un mensaje en el chatter del artículo (para que el propietario lo
        reciba si está suscrito) y también notifica directamente al receptor.

        :raises Exception: Capturada internamente; registra el error en el log
            sin interrumpir el flujo principal.
        """
        self.ensure_one()
        try:
            body = _(
                "¡Tienes un nuevo comentario en tu artículo <b>%s</b>!<br/><br/>"
                "<b>%s:</b> %s"
            ) % (self.id_articulo.nombre, self.id_emisor.name, self.texto)

            self.id_articulo.message_post(
                body=body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
            self.id_receptor.message_post(
                body=body,
                message_type='notification'
            )
        except Exception as e:
            from odoo import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Error al enviar notificación de comentario: %s", str(e))

    def action_ver_articulo(self):
        """Abrir el formulario del artículo relacionado con el comentario.

        :return: Acción de ventana para abrir el artículo en modo formulario.
        :rtype: dict
        """
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
        """Abrir un formulario para crear un nuevo comentario como respuesta.

        Pre-rellena el artículo y el receptor (el emisor original) en el contexto.

        :return: Acción de ventana para crear un comentario de respuesta.
        :rtype: dict
        """
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
            }
        }