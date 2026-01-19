# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import re


class SecondMarketUser(models.Model):
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
        size=50,
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
        for rec in self:
            if not rec.id_usuario.isdigit() or len(rec.id_usuario) != 7:
                raise ValidationError('El ID de usuario debe tener exactamente 7 dígitos numéricos.')

    @api.constrains('password')
    def _check_password(self):
        """Validar contraseña (8-50 caracteres)"""
        for rec in self:
            if len(rec.password) < 8:
                raise ValidationError(_('La contraseña debe tener al menos 8 caracteres.'))
            if len(rec.password) > 50:
                raise ValidationError(_('La contraseña no puede tener más de 50 caracteres.'))
            
    def action_eliminar_usuario(self):
        for record in self:
            record.unlink()
    
    # ============================================
    # RELACIONES CON OTROS MODELOS
    # ============================================
    
    # Artículos que el usuario está vendiendo
    ids_articulos_venta = fields.One2many(
        'second_market.article',
        'id_propietario',
        string='Artículos en Venta',
        domain=[('estado_publicacion', 'in', ['borrador', 'publicado', 'reservado'])],
        help='Artículos que el usuario tiene publicados'
    )
    
    # Comentarios enviados
    ids_comentarios_enviados = fields.One2many(
        'second_market.comment',
        'id_emisor',
        string='Comentarios Enviados'
    )
    
    # Comentarios recibidos
    ids_comentarios_recibidos = fields.One2many(
        'second_market.comment',
        'id_receptor',
        string='Comentarios Recibidos'
    )
    
    # Compras realizadas (como comprador)
    ids_compras = fields.One2many(
        'second_market.purchase',
        'id_comprador',
        string='Compras Realizadas'
    )
    
    # Ventas realizadas (como vendedor)
    ids_ventas = fields.One2many(
        'second_market.purchase',
        'id_vendedor',
        string='Ventas Realizadas'
    )
    
    # Valoraciones recibidas
    ids_valoraciones = fields.One2many(
        'second_market.rating',
        'id_usuario',
        string='Valoraciones Recibidas'
    )
    
    # Chats del usuario
    # ids_chats = fields.Many2many(
    #     'second_market.chat',
    #     'second_market_user_chat_rel',
    #     'user_id',
    #     'chat_id',
    #     string='Chats'
    # )
    
    # Reportes realizados por el usuario
    # ids_reportes_enviados = fields.One2many(
    #     'second_market.report',
    #     'id_reportador',
    #     string='Reportes Enviados'
    # )
    
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
    
    @api.depends('ids_articulos_venta.estado_publicacion')
    def _computar_productos_en_venta(self):
        """Contar productos actualmente en venta"""
        for usuario in self:
            usuario.productos_en_venta = len(usuario.ids_articulos_venta.filtered(
                lambda a: a.estado_publicacion in ['publicado', 'reservado'] and a.activo
            ))
    
    @api.depends('ids_ventas')
    def _computar_productos_vendidos(self):
        """Contar productos vendidos"""
        for usuario in self:
            usuario.productos_vendidos = len(usuario.ids_ventas)
    
    @api.depends('ids_compras')
    def _computar_productos_comprados(self):
        """Contar productos comprados"""
        for usuario in self:
            usuario.productos_comprados = len(usuario.ids_compras)
    
    @api.depends('fecha_registro')
    def _computar_antiguedad(self):
        """Calcular años de antigüedad"""
        for usuario in self:
            if usuario.fecha_registro:
                delta = fields.Datetime.now() - usuario.fecha_registro
                usuario.antiguedad = int(delta.days / 365)
            else:
                usuario.antiguedad = 0
    
    @api.depends('ids_valoraciones.calificacion')
    def _computar_calificacion_promedio(self):
        """Calcular promedio de calificaciones"""
        for usuario in self:
            valoraciones = usuario.ids_valoraciones.filtered(lambda v: v.calificacion > 0)
            if valoraciones:
                usuario.calificacion_promedio = sum(valoraciones.mapped('calificacion')) / len(valoraciones)
            else:
                usuario.calificacion_promedio = 0.0
    
    @api.depends('ids_valoraciones')
    def _computar_total_valoraciones(self):
        """Contar total de valoraciones recibidas"""
        for usuario in self:
            usuario.total_valoraciones = len(usuario.ids_valoraciones)
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    @api.constrains('id_usuario')
    def _check_id_usuario(self):
        """Validar formato del ID de usuario (7 dígitos)"""
        for usuario in self:
            if usuario.id_usuario != _('Nuevo'):
                if not usuario.id_usuario.isdigit() or len(usuario.id_usuario) != 7:
                    raise ValidationError(_('El ID de usuario debe tener exactamente 7 dígitos numéricos.'))
    
    
    @api.constrains('name')
    def _check_nombre_length(self):
        """Validar longitud del nombre (máx 50)"""
        for usuario in self:
            if len(usuario.name) > 50:
                raise ValidationError(_('El nombre no puede tener más de 50 caracteres.'))
    
    @api.constrains('login')
    def _check_login_unique(self):
        """Validar que el login sea único"""
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
        """Validar formato de email si se usa como login"""
        for usuario in self:
            if usuario.login and '@' in usuario.login:
                # Validación básica de email
                email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_regex, usuario.login):
                    raise ValidationError(_('El formato del email no es válido.'))
    
    @api.constrains('biografia')
    def _check_biografia_length(self):
        """Validar longitud de la biografía"""
        for usuario in self:
            if usuario.biografia and len(usuario.biografia) > 200:
                raise ValidationError(_('La biografía no puede tener más de 200 caracteres.'))
    
    @api.constrains('telefono')
    def _check_telefono_format(self):
        """Validar formato del teléfono"""
        for usuario in self:
            if usuario.telefono:
                # Permitir solo números, espacios, guiones y paréntesis
                if not re.match(r'^[\d\s\-\(\)\+]+$', usuario.telefono):
                    raise ValidationError(_('El formato del teléfono no es válido. Solo números, espacios, guiones y paréntesis.'))
    
    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generar ID único al crear usuario"""
        for vals in vals_list:
            if vals.get('id_usuario', _('Nuevo')) == _('Nuevo'):
                vals['id_usuario'] = self.env['ir.sequence'].next_by_code('second_market.user') or _('Nuevo')
        
        usuarios = super(SecondMarketUser, self).create(vals_list)
        return usuarios
    
    def write(self, vals):
        """Tracking de cambios importantes"""
        # Validar cambios de contraseña
        if 'password' in vals:
            # Aquí podrías agregar hash de contraseña
            pass
        
        return super(SecondMarketUser, self).write(vals)
    
    # ============================================
    # MÉTODOS PRINCIPALES (FUNCIONES DEL DIAGRAMA)
    # ============================================
    
    def comprar(self, articulo_id):
        """Realizar una compra de un artículo"""
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
        
        # Crear registro de compra
        compra = self.env['second_market.purchase'].create({
            'id_comprador': self.id,
            'id_vendedor': articulo.id_propietario.id,
            'id_articulo': articulo.id,
            'precio': articulo.precio,
            'fecha_hora': fields.Datetime.now()
        })
        
        # Actualizar estado del artículo
        articulo.write({'estado_publicacion': 'vendido'})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Compra Realizada!'),
                'message': _('Has comprado "%s" por %.2f€') % (articulo.nombre, articulo.precio),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def vender(self, vals_articulo):
        """Publicar un artículo para vender"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))
        
        # Asignar el propietario
        vals_articulo['id_propietario'] = self.id
        
        # Crear el artículo
        articulo = self.env['second_market.article'].create(vals_articulo)
        
        return articulo
    
    def chatear(self, destinatario_id, mensaje):
        """Iniciar o continuar un chat con otro usuario"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))
        
        destinatario = self.env['second_market.user'].browse(destinatario_id)
        
        if not destinatario.exists() or not destinatario.activo:
            raise UserError(_('El destinatario no existe o está deshabilitado.'))
        
        if destinatario.id == self.id:
            raise UserError(_('No puedes chatear contigo mismo.'))
        
        # TODO: Implementar creación de chat
        # chat = self.env['second.market.chat'].create({...})
        
        return True
    
    def valorar(self, usuario_id, calificacion, comentario=False):
        """Valorar a otro usuario"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))
        
        usuario_valorado = self.env['second_market.user'].browse(usuario_id)
        
        if not usuario_valorado.exists():
            raise UserError(_('El usuario no existe.'))
        
        if usuario_valorado.id == self.id:
            raise UserError(_('No puedes valorarte a ti mismo.'))
        
        # Crear valoración
        valoracion = self.env['second_market.rating'].create({
            'id_usuario': usuario_valorado.id,
            'id_valorador': self.id,
            'calificacion': calificacion,
            'comentario': comentario
        })
        
        return valoracion
    
    def comentar(self, articulo_id, texto):
        """Comentar en un artículo"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))
        
        articulo = self.env['second_market.article'].browse(articulo_id)
        
        if not articulo.exists():
            raise UserError(_('El artículo no existe.'))
        
        # Crear comentario dirigido al propietario del artículo
        comentario = self.env['second_market.comment'].create({
            'id_articulo': articulo.id,
            'id_emisor': self.id,
            'id_receptor': articulo.id_propietario.id,
            'texto': texto,
            'fecha_hora': fields.Datetime.now()
        })
        
        return comentario
    
    def reportar(self, tipo_reporte, id_reportado, motivo):
        """Reportar un usuario o artículo"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Tu cuenta está deshabilitada.'))
        
        # TODO: Implementar sistema de reportes
        # reporte = self.env['second.market.report'].create({...})
        
        return True
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    def action_ver_articulos(self):
        """Ver artículos del usuario"""
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
        """Ver compras realizadas"""
        self.ensure_one()
        return {
            'name': _('Compras de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.purchase',
            'view_mode': 'list,form',
            'domain': [('id_comprador', '=', self.id)]
        }
    
    def action_ver_ventas(self):
        """Ver ventas realizadas"""
        self.ensure_one()
        return {
            'name': _('Ventas de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.purchase',
            'view_mode': 'list,form',
            'domain': [('id_vendedor', '=', self.id)]
        }
    
    def action_ver_valoraciones(self):
        """Ver valoraciones recibidas"""
        self.ensure_one()
        return {
            'name': _('Valoraciones de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.rating',
            'view_mode': 'list,form',
            'domain': [('id_usuario', '=', self.id)]
        }
    
    def action_eliminar_usuario(self):
        """Eliminar (desactivar) usuario"""
        self.ensure_one()
        
        # Solo moderadores pueden eliminar usuarios
        if not self.env.user.has_group('second_market.group_second_market_moderator'):
            raise UserError(_('No tienes permisos para eliminar usuarios.'))
        
        self.write({'activo': False})
        
        # Despublicar todos los artículos del usuario
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
        """Enviar email de bienvenida al nuevo usuario"""
        self.ensure_one()
        # TODO: Implementar envío de email
        pass