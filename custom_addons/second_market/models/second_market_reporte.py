# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SecondMarketReport(models.Model):
    _name = 'second.market.report'
    _description = 'Denuncia/Reporte de Second Market'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    
    # ============================================
    # CAMPOS PRINCIPALES
    # ============================================
    
    id_reporte = fields.Char(
        string='ID Reporte',
        size=7,
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
        help='Código único de 7 dígitos para el reporte'
    )
    
    # ============================================
    # USUARIO QUE DENUNCIA
    # ============================================
    
    id_reportador = fields.Many2one(
        'second.market.user',
        string='Reportado por',
        required=True,
        ondelete='cascade',
        tracking=True,
        help='Usuario que realiza el reporte'
    )
    
    nombre_reportador = fields.Char(
        string='Nombre Reportador',
        related='id_reportador.name',
        store=True,
        readonly=True
    )
    
    # ============================================
    # MENSAJE DE DENUNCIA
    # ============================================
    
    mensaje = fields.Text(
        string='Mensaje de Denuncia',
        required=True,
        help='Descripción del problema (máx 500 caracteres)'
    )
    
    # ============================================
    # OBJETO DENUNCIADO (PRODUCTO O COMENTARIO)
    # ============================================
    
    tipo_objeto = fields.Selection([
        ('producto', 'Producto'),
        ('comentario', 'Comentario')
    ],
        string='Tipo de Denuncia',
        required=True,
        tracking=True,
        help='Elemento que se está denunciando'
    )
    
    id_articulo = fields.Many2one(
        'second_market.article',
        string='Producto Denunciado',
        ondelete='cascade',
        tracking=True,
        help='Producto denunciado (si aplica)'
    )
    
    id_comentario = fields.Many2one(
        'second.market.comment',
        string='Comentario Denunciado',
        ondelete='cascade',
        tracking=True,
        help='Comentario denunciado (si aplica)'
    )
    
    # Campos relacionados para mostrar información
    nombre_articulo = fields.Char(
        string='Producto',
        related='id_articulo.nombre',
        store=True,
        readonly=True
    )
    
    texto_comentario = fields.Text(
        string='Texto Comentario',
        related='id_comentario.texto',
        readonly=True
    )
    
    # ============================================
    # FECHA DE CREACIÓN
    # ============================================
    
    fecha_creacion = fields.Datetime(
        string='Fecha de Denuncia',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
        help='Fecha y hora en que se creó la denuncia'
    )
    
    # ============================================
    # ESTADO
    # ============================================
    
    activo = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desmarcado, la denuncia está archivada'
    )
    
    # ============================================
    # CONSTRAINTS Y VALIDACIONES
    # ============================================
    
    @api.constrains('tipo_objeto', 'id_articulo', 'id_comentario')
    def _check_tipo_objeto_coherente(self):
        """Validar que el tipo coincida con el objeto denunciado"""
        for reporte in self:
            if reporte.tipo_objeto == 'producto' and not reporte.id_articulo:
                raise ValidationError(_('Debes seleccionar un producto para denuncias de producto.'))
            
            if reporte.tipo_objeto == 'comentario' and not reporte.id_comentario:
                raise ValidationError(_('Debes seleccionar un comentario para denuncias de comentario.'))
    
    @api.constrains('mensaje')
    def _check_mensaje(self):
        """Validar mensaje"""
        for reporte in self:
            if not reporte.mensaje or not reporte.mensaje.strip():
                raise ValidationError(_('El mensaje de denuncia no puede estar vacío.'))
            if len(reporte.mensaje) > 500:
                raise ValidationError(_('El mensaje no puede tener más de 500 caracteres.'))
    
    # ============================================
    # MÉTODOS CREATE
    # ============================================
    
    @api.model
    def create(self, vals):
        """Generar ID único y notificar a todos los empleados"""
        if vals.get('id_reporte', _('Nuevo')) == _('Nuevo'):
            vals['id_reporte'] = self.env['ir.sequence'].next_by_code('second.market.report') or _('Nuevo')
        
        reporte = super(SecondMarketReport, self).create(vals)
        
        # Notificar a TODOS los empleados
        reporte._notificar_empleados()
        
        return reporte
    
    # ============================================
    # MÉTODOS PRINCIPALES
    # ============================================
    
    def eliminar_objeto_denunciado(self):
        """
        Eliminar el objeto denunciado (producto o comentario)
        Cualquier empleado puede ejecutar esta acción
        """
        self.ensure_one()
        
        # Verificar que sea un empleado (usuario interno de Odoo)
        if self.env.user.share:
            raise UserError(_('Solo los empleados pueden gestionar denuncias.'))
        
        if self.tipo_objeto == 'producto' and self.id_articulo:
            self.id_articulo.write({
                'activo': False,
                'estado_publicacion': 'eliminado'
            })
            mensaje = _('El producto "%s" ha sido eliminado.') % self.nombre_articulo
        
        elif self.tipo_objeto == 'comentario' and self.id_comentario:
            self.id_comentario.write({
                'activo': False
            })
            mensaje = _('El comentario ha sido eliminado.')
        
        else:
            raise UserError(_('No se encontró el objeto a eliminar.'))
        
        # Archivar la denuncia
        self.write({'activo': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Contenido Eliminado'),
                'message': mensaje,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def descartar_denuncia(self):
        """
        Descartar la denuncia sin eliminar el objeto
        Cualquier empleado puede ejecutar esta acción
        """
        self.ensure_one()
        
        # Verificar que sea un empleado
        if self.env.user.share:
            raise UserError(_('Solo los empleados pueden gestionar denuncias.'))
        
        # Archivar la denuncia
        self.write({'activo': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Denuncia Descartada'),
                'message': _('La denuncia ha sido descartada sin tomar acciones.'),
                'type': 'info',
                'sticky': False,
            }
        }
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    
    def _notificar_empleados(self):
        """Notificar a TODOS los empleados sobre la nueva denuncia"""
        self.ensure_one()
        
        # Obtener todos los usuarios empleados (usuarios internos de Odoo)
        empleados = self.env['res.users'].search([
            ('share', '=', False),  # Solo usuarios internos, no usuarios portal
            ('active', '=', True)
        ])
        
        if empleados:
            # Determinar qué se denunció
            objeto_denunciado = ''
            if self.tipo_objeto == 'producto':
                objeto_denunciado = _('Producto: %s') % self.nombre_articulo
            elif self.tipo_objeto == 'comentario':
                objeto_denunciado = _('Comentario: %s') % (self.texto_comentario[:50] + '...' if len(self.texto_comentario) > 50 else self.texto_comentario)
            
            # Crear mensaje de notificación
            mensaje = _(
                '<p><strong>Nueva Denuncia Recibida</strong></p>'
                '<ul>'
                '<li><strong>ID:</strong> %s</li>'
                '<li><strong>Denunciado por:</strong> %s</li>'
                '<li><strong>Objeto:</strong> %s</li>'
                '<li><strong>Fecha:</strong> %s</li>'
                '</ul>'
                '<p><strong>Mensaje:</strong><br/>%s</p>'
                '<p><em>Revisa la denuncia y decide si eliminar el contenido o descartarla.</em></p>'
            ) % (
                self.id_reporte,
                self.nombre_reportador,
                objeto_denunciado,
                self.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                self.mensaje
            )
            
            # Enviar notificación a todos los empleados
            self.message_notify(
                partner_ids=empleados.mapped('partner_id').ids,
                subject=_('Nueva Denuncia: %s') % self.id_reporte,
                body=mensaje,
                notification_type='inbox'
            )
    
    # ============================================
    # ACCIONES DE VISTA
    # ============================================
    
    def action_ver_objeto_denunciado(self):
        """Abrir el objeto denunciado para revisarlo"""
        self.ensure_one()
        
        if self.tipo_objeto == 'producto' and self.id_articulo:
            return {
                'name': _('Producto Denunciado'),
                'type': 'ir.actions.act_window',
                'res_model': 'second_market.article',
                'view_mode': 'form',
                'res_id': self.id_articulo.id,
                'target': 'current',
            }
        
        elif self.tipo_objeto == 'comentario' and self.id_comentario:
            return {
                'name': _('Comentario Denunciado'),
                'type': 'ir.actions.act_window',
                'res_model': 'second.market.comment',
                'view_mode': 'form',
                'res_id': self.id_comentario.id,
                'target': 'current',
            }