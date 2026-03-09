# -*- coding: utf-8 -*-

"""
Módulo de gestión de usuarios de la plataforma.

Define el modelo :class:`SecondMarketUser` que representa a los usuarios
registrados en Second Market. Gestiona autenticación, estadísticas del usuario,
ciclo de vida de sus artículos y valoraciones recibidas.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import re
from passlib.context import CryptContext

#: Contexto de hashing de contraseñas usando el estándar de Odoo (PBKDF2-SHA512).
crypt_context = CryptContext(schemes=["pbkdf2_sha512", "plaintext"], deprecated="auto")


class SecondMarketUser(models.Model):
    """Modelo que representa un usuario de la plataforma Second Market.

    Extiende ``mail.thread`` y ``mail.activity.mixin`` para soporte de chatter
    y actividades. Gestiona el cifrado de contraseñas con PBKDF2-SHA512,
    la generación de IDs únicos y las estadísticas derivadas de las relaciones
    con artículos, compras y valoraciones.

    :cvar _name: Nombre técnico del modelo en Odoo.
    :cvar _description: Descripción legible del modelo.
    :cvar _inherit: Mixins heredados para chatter y actividades.
    :cvar _order: Ordenación por fecha de registro (más reciente primero).
    """

    _name = 'second_market.user'
    _description = 'Usuario de Second Market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================

    id_usuario = fields.Char(
        string='ID Usuario',
        size=7,
        required=True,
        copy=False,
        help='ID único de usuario de 7 dígitos'
    )

    name = fields.Char(
        string='Nombre',
        size=50,
        required=True,
        tracking=True,
        help='Nombre del usuario (máx 50 caracteres)'
    )

    password = fields.Char(
        string='Contraseña',
        required=True,
        password=True,
        help='Contraseña (8-50 caracteres)'
    )

    login = fields.Char(
        string='Login/Email',
        required=True,
        tracking=True,
        help='Email o nombre de usuario para iniciar sesión'
    )

    # ============================================
    # ESTADÍSTICAS DEL USUARIO
    # ============================================

    productos_en_venta = fields.Integer(
        string='Productos en Venta',
        compute='_computar_productos_en_venta',
        store=True,
        help='Número de productos actualmente en venta'
    )

    productos_vendidos = fields.Integer(
        string='Productos Vendidos',
        compute='_computar_productos_vendidos',
        store=True,
        help='Total de productos vendidos'
    )

    productos_comprados = fields.Integer(
        string='Productos Comprados',
        compute='_computar_productos_comprados',
        store=True,
        help='Total de productos comprados'
    )

    antiguedad = fields.Integer(
        string='Antigüedad (años)',
        compute='_computar_antiguedad',
        store=True,
        help='Años desde el registro del usuario'
    )

    @api.constrains('id_usuario')
    def _check_id_usuario(self):
        """Validar que el ID de usuario tenga exactamente 7 dígitos numéricos.

        :raises ValidationError: Si el ID no es un número de 7 dígitos.
        """
        for rec in self:
            if not rec.id_usuario.isdigit() or len(rec.id_usuario) != 7:
                raise ValidationError('El ID de usuario debe tener exactamente 7 dígitos numéricos.')

    def _validar_password_segura(self, password):
        """Validar que la contraseña en texto plano cumpla los requisitos mínimos.

        La contraseña debe tener entre 8 y 50 caracteres.

        :param password: Contraseña en texto plano a validar.
        :type password: str
        :raises ValidationError: Si la contraseña tiene menos de 8 o más de 50 caracteres.
        """
        if not password or len(password) < 8:
            raise ValidationError(_('La contraseña debe tener al menos 8 caracteres.'))
        if len(password) > 50:
            raise ValidationError(_('La contraseña no puede tener más de 50 caracteres.'))

    def _hash_password(self, password):
        """Hashear una contraseña en texto plano usando PBKDF2-SHA512.

        :param password: Contraseña en texto plano.
        :type password: str
        :return: Hash de la contraseña.
        :rtype: str
        """
        return crypt_context.hash(password)

    def action_eliminar_usuario(self):
        """Eliminar físicamente el registro del usuario de la base de datos.

        .. warning::
            Este método borra el registro permanentemente. Considerar usar
            :meth:`action_eliminar_usuario` del bloque de métodos principales
            que realiza un borrado lógico.
        """
        for record in self:
            record.unlink()

    # ============================================
    # RELACIONES CON OTROS MODELOS
    # ============================================

    ids_articulos_venta = fields.One2many(
        'second_market.article',
        'id_propietario',
        string='Artículos en Venta',
        domain=[('estado_publicacion', 'in', ['borrador', 'publicado', 'reservado'])],
        help='Artículos que el usuario tiene publicados'
    )

    ids_comentarios_enviados = fields.One2many(
        'second_market.comment',
        'id_emisor',
        string='Comentarios Enviados'
    )

    ids_comentarios_recibidos = fields.One2many(
        'second_market.comment',
        'id_receptor',
        string='Comentarios Recibidos'
    )

    ids_compras = fields.One2many(
        'second_market.purchase',
        'id_comprador',
        string='Compras Realizadas'
    )

    ids_ventas = fields.One2many(
        'second_market.purchase',
        'id_vendedor',
        string='Ventas Realizadas'
    )

    ids_valoraciones = fields.One2many(
        'second_market.rating',
        'id_usuario',
        string='Valoraciones Recibidas'
    )

    # ============================================
    # CAMPOS ADICIONALES
    # ============================================

    activo = fields.Boolean(
        string='Activo',
        default=True,
        tracking=True,
        help='Si está desmarcado, el usuario está deshabilitado'
    )

    fecha_registro = fields.Datetime(
        string='Fecha de Registro',
        default=fields.Datetime.now,
        readonly=True,
        help='Fecha en que se registró el usuario'
    )

    calificacion_promedio = fields.Float(
        string='Calificación Promedio',
        compute='_computar_calificacion_promedio',
        store=True,
        digits=(3, 2),
        help='Promedio de calificaciones recibidas (1-5)'
    )

    total_valoraciones = fields.Integer(
        string='Total de Valoraciones',
        compute='_computar_total_valoraciones',
        store=True
    )

    avatar = fields.Binary(
        string='Foto de Perfil',
        help='Imagen del perfil del usuario'
    )

    telefono = fields.Char(
        string='Teléfono',
        size=15,
        help='Número de contacto'
    )

    ubicacion = fields.Char(
        string='Ubicación',
        help='Ciudad o localidad del usuario'
    )

    biografia = fields.Text(
        string='Biografía',
        help='Descripción breve del usuario (máx 200 caracteres)'
    )

    # ============================================
    # CAMPOS COMPUTADOS
    # ============================================

    @api.depends('ids_articulos_venta', 'ids_articulos_venta.estado_publicacion', 'ids_articulos_venta.activo')
    def _computar_productos_en_venta(self):
        """Contar los artículos activos en estado ``publicado`` o ``reservado``.

        Almacena el resultado en :attr:`productos_en_venta`.

        .. note::
            En caso de error durante el cálculo, asigna ``0`` y registra
            una advertencia en el log del servidor.
        """
        for usuario in self:
            try:
                if usuario.ids_articulos_venta:
                    articulos_venta = usuario.ids_articulos_venta.filtered(
                        lambda a: a.estado_publicacion in ['publicado', 'reservado'] and a.activo
                    )
                    usuario.productos_en_venta = len(articulos_venta)
                else:
                    usuario.productos_en_venta = 0
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando productos en venta para usuario {usuario.id}: {str(e)}")
                usuario.productos_en_venta = 0

    @api.depends('ids_ventas')
    def _computar_productos_vendidos(self):
        """Contar el total de ventas realizadas por el usuario.

        Almacena el resultado en :attr:`productos_vendidos`.

        .. note::
            En caso de error, asigna ``0`` y registra una advertencia en el log.
        """
        for usuario in self:
            try:
                usuario.productos_vendidos = len(usuario.ids_ventas) if usuario.ids_ventas else 0
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando productos vendidos para usuario {usuario.id}: {str(e)}")
                usuario.productos_vendidos = 0

    @api.depends('ids_compras')
    def _computar_productos_comprados(self):
        """Contar el total de compras realizadas por el usuario.

        Almacena el resultado en :attr:`productos_comprados`.

        .. note::
            En caso de error, asigna ``0`` y registra una advertencia en el log.
        """
        for usuario in self:
            try:
                usuario.productos_comprados = len(usuario.ids_compras) if usuario.ids_compras else 0
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando productos comprados para usuario {usuario.id}: {str(e)}")
                usuario.productos_comprados = 0

    @api.depends('fecha_registro')
    def _computar_antiguedad(self):
        """Calcular los años transcurridos desde la fecha de registro del usuario.

        Almacena el resultado en :attr:`antiguedad`.
        """
        for usuario in self:
            if usuario.fecha_registro:
                delta = fields.Datetime.now() - usuario.fecha_registro
                usuario.antiguedad = int(delta.days / 365)
            else:
                usuario.antiguedad = 0

    @api.depends('ids_valoraciones', 'ids_valoraciones.calificacion')
    def _computar_calificacion_promedio(self):
        """Calcular el promedio de calificaciones recibidas por el usuario.

        Solo se incluyen valoraciones con calificación mayor que 0.
        El resultado se redondea a 2 decimales.

        Almacena el resultado en :attr:`calificacion_promedio`.

        .. note::
            En caso de error, asigna ``0.0`` y registra una advertencia en el log.
        """
        for usuario in self:
            try:
                if usuario.ids_valoraciones:
                    valoraciones = usuario.ids_valoraciones.filtered(lambda v: int(v.calificacion) > 0)
                    if valoraciones:
                        usuario.calificacion_promedio = round(
                            sum(int(v.calificacion) for v in valoraciones) / len(valoraciones), 2
                        )
                    else:
                        usuario.calificacion_promedio = 0.0
                else:
                    usuario.calificacion_promedio = 0.0
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando calificación promedio para usuario {usuario.id}: {str(e)}")
                usuario.calificacion_promedio = 0.0

    @api.depends('ids_valoraciones')
    def _computar_total_valoraciones(self):
        """Contar el número total de valoraciones recibidas por el usuario.

        Almacena el resultado en :attr:`total_valoraciones`.

        .. note::
            En caso de error, asigna ``0`` y registra una advertencia en el log.
        """
        for usuario in self:
            try:
                usuario.total_valoraciones = len(usuario.ids_valoraciones) if usuario.ids_valoraciones else 0
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error calculando total valoraciones para usuario {usuario.id}: {str(e)}")
                usuario.total_valoraciones = 0

    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================

    @api.constrains('id_usuario')
    def _check_id_usuario(self):
        """Validar que el ID de usuario tenga exactamente 7 dígitos numéricos.

        Solo se valida cuando el valor no es el placeholder ``'Nuevo'``.

        :raises ValidationError: Si el ID no es un número de exactamente 7 dígitos.
        """
        for usuario in self:
            if usuario.id_usuario != _('Nuevo'):
                if not usuario.id_usuario.isdigit() or len(usuario.id_usuario) != 7:
                    raise ValidationError(_('El ID de usuario debe tener exactamente 7 dígitos numéricos.'))

    @api.constrains('name')
    def _check_nombre_length(self):
        """Validar que el nombre del usuario no supere 50 caracteres.

        :raises ValidationError: Si el nombre tiene más de 50 caracteres.
        """
        for usuario in self:
            if len(usuario.name) > 50:
                raise ValidationError(_('El nombre no puede tener más de 50 caracteres.'))

    @api.constrains('login')
    def _check_login_unique(self):
        """Validar que el login sea único en la plataforma.

        :raises ValidationError: Si ya existe otro usuario con el mismo login/email.
        """
        for usuario in self:
            if usuario.login:
                duplicados = self.search([
                    ('login', '=', usuario.login),
                    ('id', '!=', usuario.id)
                ])
                if duplicados:
                    raise ValidationError(_('Ya existe un usuario con este login/email.'))

    @api.constrains('login')
    def _check_email_format(self):
        """Validar el formato del email cuando el login contiene el símbolo ``@``.

        Solo se aplica validación de formato email si el login contiene ``@``.

        :raises ValidationError: Si el login parece un email pero su formato no es válido.
        """
        for usuario in self:
            if usuario.login and '@' in usuario.login:
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_regex, usuario.login):
                    raise ValidationError(_('El formato del email no es válido.'))

    @api.constrains('biografia')
    def _check_biografia_length(self):
        """Validar que la biografía no supere 200 caracteres.

        :raises ValidationError: Si la biografía tiene más de 200 caracteres.
        """
        for usuario in self:
            if usuario.biografia and len(usuario.biografia) > 200:
                raise ValidationError(_('La biografía no puede tener más de 200 caracteres.'))

    @api.constrains('telefono')
    def _check_telefono_format(self):
        """Validar el formato del número de teléfono.

        Solo se permiten dígitos, espacios, guiones, paréntesis y el símbolo ``+``.

        :raises ValidationError: Si el teléfono contiene caracteres no permitidos.
        """
        for usuario in self:
            if usuario.telefono:
                if not re.match(r'^[\d\s\-\(\)\+]+$', usuario.telefono):
                    raise ValidationError(_(
                        'El formato del teléfono no es válido. '
                        'Solo números, espacios, guiones y paréntesis.'
                    ))

    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================

    @api.model_create_multi
    def create(self, vals_list):
        """Crear uno o varios usuarios generando el ID único y hasheando la contraseña.

        Para cada usuario:
        - Genera un ID de 7 dígitos desde la secuencia ``second_market.user``.
        - Valida y hashea la contraseña antes de guardarla.

        :param vals_list: Lista de diccionarios con los valores de cada usuario.
        :type vals_list: list[dict]
        :return: Recordset con los usuarios creados.
        :rtype: second_market.user
        """
        for vals in vals_list:
            if vals.get('id_usuario', _('Nuevo')) == _('Nuevo'):
                vals['id_usuario'] = self.env['ir.sequence'].next_by_code('second_market.user') or _('Nuevo')
            if vals.get('password'):
                self._validar_password_segura(vals['password'])
                vals['password'] = self._hash_password(vals['password'])

        usuarios = super(SecondMarketUser, self).create(vals_list)
        return usuarios

    def write(self, vals):
        """Actualizar un usuario, hasheando la contraseña si se modifica.

        :param vals: Diccionario con los campos a actualizar.
        :type vals: dict
        :return: Resultado de la operación de escritura.
        :rtype: bool
        """
        if 'password' in vals:
            self._validar_password_segura(vals['password'])
            vals['password'] = self._hash_password(vals['password'])
        return super(SecondMarketUser, self).write(vals)

    # ============================================
    # MÉTODOS PRINCIPALES (FUNCIONES DEL DIAGRAMA)
    # ============================================

    def comprar(self, articulo_id):
        """Iniciar el proceso de compra de un artículo.

        Crea un registro de compra en estado ``pendiente`` vinculado al artículo
        y al usuario actual como comprador.

        :param articulo_id: ID del artículo a comprar.
        :type articulo_id: int
        :raises UserError: Si la cuenta del usuario está deshabilitada,
            el artículo no existe, el usuario intenta comprar su propio artículo
            o el artículo no está publicado.
        :return: Acción de notificación de éxito.
        :rtype: dict
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))

        articulo = self.env['second_market.article'].browse(articulo_id)

        if not articulo.exists():
            raise UserError(_('El artículo no existe.'))
        if articulo.id_propietario.id == self.id:
            raise UserError(_('No puedes comprar tu propio artículo.'))
        if articulo.estado_publicacion != 'publicado':
            raise UserError(_('Este artículo no está disponible para compra.'))

        compra = self.env['second_market.purchase'].create({
            'id_comprador': self.id,
            'id_vendedor': articulo.id_propietario.id,
            'id_articulo': articulo.id,
            'precio': articulo.precio,
            'fecha_hora': fields.Datetime.now()
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Compra Iniciada!'),
                'message': _('Has iniciado la compra de "%s" por %.2f€. Confirma la transacción para reservarlo.') % (articulo.nombre, articulo.precio),
                'type': 'success',
                'sticky': False,
            }
        }

    def vender(self, vals_articulo):
        """Publicar un nuevo artículo para vender.

        Asigna automáticamente el usuario actual como propietario del artículo
        y crea el registro en el modelo ``second_market.article``.

        :param vals_articulo: Diccionario con los valores del artículo a publicar.
        :type vals_articulo: dict
        :raises UserError: Si la cuenta del usuario está deshabilitada.
        :return: Registro del artículo creado.
        :rtype: second_market.article
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))

        vals_articulo['id_propietario'] = self.id
        articulo = self.env['second_market.article'].create(vals_articulo)
        return articulo

    def chatear(self, destinatario_id, mensaje):
        """Iniciar o continuar un chat con otro usuario.

        :param destinatario_id: ID del usuario con el que se quiere chatear.
        :type destinatario_id: int
        :param mensaje: Texto del mensaje inicial.
        :type mensaje: str
        :raises UserError: Si la cuenta del usuario o del destinatario está deshabilitada,
            o si el usuario intenta chatear consigo mismo.
        :return: ``True`` si la operación se realizó con éxito.
        :rtype: bool

        .. todo::
            Implementar la creación real del chat y del mensaje inicial.
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))

        destinatario = self.env['second_market.user'].browse(destinatario_id)

        if not destinatario.exists() or not destinatario.activo:
            raise UserError(_('El destinatario no existe o está deshabilitado.'))
        if destinatario.id == self.id:
            raise UserError(_('No puedes chatear contigo mismo.'))

        return True

    def valorar(self, usuario_id, calificacion, comentario=False):
        """Valorar a otro usuario de la plataforma.

        :param usuario_id: ID del usuario a valorar.
        :type usuario_id: int
        :param calificacion: Calificación del 1 al 5.
        :type calificacion: str
        :param comentario: Comentario opcional sobre la valoración.
        :type comentario: str or bool
        :raises UserError: Si la cuenta está deshabilitada, el usuario no existe
            o el usuario intenta valorarse a sí mismo.
        :return: Registro de valoración creado.
        :rtype: second_market.rating
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))

        usuario_valorado = self.env['second_market.user'].browse(usuario_id)

        if not usuario_valorado.exists():
            raise UserError(_('El usuario no existe.'))
        if usuario_valorado.id == self.id:
            raise UserError(_('No puedes valorarte a ti mismo.'))

        valoracion = self.env['second_market.rating'].create({
            'id_usuario': usuario_valorado.id,
            'id_valorador': self.id,
            'calificacion': calificacion,
            'comentario': comentario
        })

        return valoracion

    def comentar(self, articulo_id, texto):
        """Publicar un comentario en un artículo dirigido a su propietario.

        :param articulo_id: ID del artículo en el que se comenta.
        :type articulo_id: int
        :param texto: Contenido del comentario.
        :type texto: str
        :raises UserError: Si la cuenta está deshabilitada o el artículo no existe.
        :return: Registro de comentario creado.
        :rtype: second_market.comment
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))

        articulo = self.env['second_market.article'].browse(articulo_id)

        if not articulo.exists():
            raise UserError(_('El artículo no existe.'))

        comentario = self.env['second_market.comment'].create({
            'id_articulo': articulo.id,
            'id_emisor': self.id,
            'id_receptor': articulo.id_propietario.id,
            'texto': texto,
            'fecha_hora': fields.Datetime.now()
        })

        return comentario

    def reportar(self, tipo_reporte, id_reportado, motivo):
        """Reportar un usuario o artículo por comportamiento inapropiado.

        :param tipo_reporte: Tipo de elemento reportado (``'articulo'``, ``'comentario'`` o ``'usuario'``).
        :type tipo_reporte: str
        :param id_reportado: ID del elemento a reportar.
        :type id_reportado: int
        :param motivo: Motivo del reporte.
        :type motivo: str
        :raises UserError: Si la cuenta del usuario está deshabilitada.
        :return: ``True`` si la operación se realizó con éxito.
        :rtype: bool

        .. todo::
            Implementar la creación del registro de denuncia en ``second_market.report``.
        """
        self.ensure_one()

        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))

        return True

    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================

    def action_ver_articulos(self):
        """Abrir la vista de artículos del usuario.

        :return: Acción de ventana para ver los artículos del usuario.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': _('Artículos de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.article',
            'view_mode': 'list,kanban,form',
            'domain': [('id_propietario', '=', self.id)],
            'context': {'default_id_propietario': self.id}
        }

    def action_ver_compras(self):
        """Abrir la vista de compras realizadas por el usuario.

        :return: Acción de ventana para ver las compras del usuario.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': _('Compras de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.purchase',
            'view_mode': 'list,form',
            'domain': [('id_comprador', '=', self.id)]
        }

    def action_ver_ventas(self):
        """Abrir la vista de ventas realizadas por el usuario.

        :return: Acción de ventana para ver las ventas del usuario.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': _('Ventas de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.purchase',
            'view_mode': 'list,form',
            'domain': [('id_vendedor', '=', self.id)]
        }

    def action_ver_valoraciones(self):
        """Abrir la vista de valoraciones recibidas por el usuario (lista, formulario y gráfico).

        :return: Acción de ventana para ver las valoraciones del usuario.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': _('Valoraciones de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.rating',
            'view_mode': 'list,form,graph',
            'domain': [('id_usuario', '=', self.id)],
            'context': {'default_id_usuario': self.id}
        }

    def action_ver_grafico_valoraciones(self):
        """Abrir directamente la vista de gráfico de valoraciones del usuario.

        :return: Acción de ventana apuntando a la vista de gráfico de valoraciones.
        :rtype: dict
        """
        self.ensure_one()
        return {
            'name': _('Gráfico de Valoraciones: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.rating',
            'view_mode': 'graph',
            'view_id': self.env.ref('second_market.view_second_market_rating_graph').id,
            'domain': [('id_usuario', '=', self.id)],
            'context': {
                'default_id_usuario': self.id,
                'search_default_group_by_calificacion': 1,
            },
            'target': 'current',
        }

    def action_eliminar_usuario(self):
        """Deshabilitar (borrado lógico) al usuario y despublicar sus artículos.

        Solo los moderadores pueden ejecutar esta acción. Establece ``activo = False``
        tanto en el usuario como en todos sus artículos en venta.

        :raises UserError: Si el usuario actual no pertenece al grupo de moderadores.
        :return: Notificación de advertencia en forma de acción de cliente.
        :rtype: dict
        """
        self.ensure_one()

        if not self.env.user.has_group('second_market.group_second_market_moderator'):
            raise UserError(_('No tienes permisos para eliminar usuarios.'))

        self.write({'activo': False})
        self.ids_articulos_venta.write({'activo': False})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Usuario Eliminado'),
                'message': _('El usuario ha sido deshabilitado correctamente.'),
                'type': 'warning',
                'sticky': False,
            }
        }

    def _enviar_email_bienvenida(self):
        """Enviar un email de bienvenida al nuevo usuario tras su registro.

        .. todo::
            Implementar el envío del email de bienvenida usando la plantilla
            de correo correspondiente.
        """
        self.ensure_one()
        pass