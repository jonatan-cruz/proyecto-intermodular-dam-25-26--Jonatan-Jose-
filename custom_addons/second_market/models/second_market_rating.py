# -*- coding: utf-8 -*-

"""
Módulo de gestión de valoraciones de usuarios.

Define el modelo :class:`SecondMarketRating` que permite a los usuarios
calificarse mutuamente tras completar una transacción en la plataforma
Second Market.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SecondMarketRating(models.Model):
    """Modelo que representa una valoración entre usuarios.

    Permite que un usuario (valorador) asigne una calificación del 1 al 5
    a otro usuario (valorado). Cada par valorador-valorado solo puede tener
    una valoración activa.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _inherit: Mixins heredados para chatter y actividades.
    :cvar _order: Ordenación por fecha de valoración (más reciente primero).
    """

    _name = 'second_market.rating'
    _description = 'Valoración de Usuario'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_hora desc'

    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================

    calificacion = fields.Selection(
        selection=[
            ('0', '0'),
            ('1', '1'),
            ('2', '2'),
            ('3', '3'),
            ('4', '4'),
            ('5', '5'),
        ],
        string='Calificación',
        required=True,
        default='1',
        help='Calificación del 1 al 5',
        tracking=True,
    )

    id_usuario = fields.Many2one(
        'second_market.user',
        string='Usuario Valorado',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Usuario que recibe la valoración'
    )

    id_valorador = fields.Many2one(
        'second_market.user',
        string='Valorador',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Usuario que realiza la valoración'
    )

    comentario = fields.Text(
        string='Comentario',
        size=300,
        help='Comentario opcional sobre la valoración (máx 300 caracteres)'
    )

    fecha_hora = fields.Datetime(
        string='Fecha y Hora',
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        tracking=True
    )

    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================

    nombre_usuario = fields.Char(
        string='Usuario',
        related='id_usuario.name',
        store=True,
        readonly=True
    )

    nombre_valorador = fields.Char(
        string='Valorado por',
        related='id_valorador.name',
        store=True,
        readonly=True
    )

    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, la valoración está eliminada'
    )

    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================

    @api.constrains('calificacion')
    def _check_calificacion(self):
        """Validar que la calificación esté en el rango permitido (1-5).

        :raises ValidationError: Si la calificación es 0 o superior a 5.
        """
        for valoracion in self:
            cal = int(valoracion.calificacion)
            if cal < 1 or cal > 5:
                raise ValidationError(_('La calificación debe estar entre 1 y 5 estrellas.'))

    @api.constrains('id_usuario', 'id_valorador')
    def _check_autovaloracion(self):
        """Validar que un usuario no pueda valorarse a sí mismo.

        :raises ValidationError: Si ``id_usuario`` e ``id_valorador`` son el mismo.
        """
        for valoracion in self:
            if valoracion.id_usuario == valoracion.id_valorador:
                raise ValidationError(_('No puedes valorarte a ti mismo.'))

    @api.constrains('comentario')
    def _check_comentario_length(self):
        """Validar que el comentario de la valoración no supere 300 caracteres.

        :raises ValidationError: Si el comentario tiene más de 300 caracteres.
        """
        for valoracion in self:
            if valoracion.comentario and len(valoracion.comentario) > 300:
                raise ValidationError(_('El comentario no puede tener más de 300 caracteres.'))

    @api.constrains('id_usuario', 'id_valorador')
    def _check_valoracion_unica(self):
        """Validar que no exista ya una valoración activa del mismo par valorador-valorado.

        :raises ValidationError: Si el valorador ya calificó previamente al usuario
            y la valoración sigue activa.
        """
        for valoracion in self:
            duplicados = self.search([
                ('id_usuario', '=', valoracion.id_usuario.id),
                ('id_valorador', '=', valoracion.id_valorador.id),
                ('id', '!=', valoracion.id),
                ('activo', '=', True)
            ])
            if duplicados:
                raise ValidationError(_('Ya has valorado a este usuario anteriormente.'))

    # ============================================
    # MÉTODOS
    # ============================================

    @api.model
    def create(self, vals):
        """Crear una valoración y notificar al usuario valorado.

        :param vals: Diccionario con los valores del nuevo registro.
        :type vals: dict
        :return: Registro de valoración creado.
        :rtype: second_market.rating
        """
        valoracion = super(SecondMarketRating, self).create(vals)
        valoracion._notificar_nueva_valoracion()
        return valoracion

    def asignar_calificacion(self, calificacion_nueva):
        """Actualizar la calificación de una valoración existente.

        :param calificacion_nueva: Nueva calificación a asignar (valor de selección '1'-'5').
        :type calificacion_nueva: str
        :raises UserError: Si la valoración está eliminada (``activo = False``).
        :return: Notificación de éxito en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Esta valoración está eliminada.'))

        self.write({'calificacion': calificacion_nueva})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Calificación Actualizada'),
                'message': _('La calificación se ha actualizado correctamente.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def obtener_promedio(self):
        """Placeholder para obtener el promedio de calificaciones de un usuario.

        .. note::
            Este método delega la lógica al campo computado
            ``_computar_calificacion_promedio`` del modelo ``second_market.user``.
            Ver :meth:`~second_market.user.SecondMarketUser._computar_calificacion_promedio`.
        """
        pass

    def _notificar_nueva_valoracion(self):
        """Notificar al usuario valorado sobre la nueva calificación recibida.

        .. todo::
            Implementar el envío de notificación al usuario valorado.
        """
        self.ensure_one()
        pass