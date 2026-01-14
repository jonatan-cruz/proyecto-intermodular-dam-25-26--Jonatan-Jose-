# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SecondMarketUser(models.Model):
    _name = 'second.market.user'
    _description = 'Usuario de Second Market'

    id_usuario = fields.Char(
        string='ID Usuario', 
        size=7, 
        required=True, 
        help='ID de usuario de 7 dígitos'
    )

    name = fields.Char(
        string='Nombre', 
        size=50, 
        required=True
    )

    contraseña = fields.Char(
        string='Contraseña', 
        size=50, 
        required=True
    )

    productos_en_venta = fields.Integer(
        string='Productos en Venta', 
        default=0
    )

    productos_vendidos = fields.Integer(
        string='Productos Vendidos', 
        default=0
    )

    productos_comprados = fields.Integer(
        string='Productos Comprados', 
        default=0
    )

    antiguedad = fields.Integer(
        string='Antigüedad (años)', 
        default=0
    )

    # Validación para el ID de usuario (7 dígitos)
    @api.constrains('id_usuario')
    def _check_id_usuario(self):
        for rec in self:
            if not rec.id_usuario.isdigit() or len(rec.id_usuario) != 7:
                raise ValidationError('El ID de usuario debe tener exactamente 7 dígitos numéricos.')

    # Validación para la contraseña (mínimo 8 caracteres)
    @api.constrains('contraseña')
    def _check_contraseña(self):
        for rec in self:
            if len(rec.contraseña) < 8:
                raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
            
    def action_eliminar_usuario(self):
        for record in self:
            record.unlink()
        return True
