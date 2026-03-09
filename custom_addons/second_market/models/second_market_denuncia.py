# -*- coding: utf-8 -*-

"""
Módulo de gestión de denuncias y reportes.

Define el modelo :class:`Denuncia` que permite a los usuarios de la plataforma
Second Market reportar contenido inapropiado (artículos, comentarios o usuarios)
para que los moderadores puedan revisarlo y tomar las acciones oportunas.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class Denuncia(models.Model):
    """Modelo que representa una denuncia o reporte dentro de la plataforma.

    Una denuncia puede estar dirigida a un artículo, un comentario o un usuario.
    El ciclo de vida de la denuncia va desde ``pendiente`` hasta ``resuelta``,
    ``rechazada`` o ``cerrada``, gestionado por un moderador.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _inherit: Mixins heredados para chatter y actividades.
    :cvar _order: Ordenación por fecha de creación (más reciente primero).
    :cvar _rec_name: Campo usado como nombre representativo del registro.
    """

    _name = 'second_market.report'
    _description = 'Denuncia/Reporte de Artículo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'num_denuncia'

    # ============================================
    # CAMPOS BÁSICOS
    # ============================================

    num_denuncia = fields.Char(
        string='Número de Denuncia',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('REP-0000X'),
        help='Identificador único de la denuncia'
    )

    motivo = fields.Selection([
        ('contenido_inapropiado', 'Contenido Inapropiado'),
        ('spam', 'Spam o Publicidad'),
        ('informacion_falsa', 'Información Falsa o Engañosa'),
        ('precio_sospechoso', 'Precio Sospechoso'),
        ('producto_prohibido', 'Producto Prohibido'),
        ('acoso', 'Acoso o Abuso'),
        ('otro', 'Otro')
    ],
        string='Motivo',
        required=True,
        tracking=True,
        help='Razón de la denuncia'
    )

    descripcion = fields.Text(
        string='Descripción',
        required=True,
        tracking=True,
        help='Detalle de la denuncia (máx 500 caracteres)'
    )

    # ============================================
    # RELACIONES - ¿SOBRE QUÉ ES LA DENUNCIA?
    # ============================================

    tipo_denuncia = fields.Selection([
        ('articulo', 'Artículo'),
        ('comentario', 'Comentario'),
        ('usuario', 'Usuario')
    ],
        string='Tipo de Denuncia',
        required=True,
        default='articulo',
        help='Indica si la denuncia es sobre un artículo, un comentario o un usuario'
    )

    id_usuario_denunciado = fields.Many2one(
        'second_market.user',
        string='Usuario Denunciado',
        ondelete='cascade',
        tracking=True,
        help='Usuario sobre el que se realiza la denuncia'
    )

    id_comentario = fields.Many2one(
        'second_market.comment',
        string='Comentario Denunciado',
        ondelete='cascade',
        tracking=True,
        help='Comentario sobre el que se realiza la denuncia'
    )

    id_articulo = fields.Many2one(
        'second_market.article',
        string='Artículo Denunciado',
        ondelete='cascade',
        tracking=True,
        help='Artículo sobre el que se realiza la denuncia'
    )

    # ============================================
    # RELACIONES - USUARIOS
    # ============================================

    id_denunciante = fields.Many2one(
        'second_market.user',
        string='Denunciante',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Usuario de la app que realiza la denuncia'
    )

    id_moderador = fields.Many2one(
        'res.users',
        string='Moderador Asignado',
        ondelete='set null',
        tracking=True,
        help='Empleado o moderador que gestiona la denuncia'
    )

    # ============================================
    # ESTADO Y RESOLUCIÓN
    # ============================================

    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En Revisión'),
        ('resuelta', 'Resuelta'),
        ('rechazada', 'Rechazada'),
        ('cerrada', 'Cerrada')
    ],
        string='Estado',
        default='pendiente',
        required=True,
        tracking=True,
        help='Estado actual de la denuncia'
    )

    fecha_resolucion = fields.Datetime(
        string='Fecha de Resolución',
        readonly=True,
        tracking=True,
        help='Fecha en que se resolvió o rechazó la denuncia'
    )

    resolucion = fields.Text(
        string='Resolución',
        tracking=True,
        help='Descripción de la resolución tomada'
    )

    accion_tomada = fields.Selection([
        ('ninguna', 'Ninguna'),
        ('advertencia', 'Advertencia al Usuario'),
        ('eliminado_contenido', 'Contenido Eliminado'),
        ('suspendido_usuario', 'Usuario Suspendido'),
        ('bloqueado_usuario', 'Usuario Bloqueado'),
        ('otra', 'Otra Acción')
    ],
        string='Acción Tomada',
        default='ninguna',
        tracking=True,
        help='Acción aplicada tras revisar la denuncia'
    )

    # ============================================
    # CAMPOS ADICIONALES
    # ============================================

    prioridad = fields.Selection([
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente')
    ],
        string='Prioridad',
        default='media',
        tracking=True,
        help='Prioridad de la denuncia'
    )

    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, la denuncia está archivada'
    )

    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================

    nombre_denunciado = fields.Char(
        string='Usuario Denunciado',
        compute='_computar_nombre_denunciado',
        store=True,
        help='Propietario del artículo o autor del comentario denunciado'
    )

    @api.depends('id_articulo', 'id_comentario', 'id_usuario_denunciado', 'tipo_denuncia')
    def _computar_nombre_denunciado(self):
        """Calcular el nombre del usuario denunciado según el tipo de denuncia.

        - Si ``tipo_denuncia == 'articulo'``: obtiene el propietario del artículo.
        - Si ``tipo_denuncia == 'comentario'``: obtiene el emisor del comentario.
        - Si ``tipo_denuncia == 'usuario'``: obtiene directamente el usuario denunciado.

        Almacena el resultado en :attr:`nombre_denunciado`.
        """
        for denuncia in self:
            nombre = False

            if denuncia.tipo_denuncia == 'articulo' and denuncia.id_articulo:
                propietario = denuncia.id_articulo.id_propietario
                nombre = propietario.name or str(propietario.id) if propietario else 'Usuario eliminado'
            elif denuncia.tipo_denuncia == 'comentario' and denuncia.id_comentario:
                nombre = denuncia.id_comentario.id_emisor.name if denuncia.id_comentario.id_emisor else 'Por implementar'
            elif denuncia.tipo_denuncia == 'usuario' and denuncia.id_usuario_denunciado:
                nombre = denuncia.id_usuario_denunciado.name

            denuncia.nombre_denunciado = nombre

    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================

    @api.constrains('id_articulo', 'id_comentario', 'id_usuario_denunciado', 'tipo_denuncia')
    def _check_tipo_denuncia(self):
        """Verificar que la denuncia tenga el elemento relacionado según su tipo.

        :raises ValidationError: Si el tipo es ``'articulo'`` y no hay artículo,
            si el tipo es ``'comentario'`` y no hay comentario, o si el tipo
            es ``'usuario'`` y no hay usuario denunciado.
        """
        for denuncia in self:
            if denuncia.tipo_denuncia == 'articulo' and not denuncia.id_articulo:
                raise ValidationError(_('Debes seleccionar un artículo para denunciar.'))
            if denuncia.tipo_denuncia == 'comentario' and not denuncia.id_comentario:
                raise ValidationError(_('Debes seleccionar un comentario para denunciar.'))
            if denuncia.tipo_denuncia == 'usuario' and not denuncia.id_usuario_denunciado:
                raise ValidationError(_('Debes seleccionar un usuario para denunciar.'))

    @api.constrains('descripcion')
    def _check_descripcion_length(self):
        """Validar que la descripción de la denuncia no supere 500 caracteres.

        :raises ValidationError: Si la descripción tiene más de 500 caracteres.
        """
        for denuncia in self:
            if denuncia.descripcion and len(denuncia.descripcion) > 500:
                raise ValidationError(_('La descripción no puede tener más de 500 caracteres.'))

    @api.constrains('id_denunciante', 'id_articulo')
    def _check_no_auto_denuncia_articulo(self):
        """Evitar que un usuario denuncie su propio artículo.

        :raises ValidationError: Si el denunciante es el propietario del artículo.
        """
        for denuncia in self:
            if denuncia.id_articulo and denuncia.id_denunciante:
                if denuncia.id_denunciante.id == denuncia.id_articulo.id_propietario.id:
                    raise ValidationError(_('No puedes denunciar tu propio artículo.'))

    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================

    @api.model_create_multi
    def create(self, vals_list):
        """Crear una o varias denuncias generando el número único de cada una.

        Asigna un código desde la secuencia ``second_market.report`` y
        notifica a los moderadores sobre la nueva denuncia.

        :param vals_list: Lista de diccionarios con los valores de cada denuncia.
        :type vals_list: list[dict]
        :return: Recordset con las denuncias creadas.
        :rtype: second_market.report
        """
        for vals in vals_list:
            if vals.get('num_denuncia', _('Nueva')) == _('Nueva'):
                vals['num_denuncia'] = self.env['ir.sequence'].next_by_code('second_market.report') or _('Nueva')

        denuncias = super(Denuncia, self).create(vals_list)
        for denuncia in denuncias:
            denuncia._notificar_nueva_denuncia()
        return denuncias

    def write(self, vals):
        """Actualizar la denuncia registrando la fecha de resolución si cambia el estado.

        Si el nuevo estado es ``'resuelta'``, ``'rechazada'`` o ``'cerrada'``,
        se asigna automáticamente ``fecha_resolucion`` con la fecha y hora actuales.
        Además notifica al denunciante sobre el cambio de estado.

        :param vals: Diccionario con los campos a actualizar.
        :type vals: dict
        :return: Resultado de la operación de escritura.
        :rtype: bool
        """
        if 'estado' in vals:
            if vals['estado'] in ['resuelta', 'rechazada', 'cerrada']:
                vals['fecha_resolucion'] = fields.Datetime.now()

        result = super(Denuncia, self).write(vals)

        if 'estado' in vals:
            self._notificar_cambio_estado()

        return result

    # ============================================
    # MÉTODOS DE ACCIÓN
    # ============================================

    def accion_asignar_moderador(self):
        """Asignar el usuario actual como moderador de la denuncia y pasarla a revisión.

        :return: Notificación de éxito en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()
        self.write({'id_moderador': self.env.user, 'estado': 'en_revision'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Denuncia Asignada'),
                'message': _('Te has asignado esta denuncia.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def accion_resolver(self):
        """Marcar la denuncia como resuelta.

        :raises UserError: Si no se ha proporcionado una descripción de resolución.
        :return: Notificación de éxito en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()
        if not self.resolucion:
            raise UserError(_('Debes proporcionar una descripción de la resolución.'))
        self.write({'estado': 'resuelta'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Denuncia Resuelta'),
                'message': _('La denuncia ha sido marcada como resuelta.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def accion_rechazar(self):
        """Rechazar la denuncia indicando la razón en el campo de resolución.

        :raises UserError: Si no se ha proporcionado la razón del rechazo.
        :return: Notificación informativa en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()
        if not self.resolucion:
            raise UserError(_('Debes proporcionar una razón para rechazar la denuncia.'))
        self.write({'estado': 'rechazada'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Denuncia Rechazada'),
                'message': _('La denuncia ha sido rechazada.'),
                'type': 'info',
                'sticky': False,
            }
        }

    def accion_cerrar(self):
        """Cerrar la denuncia desactivándola.

        :return: ``True`` si la operación se realizó con éxito.
        :rtype: bool
        """
        self.ensure_one()
        self.write({'estado': 'cerrada', 'activo': False})
        return True

    def accion_ver_articulo(self):
        """Abrir el formulario del artículo denunciado.

        :raises UserError: Si la denuncia no está relacionada con un artículo.
        :return: Acción de ventana para abrir el artículo en modo formulario.
        :rtype: dict
        """
        self.ensure_one()
        if not self.id_articulo:
            raise UserError(_('Esta denuncia no está relacionada con un artículo.'))
        return {
            'name': _('Artículo Denunciado'),
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.article',
            'view_mode': 'form',
            'res_id': self.id_articulo.id,
            'target': 'current'
        }

    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================

    def _notificar_nueva_denuncia(self):
        """Publicar un mensaje en el chatter de la denuncia para alertar a los moderadores.

        El mensaje incluye el nombre del denunciante y el motivo de la denuncia.
        """
        self.ensure_one()
        self.message_post(
            body=_('Nueva denuncia creada por {}. Motivo: {}').format(
                self.id_denunciante.name,
                dict(self._fields['motivo'].selection).get(self.motivo)
            ),
            subject=_('Nueva Denuncia: {}').format(self.num_denuncia)
        )

    def _notificar_cambio_estado(self):
        """Notificar al denunciante sobre el cambio de estado de su denuncia.

        Publica un mensaje en el chatter de la denuncia con el nuevo estado
        para que el denunciante esté informado.
        """
        for denuncia in self:
            if denuncia.id_denunciante:
                denuncia.message_post(
                    body=_('El estado de la denuncia de {} ha cambiado a: {}').format(
                        denuncia.id_denunciante.name,
                        dict(self._fields['estado'].selection).get(denuncia.estado)
                    ),
                    subject=_('Actualización de Denuncia: {}').format(denuncia.num_denuncia)
                )
