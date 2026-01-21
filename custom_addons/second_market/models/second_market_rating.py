# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SecondMarketRating(models.Model):
    _name = 'second_market.rating'
    _description = 'Valoración de Usuario'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_hora desc'
    
    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================
    
    calificacion = fields.Selection(
    selection=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ],
    string='Calificación',
    required=True,
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
        """Validar que la calificación esté entre 1 y 5"""
        for valoracion in self:
            cal = int(valoracion.calificacion)  # <-- convertir a int
            if cal < 1 or cal > 5:
                raise ValidationError(_('La calificación debe estar entre 1 y 5 estrellas.'))

    
    @api.constrains('id_usuario', 'id_valorador')
    def _check_autovaloracion(self):
        """Validar que un usuario no se valore a sí mismo"""
        for valoracion in self:
            if valoracion.id_usuario == valoracion.id_valorador:
                raise ValidationError(_('No puedes valorarte a ti mismo.'))
    
    @api.constrains('comentario')
    def _check_comentario_length(self):
        """Validar longitud del comentario"""
        for valoracion in self:
            if valoracion.comentario and len(valoracion.comentario) > 300:
                raise ValidationError(_('El comentario no puede tener más de 300 caracteres.'))
    
    @api.constrains('id_usuario', 'id_valorador')
    def _check_valoracion_unica(self):
        """Validar que no exista ya una valoración del mismo valorador al mismo usuario"""
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
        """Crear valoración"""
        valoracion = super(SecondMarketRating, self).create(vals)
        
        # Notificar al usuario valorado
        valoracion._notificar_nueva_valoracion()
        
        return valoracion
    
    def asignar_calificacion(self, calificacion_nueva):
        """Asignar o actualizar calificación"""
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
        """Obtener promedio de calificaciones de un usuario"""
        # Este método se llama desde el usuario
        # Ver _computar_calificacion_promedio en second_market.user
        pass
    
    def _notificar_nueva_valoracion(self):
        """Notificar al usuario que ha recibido una valoración"""
        self.ensure_one()
        # TODO: Implementar notificación
        pass