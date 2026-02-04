# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import logging
from passlib.context import CryptContext

# Configuración de hashing (mismo que en login.py)
crypt_context = CryptContext(schemes=["pbkdf2_sha512", "plaintext"], deprecated="auto")

from .auth_controller import verify_jwt_token, get_token_from_request, get_authenticated_user_with_refresh

_logger = logging.getLogger(__name__)


class SecondMarketUserController(http.Controller):
    """Controlador para gestión de perfiles de usuario"""

    def _get_authenticated_user(self):
        """
        Obtener usuario autenticado desde el token
        Incluye renovación automática de tokens si es necesario
        
        Returns:
            dict: {
                'user_data': dict con datos del usuario,
                'new_token': str (opcional, solo si se renovó)
            }
            None: Si no está autenticado
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/users/profile', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_my_profile(self, **kwargs):
        """Obtener perfil del usuario autenticado"""
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado',
                    'error_code': 'UNAUTHORIZED'
                }
            
            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            
            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])
            
            if not user.exists():
                return {
                    'success': False,
                    'message': 'Usuario no encontrado',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            profile_data = {
                'id': user.id,
                'id_usuario': user.id_usuario,
                'name': user.name,
                'login': user.login,
                'telefono': user.telefono,
                'ubicacion': user.ubicacion,
                'biografia': user.biografia,
                'avatar': user.avatar.decode('utf-8') if user.avatar else None,
                'calificacion_promedio': user.calificacion_promedio,
                'total_valoraciones': user.total_valoraciones,
                'productos_en_venta': user.productos_en_venta,
                'productos_vendidos': user.productos_vendidos,
                'productos_comprados': user.productos_comprados,
                'antiguedad': user.antiguedad,
                'fecha_registro': user.fecha_registro.isoformat() if user.fecha_registro else None,
                'activo': user.activo
            }
            
            response_data = {
                'success': True,
                'data': profile_data
            }
            
            # Agregar nuevo token en la respuesta si fue renovado
            if new_token:
                response_data['new_token'] = new_token
            
            return response_data
            
        except Exception as e:
            _logger.error(f"Error al obtener perfil: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener perfil',
                'error_code': 'GET_PROFILE_ERROR'
            }

    @http.route('/api/v1/users/profile', type='json', auth='public', methods=['PUT'], csrf=False, cors='*')
    def update_profile(self, **kwargs):
        """
        Actualizar perfil del usuario autenticado
        
        Parámetros opcionales:
        - name: str
        - telefono: str
        - ubicacion: str
        - biografia: str
        - avatar: str (base64)
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado',
                    'error_code': 'UNAUTHORIZED'
                }
            
            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            
            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])
            
            if not user.exists():
                return {
                    'success': False,
                    'message': 'Usuario no encontrado',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            data = request.params or request.httprequest.get_json(force=True) or {}
            
            # Campos actualizables
            update_vals = {}
            updatable_fields = ['name', 'telefono', 'ubicacion', 'biografia', 'avatar']
            
            for field in updatable_fields:
                if field in data and data[field] is not None:
                    update_vals[field] = data[field]
            
            if update_vals:
                user.sudo().write(update_vals)
                _logger.info(f"Perfil actualizado para usuario {user.id}")
            
            response = {
                'success': True,
                'message': 'Perfil actualizado exitosamente'
            }
            
            # Agregar nuevo token en la respuesta si fue renovado
            if new_token:
                response['new_token'] = new_token
            
            return response
            
        except Exception as e:
            _logger.error(f"Error al actualizar perfil: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al actualizar perfil',
                'error_code': 'UPDATE_PROFILE_ERROR',
                'error_detail': str(e)
            }

    @http.route('/api/v1/users/change-password', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def change_password(self, **kwargs):
        """
        Cambiar contraseña del usuario
        
        Parámetros requeridos:
        - current_password: str
        - new_password: str
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado',
                    'error_code': 'UNAUTHORIZED'
                }
            
            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            
            data = request.params or request.httprequest.get_json(force=True) or {}
            
            if not data.get('current_password') or not data.get('new_password'):
                return {
                    'success': False,
                    'message': 'Se requiere la contraseña actual y la nueva',
                    'error_code': 'MISSING_FIELD'
                }
            
            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])
            
            if not user.exists():
                return {
                    'success': False,
                    'message': 'Usuario no encontrado',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Verificar contraseña actual
            if not crypt_context.verify(data['current_password'], user.password):
                return {
                    'success': False,
                    'message': 'Contraseña actual incorrecta',
                    'error_code': 'INVALID_PASSWORD'
                }
            
            # Validar nueva contraseña
            if len(data['new_password']) < 8:
                return {
                    'success': False,
                    'message': 'La nueva contraseña debe tener al menos 8 caracteres',
                    'error_code': 'PASSWORD_TOO_SHORT'
                }
            
            # Actualizar contraseña
            user.sudo().write({'password': data['new_password']})
            
            _logger.info(f"Contraseña cambiada para usuario {user.id}")
            
            response = {
                'success': True,
                'message': 'Contraseña actualizada exitosamente'
            }
            
            # Agregar nuevo token en la respuesta si fue renovado
            if new_token:
                response['new_token'] = new_token
            
            return response
            
        except Exception as e:
            _logger.error(f"Error al cambiar contraseña: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al cambiar contraseña',
                'error_code': 'CHANGE_PASSWORD_ERROR'
            }

    @http.route('/api/v1/users/<int:user_id>', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_user_profile(self, user_id, **kwargs):
        """Obtener perfil público de un usuario"""
        try:
            user = request.env['second_market.user'].sudo().browse(user_id)
            
            if not user.exists() or not user.activo:
                return {
                    'success': False,
                    'message': 'Usuario no encontrado',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            profile_data = {
                'id': user.id,
                'id_usuario': user.id_usuario,
                'name': user.name,
                'ubicacion': user.ubicacion,
                'biografia': user.biografia,
                'avatar': user.avatar.decode('utf-8') if user.avatar else None,
                'calificacion_promedio': user.calificacion_promedio,
                'total_valoraciones': user.total_valoraciones,
                'productos_en_venta': user.productos_en_venta,
                'productos_vendidos': user.productos_vendidos,
                'antiguedad': user.antiguedad,
                'fecha_registro': user.fecha_registro.isoformat() if user.fecha_registro else None
            }
            
            return {
                'success': True,
                'data': profile_data
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener perfil de usuario: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener perfil',
                'error_code': 'GET_USER_PROFILE_ERROR'
            }

    @http.route('/api/v1/users/<int:user_id>/articles', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_user_articles(self, user_id, **kwargs):
        """Obtener artículos publicados de un usuario"""
        try:
            data = request.params
            limit = data.get('limit', 20)
            offset = data.get('offset', 0)
            
            articles = request.env['second_market.article'].sudo().search([
                ('id_propietario', '=', user_id),
                ('estado_publicacion', '=', 'publicado'),
                ('activo', '=', True)
            ], limit=limit, offset=offset, order='create_date desc')
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    'id': article.id,
                    'codigo': article.codigo,
                    'nombre': article.nombre,
                    'descripcion': article.descripcion,
                    'precio': article.precio,
                    'estado_producto': article.estado_producto,
                    'localidad': article.localidad,
                    'imagen_principal': article.imagen_principal.decode('utf-8') if article.imagen_principal else None,
                    'conteo_vistas': article.conteo_vistas,
                    'create_date': article.create_date.isoformat() if article.create_date else None
                })
            
            return {
                'success': True,
                'data': {'articles': articles_data}
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener artículos de usuario: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener artículos',
                'error_code': 'GET_USER_ARTICLES_ERROR'
            }

    @http.route('/api/v1/users/<int:user_id>/ratings', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_user_ratings(self, user_id, **kwargs):
        """Obtener valoraciones de un usuario"""
        try:
            data = request.params
            limit = data.get('limit', 10)
            offset = data.get('offset', 0)
            
            ratings = request.env['second_market.rating'].sudo().search([
                ('id_usuario', '=', user_id),
                ('activo', '=', True)
            ], limit=limit, offset=offset, order='fecha_hora desc')
            
            ratings_data = []
            for rating in ratings:
                ratings_data.append({
                    'id': rating.id,
                    'calificacion': rating.calificacion,
                    'comentario': rating.comentario,
                    'fecha_hora': rating.fecha_hora.isoformat() if rating.fecha_hora else None,
                    'valorador': {
                        'id': rating.id_valorador.id,
                        'nombre': rating.id_valorador.name
                    }
                })
            
            return {
                'success': True,
                'data': {
                    'ratings': ratings_data,
                    'calificacion_promedio': request.env['second_market.user'].sudo().browse(user_id).calificacion_promedio
                }
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener valoraciones de usuario: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener valoraciones',
                'error_code': 'GET_USER_RATINGS_ERROR'
            }

    @http.route('/api/v1/users/statistics', type='json', auth='public', methods=['GET', 'POST'], csrf=False)
    def get_my_statistics(self, **kwargs):
        """Obtener estadísticas detalladas de actividad del usuario autenticado"""
        try:
            auth_data = self._get_authenticated_user()
            _logger.debug(f"_get_authenticated_user() => {auth_data}")

            user = auth_data.get('user_data', {}).get('user')

            if not user:
                return {
                    'success': False,
                    'message': 'No autenticado',
                    'error_code': 'UNAUTHORIZED'
                }

            stats = {
                'productos_en_venta': user.productos_en_venta,
                'productos_vendidos': user.productos_vendidos,
                'productos_comprados': user.productos_comprados,
                'calificacion_promedio': user.calificacion_promedio,
                'total_valoraciones': user.total_valoraciones,
                'antiguedad': user.antiguedad,

                'total_vistas': sum(user.ids_articulos_venta.mapped('conteo_vistas')),
                'comentarios_recibidos': len(user.ids_comentarios_recibidos.filtered(lambda c: c.activo)),
                'comentarios_enviados': len(user.ids_comentarios_enviados.filtered(lambda c: c.activo)),

                'ventas_pendientes': len(user.ids_ventas.filtered(lambda v: v.estado == 'pendiente')),
                'ventas_confirmadas': len(user.ids_ventas.filtered(lambda v: v.estado == 'confirmada')),
                'ventas_completadas': len(user.ids_ventas.filtered(lambda v: v.estado == 'completada')),

                'compras_pendientes': len(user.ids_compras.filtered(lambda c: c.estado == 'pendiente')),
                'compras_confirmadas': len(user.ids_compras.filtered(lambda c: c.estado == 'confirmada')),
                'compras_completadas': len(user.ids_compras.filtered(lambda c: c.estado == 'completada')),

                'articulos_borradores': len(user.ids_articulos_venta.filtered(lambda a: a.estado_publicacion == 'borrador')),
                'articulos_publicados': len(user.ids_articulos_venta.filtered(lambda a: a.estado_publicacion == 'publicado')),
                'articulos_vendidos': len(user.ids_articulos_venta.filtered(lambda a: a.estado_publicacion == 'vendido')),
            }

            return {
                'success': True,
                'data': stats
            }

        except Exception as e:
            _logger.error(f"Error al obtener estadísticas: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': str(e),
                'error_code': 'GET_STATISTICS_ERROR'
            }

    @http.route('/api/v1/users/deactivate', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def deactivate_account(self, **kwargs):
        """
        Desactivar cuenta del usuario
        
        Parámetros requeridos:
        - password: str (confirmación)
        """
        try:
            user_data = self._get_authenticated_user()
            if not user_data:
                return {
                    'success': False,
                    'message': 'No autenticado',
                    'error_code': 'UNAUTHORIZED'
                }
            
            data = request.params or request.httprequest.get_json(force=True) or {}
            
            if not data.get('password'):
                return {
                    'success': False,
                    'message': 'Se requiere la contraseña para confirmar',
                    'error_code': 'MISSING_FIELD'
                }
            
            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])
            
            if not user.exists():
                return {
                    'success': False,
                    'message': 'Usuario no encontrado',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            # Verificar contraseña
            if not crypt_context.verify(data['password'], user.password):
                return {
                    'success': False,
                    'message': 'Contraseña incorrecta',
                    'error_code': 'INVALID_PASSWORD'
                }
            
            # Desactivar usuario
            user.sudo().write({'activo': False})
            
            # Desactivar todos sus artículos
            user.ids_articulos_venta.sudo().write({'activo': False})
            
            _logger.info(f"Usuario desactivado: {user.id}")
            
            return {
                'success': True,
                'message': 'Cuenta desactivada exitosamente'
            }
            
        except Exception as e:
            _logger.error(f"Error al desactivar cuenta: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al desactivar cuenta',
                'error_code': 'DEACTIVATE_ACCOUNT_ERROR'
            }
