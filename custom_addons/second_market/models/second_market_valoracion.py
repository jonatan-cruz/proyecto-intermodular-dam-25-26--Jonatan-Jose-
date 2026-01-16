# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SecondMarketRating(models.Model):
    _name = 'second.market.rating'
    _description = 'Valoración de Usuario'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================
    
    calificacion = fields.Integer(
        string='Calificación',
        required=True,
        tracking=True,
        help='Calificación de 1 a 5 estrellas'
    )
    
    # ============================================
    # RELACIONES
    # ============================================
    
    id_usuario = fields.Many2one(
        'second.market.user',
        string='Usuario Valorado',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Usuario que recibe la valoración'
    )
    
    id_valorador = fields.Many2one(
        'second.market.user',
        string='Valorado por',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Usuario que realiza la valoración'
    )
    
    id_transaccion = fields.Many2one(
        'second.market.purchase',
        string='Transacción',
        ondelete='cascade',
        tracking=True,
        help='Transacción asociada a esta valoración'
    )
    
    # ============================================
    # COMENTARIO OPCIONAL
    # ============================================
    
    comentario = fields.Char(
        string='Comentario',
        size=300,
        help='Comentario opcional (máx 300 caracteres)'
    )
    
    # ============================================
    # CAMPOS ADICIONALES
    # ============================================
    
    fecha_valoracion = fields.Datetime(
        string='Fecha de Valoración',
        default=fields.Datetime.now,
        required=True,
        readonly=True,
        help='Fecha en que se realizó la valoración'
    )
    
    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, la valoración está eliminada'
    )
    
    # Campos relacionados para mostrar información
    nombre_usuario_valorado = fields.Char(
        string='Usuario Valorado',
        related='id_usuario.name',
        store=True,
        readonly=True
    )
    
    nombre_valorador = fields.Char(
        string='Valorador',
        related='id_valorador.name',
        store=True,
        readonly=True
    )
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    @api.constrains('calificacion')
    def _check_calificacion_rango(self):
        """Validar que la calificación esté entre 1 y 5"""
        for valoracion in self:
            if valoracion.calificacion < 1 or valoracion.calificacion > 5:
                raise ValidationError(_('La calificación debe estar entre 1 y 5 estrellas.'))
    
    @api.constrains('comentario')
    def _check_comentario_length(self):
        """Validar longitud del comentario"""
        for valoracion in self:
            if valoracion.comentario and len(valoracion.comentario) > 300:
                raise ValidationError(_('El comentario no puede tener más de 300 caracteres.'))
    
    @api.constrains('id_usuario', 'id_valorador')
    def _check_auto_valoracion(self):
        """Validar que un usuario no se valore a sí mismo"""
        for valoracion in self:
            if valoracion.id_usuario == valoracion.id_valorador:
                raise ValidationError(_('No puedes valorarte a ti mismo.'))
    
    @api.constrains('id_usuario', 'id_valorador', 'id_transaccion')
    def _check_valoracion_duplicada(self):
        """Validar que no exista una valoración duplicada para la misma transacción"""
        for valoracion in self:
            if valoracion.id_transaccion:
                duplicados = self.search([
                    ('id_transaccion', '=', valoracion.id_transaccion.id),
                    ('id_valorador', '=', valoracion.id_valorador.id),
                    ('id_usuario', '=', valoracion.id_usuario.id),
                    ('id', '!=', valoracion.id),
                    ('activo', '=', True)
                ])
                if duplicados:
                    raise ValidationError(_('Ya has valorado a este usuario en esta transacción.'))
    
    # ============================================
    # MÉTODOS PRINCIPALES
    # ============================================
    
    def asignarCalificacion(self, calificacion_valor, comentario_texto=False):
        """
        Asignar o actualizar la calificación
        Args:
            calificacion_valor (int): Valor de 1 a 5
            comentario_texto (str): Comentario opcional
        """
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('No puedes modificar una valoración eliminada.'))
        
        # Validar rango
        if calificacion_valor < 1 or calificacion_valor > 5:
            raise UserError(_('La calificación debe estar entre 1 y 5.'))
        
        # Actualizar valores
        vals = {
            'calificacion': calificacion_valor,
            'fecha_valoracion': fields.Datetime.now()
        }
        
        if comentario_texto is not False:  # Permitir string vacío
            if comentario_texto and len(comentario_texto) > 300:
                raise UserError(_('El comentario no puede tener más de 300 caracteres.'))
            vals['comentario'] = comentario_texto
        
        self.write(vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('¡Calificación Actualizada!'),
                'message': _('Has valorado a %s con %d estrellas.') % (self.nombre_usuario_valorado, calificacion_valor),
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.model
    def obtenerPromedio(self, usuario_id):
        """
        Obtener el promedio de calificaciones de un usuario
        Args:
            usuario_id (int): ID del usuario
        Returns:
            dict: Diccionario con promedio y total de valoraciones
        """
        usuario = self.env['second.market.user'].browse(usuario_id)
        
        if not usuario.exists():
            raise UserError(_('El usuario no existe.'))
        
        # Buscar todas las valoraciones activas del usuario
        valoraciones = self.search([
            ('id_usuario', '=', usuario_id),
            ('activo', '=', True),
            ('calificacion', '>', 0)
        ])
        
        if not valoraciones:
            return {
                'promedio': 0.0,
                'total_valoraciones': 0,
                'usuario': usuario.name
            }
        
        # Calcular promedio
        suma_calificaciones = sum(valoraciones.mapped('calificacion'))
        total = len(valoraciones)
        promedio = round(suma_calificaciones / total, 2)
        
        # Distribución de estrellas (opcional, útil para mostrar gráficos)
        distribucion = {
            5: len(valoraciones.filtered(lambda v: v.calificacion == 5)),
            4: len(valoraciones.filtered(lambda v: v.calificacion == 4)),
            3: len(valoraciones.filtered(lambda v: v.calificacion == 3)),
            2: len(valoraciones.filtered(lambda v: v.calificacion == 2)),
            1: len(valoraciones.filtered(lambda v: v.calificacion == 1)),
        }
        
        return {
            'promedio': promedio,
            'total_valoraciones': total,
            'usuario': usuario.name,
            'distribucion_estrellas': distribucion
        }
    
    # ============================================
    # MÉTODOS CREATE
    # ============================================
    
    @api.model
    def create(self, vals):
        """Validaciones adicionales al crear"""
        valoracion = super(SecondMarketRating, self).create(vals)
        
        # Notificar al usuario valorado (opcional)
        valoracion._notificar_nueva_valoracion()
        
        return valoracion
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    def _notificar_nueva_valoracion(self):
        """Notificar al usuario que ha recibido una nueva valoración"""
        self.ensure_one()
        # TODO: Implementar notificación
        pass
    
    def eliminar(self):
        """Eliminar valoración (borrado lógico)"""
        self.ensure_one()
        
        # Solo el valorador o un moderador pueden eliminar
        if self.id_valorador.id != self.env.context.get('uid'):
            if not self.env.user.has_group('base.group_system'):
                raise UserError(_('Solo puedes eliminar tus propias valoraciones.'))
        
        self.write({'activo': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Valoración Eliminada'),
                'message': _('La valoración ha sido eliminada.'),
                'type': 'warning',
                'sticky': False,
            }
        }
    
    # ============================================
    # ACCIONES DE VISTA
    # ============================================
    
    def action_ver_usuario_valorado(self):
        """Abrir perfil del usuario valorado"""
        self.ensure_one()
        return {
            'name': _('Usuario Valorado'),
            'type': 'ir.actions.act_window',
            'res_model': 'second.market.user',
            'view_mode': 'form',
            'res_id': self.id_usuario.id,
            'target': 'current',
        }
    
    def action_ver_transaccion(self):
        """Abrir transacción asociada"""
        self.ensure_one()
        
        if not self.id_transaccion:
            raise UserError(_('Esta valoración no está asociada a ninguna transacción.'))
        
        return {
            'name': _('Transacción'),
            'type': 'ir.actions.act_window',
            'res_model': 'second.market.purchase',
            'view_mode': 'form',
            'res_id': self.id_transaccion.id,
            'target': 'current',
        }