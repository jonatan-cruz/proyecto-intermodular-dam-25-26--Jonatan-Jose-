# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SecondMarketPurchase(models.Model):
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
        """Validar que comprador y vendedor no sean el mismo"""
        for compra in self:
            if compra.id_comprador == compra.id_vendedor:
                raise ValidationError(_('El comprador y el vendedor no pueden ser el mismo usuario.'))
    
    @api.constrains('precio')
    def _check_precio(self):
        """Validar precio válido"""
        for compra in self:
            if compra.precio <= 0:
                raise ValidationError(_('El precio debe ser mayor que 0.'))

    @api.constrains('id_articulo', 'id_vendedor')
    def _check_vendedor_articulo(self):
        """Validar que el vendedor sea el dueño del artículo"""
        for compra in self:
            if compra.id_articulo.id_propietario != compra.id_vendedor:
                raise ValidationError(_('El vendedor debe ser el propietario del artículo.'))
    
    # ============================================
    # MÉTODOS CREATE Y WRITE
    # ============================================
    
    @api.model
    def create(self, vals):
        """Generar ID único al crear"""
        if vals.get('id_compra', _('Nuevo')) == _('Nuevo'):
            vals['id_compra'] = self.env['ir.sequence'].next_by_code('second_market.purchase') or _('Nuevo')
        
        compra = super(SecondMarketPurchase, self).create(vals)
        
        # Notificar a comprador y vendedor
        compra._notificar_nueva_compra()
        
        return compra
    
    # ============================================
    # MÉTODOS PRINCIPALES
    # ============================================
    
    def realizar_compra(self):
        """Iniciar el proceso de compra"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Esta compra está cancelada.'))
        
        if self.estado != 'pendiente':
            raise UserError(_('Esta compra ya ha sido procesada.'))
            
        if self.id_articulo.estado_publicacion != 'publicado':
            raise UserError(_('El artículo ya no está disponible (Estado: %s).') % self.id_articulo.estado_publicacion)
        
        # Cambiar estado de la compra
        self.write({'estado': 'confirmada'})
        
        # Cambiar estado del artículo a reservado
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
        """Confirmar que la transacción se ha completado"""
        self.ensure_one()
        
        if not self.activo:
            raise UserError(_('Esta compra está cancelada.'))
        
        if self.estado == 'completada':
            raise UserError(_('Esta transacción ya está completada.'))
        
        # Marcar como completada
        self.write({'estado': 'completada'})
        
        # Actualizar artículo
        self.id_articulo.write({'estado_publicacion': 'vendido'})
        
        # Notificar
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
        """Cancelar la compra"""
        self.ensure_one()
        
        if self.estado == 'completada':
            raise UserError(_('No puedes cancelar una transacción completada.'))
        
        self.write({
            'estado': 'cancelada',
            'activo': False
        })
        
        # Volver a publicar el artículo si estaba reservado
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
        """Notificar a comprador y vendedor"""
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
        """Notificar que la transacción se completó"""
        self.ensure_one()
        mensaje = _("Transacción completada exitosamente el %s.") % fields.Datetime.now()
        self.message_post(body=mensaje, subtype_xmlid='mail.mt_note')
    
    def action_ver_articulo(self):
        """Ver el artículo de la compra"""
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
        """Ver perfil del comprador"""
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
        """Ver perfil del vendedor"""
        self.ensure_one()
        return {
            'name': _('Vendedor'),
            'type': 'ir.actions.act_window',
            'res_model': 'second_market.user',
            'view_mode': 'form',
            'res_id': self.id_vendedor.id,
            'target': 'current',
        }