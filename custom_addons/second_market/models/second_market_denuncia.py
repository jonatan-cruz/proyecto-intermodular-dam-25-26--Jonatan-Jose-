# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class Denuncia(models.Model):
    _name = 'second_market.report'
    _description = 'Denuncia/Reporte de Artículo'
    _order = 'create_date desc'
    
    # ============================================
    # CAMPOS BÁSICOS
    # ============================================
    
    nombre = fields.Char(
        string='Número de Denuncia',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nueva'),
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
        ('comentario', 'Comentario')
    ],
        string='Tipo de Denuncia',
        required=True,
        default='articulo',
        help='Indica si la denuncia es sobre un artículo o un comentario'
    )
    
    # Denuncia sobre artículo
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
    
    # Usuario que crea la denuncia (usuario de la app)
    id_denunciante = fields.Many2one(
        'second_market.user',
        string='Denunciante',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Usuario de la app que realiza la denuncia'
    )
    
    # Empleado/Moderador que gestiona la denuncia
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
    
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    @api.constrains('id_articulo')
    def _check_tipo_denuncia(self):
        """Verificar que haya relación con artículo"""
        for denuncia in self:
            if not denuncia.id_articulo:
                raise ValidationError(_('Debes seleccionar un artículo para denunciar.'))
    
    @api.constrains('descripcion')
    def _check_descripcion_length(self):
        """Validar longitud de descripción"""
        for denuncia in self:
            if denuncia.descripcion and len(denuncia.descripcion) > 500:
                raise ValidationError(_('La descripción no puede tener más de 500 caracteres.'))
    
    @api.constrains('id_denunciante', 'id_articulo')
    def _check_no_auto_denuncia_articulo(self):
        """Evitar que un usuario denuncie su propio artículo"""
        for denuncia in self:
            if denuncia.id_articulo and denuncia.id_denunciante:
                if denuncia.id_denunciante.id == denuncia.id_articulo.id_propietario.id:
                    raise ValidationError(_('No puedes denunciar tu propio artículo.'))
    
    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================
    
    @api.model
    def create(self, vals):
        """Generar número de denuncia único"""
        if vals.get('nombre', _('Nueva')) == _('Nueva'):
            vals['nombre'] = self.env['ir.sequence'].next_by_code('second_market.report') or _('Nueva')
        
        denuncia = super(Denuncia, self).create(vals)
        denuncia._notificar_nueva_denuncia()
        return denuncia
    
    def write(self, vals):
        """Registrar fecha de resolución cuando cambia el estado"""
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
        """Asignar moderador actual a la denuncia"""
        self.ensure_one()
        self.write({
            'id_moderador': self.env.user.id,
            'estado': 'en_revision'
        })
        
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
        """Resolver denuncia"""
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
        """Rechazar denuncia"""
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
        """Cerrar denuncia"""
        self.ensure_one()
        self.write({'estado': 'cerrada', 'activo': False})
        return True
    
    def accion_ver_articulo(self):
        """Ver el artículo denunciado"""
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
        """Notificar a moderadores sobre nueva denuncia"""
        self.ensure_one()
        self.message_post(
            body=_('Nueva denuncia creada por {}. Motivo: {}').format(
                self.id_denunciante.name,
                dict(self._fields['motivo'].selection).get(self.motivo)
            ),
            subject=_('Nueva Denuncia: {}').format(self.nombre)
        )
    
    def _notificar_cambio_estado(self):
        """Notificar al denunciante sobre cambio de estado"""
        for denuncia in self:
            if denuncia.id_denunciante:
                denuncia.message_post(
                    body=_('El estado de la denuncia de {} ha cambiado a: {}').format(
                        denuncia.id_denunciante.name,
                        dict(self._fields['estado'].selection).get(denuncia.estado)
                    ),
                    subject=_('Actualización de Denuncia: {}').format(denuncia.nombre)
                )
