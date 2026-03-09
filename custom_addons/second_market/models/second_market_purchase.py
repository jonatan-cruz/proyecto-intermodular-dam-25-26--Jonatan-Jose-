# -*- coding: utf-8 -*-

"""
Módulo de gestión de compras y transacciones.

Define el modelo :class:`SecondMarketPurchase` que registra las transacciones
de compra-venta entre usuarios de la plataforma Second Market, incluyendo
su ciclo de vida desde el estado pendiente hasta completado o cancelado.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SecondMarketPurchase(models.Model):
    """Modelo que representa una transacción de compra-venta.

    Gestiona el ciclo completo de una compra: desde que el comprador
    inicia la transacción (``pendiente``) hasta que se confirma
    (``confirmada``), se completa (``completada``) o se cancela
    (``cancelada``).

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _inherit: Mixins heredados para chatter y actividades.
    :cvar _rec_name: Campo usado como nombre representativo del registro.
    :cvar _order: Ordenación por fecha de transacción (más reciente primero).
    """

    _name = 'second_market.purchase'
    _description = 'Compra/Transacción'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'id_compra'
    _order = 'fecha_hora desc'

    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================

    id_compra = fields.Char(
        string='ID Compra',
        size=7,
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
        help='Código único de 7 dígitos para la compra'
    )

    id_comprador = fields.Many2one(
        'second_market.user',
        string='Comprador',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Usuario que compra el artículo'
    )

    id_vendedor = fields.Many2one(
        'second_market.user',
        string='Vendedor',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Usuario que vende el artículo'
    )

    id_articulo = fields.Many2one(
        'second_market.article',
        string='Artículo',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Artículo comprado'
    )

    fecha_hora = fields.Datetime(
        string='Fecha y Hora',
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        tracking=True,
        help='Fecha y hora de la transacción'
    )

    precio = fields.Float(
        string='Precio (€)',
        required=True,
        digits=(10, 2),
        tracking=True,
        help='Precio final de la compra'
    )

    # ============================================
    # CAMPOS DE ESTADO
    # ============================================

    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    ],
        string='Estado',
        default='pendiente',
        required=True,
        tracking=True
    )

    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, la compra está cancelada'
    )

    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================

    nombre_comprador = fields.Char(
        string='Comprador',
        related='id_comprador.name',
        store=True,
        readonly=True
    )

    nombre_vendedor = fields.Char(
        string='Vendedor',
        related='id_vendedor.name',
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

    @api.constrains('id_comprador', 'id_vendedor')
    def _check_comprador_vendedor(self):
        """Validar que el comprador y el vendedor sean usuarios distintos.

        :raises ValidationError: Si el comprador y el vendedor son el mismo usuario.
        """
        for compra in self:
            if compra.id_comprador == compra.id_vendedor:
                raise ValidationError(_('El comprador y el vendedor no pueden ser el mismo usuario.'))

    @api.constrains('precio')
    def _check_precio(self):
        """Validar que el precio de la compra sea mayor que 0.

        :raises ValidationError: Si el precio es 0 o negativo.
        """
        for compra in self:
            if compra.precio <= 0:
                raise ValidationError(_('El precio debe ser mayor que 0.'))

    @api.constrains('id_articulo', 'id_vendedor')
    def _check_vendedor_articulo(self):
        """Validar que el vendedor sea el propietario del artículo.

        :raises ValidationError: Si el ``id_vendedor`` no coincide con el
            ``id_propietario`` del artículo.
        """
        for compra in self:
            if compra.id_articulo.id_propietario != compra.id_vendedor:
                raise ValidationError(_('El vendedor debe ser el propietario del artículo.'))

    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================

    @api.model
    def create(self, vals):
        """Crear una nueva compra generando su ID único.

        Asigna un código secuencial de 7 dígitos desde la secuencia
        ``second_market.purchase`` y notifica a comprador y vendedor.

        :param vals: Diccionario con los valores del nuevo registro.
        :type vals: dict
        :return: Registro de compra creado.
        :rtype: second_market.purchase
        """
        if vals.get('id_compra', _('Nuevo')) == _('Nuevo'):
            vals['id_compra'] = self.env['ir.sequence'].next_by_code('second_market.purchase') or _('Nuevo')

        compra = super(SecondMarketPurchase, self).create(vals)
        compra._notificar_nueva_compra()
        return compra

    # ============================================
    # MÉTODOS PRINCIPALES
    # ============================================

    def realizar_compra(self):
        """Confirmar la compra y reservar el artículo.

        Cambia el estado de la compra a ``confirmada`` y el estado de
        publicación del artículo a ``reservado``.

        :raises UserError: Si la compra está cancelada, ya fue procesada
            o el artículo no está disponible.
        :return: Notificación de éxito en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Esta compra está cancelada.'))
        if self.estado != 'pendiente':
            raise UserError(_('Esta compra ya ha sido procesada.'))
        if self.id_articulo.estado_publicacion != 'publicado':
            raise UserError(_('El artículo ya no está disponible (Estado: %s).') % self.id_articulo.estado_publicacion)

        self.write({'estado': 'confirmada'})
        self.id_articulo.write({'estado_publicacion': 'reservado'})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Compra Confirmada!'),
                'message': _('La compra ha sido confirmada. El artículo ha quedado reservado.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def confirmar_transaccion(self):
        """Marcar la transacción como completada y el artículo como vendido.

        Cambia el estado de la compra a ``completada`` y el del artículo
        a ``vendido``. Notifica a las partes implicadas.

        :raises UserError: Si la compra está cancelada o ya está completada.
        :return: Notificación de éxito en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Esta compra está cancelada.'))
        if self.estado == 'completada':
            raise UserError(_('Esta transacción ya está completada.'))

        self.write({'estado': 'completada'})
        self.id_articulo.write({'estado_publicacion': 'vendido'})
        self._notificar_transaccion_completada()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Transacción Completada!'),
                'message': _('La venta se ha completado exitosamente.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def cancelar_compra(self):
        """Cancelar la compra y volver a publicar el artículo si estaba reservado.

        Cambia el estado de la compra a ``cancelada`` y la desactiva.
        Si el artículo estaba en estado ``reservado``, lo vuelve a ``publicado``.

        :raises UserError: Si la transacción ya estaba completada.
        :return: Notificación de advertencia en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if self.estado == 'completada':
            raise UserError(_('No puedes cancelar una transacción completada.'))

        self.write({'estado': 'cancelada', 'activo': False})

        if self.id_articulo.estado_publicacion == 'reservado':
            self.id_articulo.write({'estado_publicacion': 'publicado'})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Compra Cancelada'),
                'message': _('La compra ha sido cancelada.'),
                'type': 'warning',
                'sticky': False,
            }
        }

    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================

    def _notificar_nueva_compra(self):
        """Enviar notificación a comprador, vendedor y artículo al crear la compra.

        Publica un mensaje en el chatter del artículo, del vendedor y del
        comprador con los detalles de la nueva transacción.
        """
        self.ensure_one()
        mensaje = _(
            "¡Nueva compra realizada!<br/>"
            "El usuario <b>%s</b> ha comprado el artículo <b>%s</b> por <b>%.2f€</b>.<br/>"
            "Estado actual: <b>%s</b>."
        ) % (self.id_comprador.name, self.id_articulo.nombre, self.precio, self.estado)

        self.id_articulo.message_post(body=mensaje, message_type='notification')
        self.id_vendedor.message_post(body=mensaje, message_type='notification')
        self.id_comprador.message_post(body=mensaje, message_type='notification')

    def _notificar_transaccion_completada(self):
        """Publicar una nota interna indicando que la transacción se completó.

        Utiliza el subtipo ``mail.mt_note`` para que la notificación quede
        como nota interna en el chatter de la compra.
        """
        self.ensure_one()
        mensaje = _("Transacción completada exitosamente el %s.") % fields.Datetime.now()
        self.message_post(body=mensaje, subtype_xmlid='mail.mt_note')

    def action_ver_articulo(self):
        """Abrir el formulario del artículo relacionado.

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

    def action_ver_comprador(self):
        """Abrir el formulario del perfil del comprador.

        :return: Acción de ventana para abrir el usuario comprador en modo formulario.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': _('Comprador'),
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.user',
            'view_mode': 'form',
            'res_id': self.id_comprador.id,
            'target': 'current',
        }

    def action_ver_vendedor(self):
        """Abrir el formulario del perfil del vendedor.

        :return: Acción de ventana para abrir el usuario vendedor en modo formulario.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': _('Vendedor'),
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.user',
            'view_mode': 'form',
            'res_id': self.id_vendedor.id,
            'target': 'current',
        }