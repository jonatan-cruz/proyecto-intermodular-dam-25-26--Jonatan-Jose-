# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import logging

from .auth_controller import verify_jwt_token, get_token_from_request, get_authenticated_user_with_refresh

_logger = logging.getLogger(__name__)


class SecondMarketCommentController(http.Controller):
    """Controlador para gestión de comentarios"""

    def _get_authenticated_user(self):
        """
        Obtener usuario autenticado desde el token
        Incluye renovación automática de tokens si es necesario
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/comments', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_comment(self, **kwargs):
        """
        Crear un nuevo comentario público en un artículo.
        El propietario del artículo recibirá una notificación automática.
        Requiere autenticación JWT.
        
        Parámetros requeridos:
        - articulo_id: int
        - texto: str
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
            
            if not data.get('articulo_id') or not data.get('texto'):
                return {
                    'success': False,
                    'message': 'El artículo y el texto son requeridos',
                    'error_code': 'MISSING_FIELD'
                }
            
            article = request.env['second_market.article'].sudo().browse(data['articulo_id'])
            
            if not article.exists():
                return {
                    'success': False,
                    'message': 'Artículo no encontrado',
                    'error_code': 'ARTICLE_NOT_FOUND'
                }
            
            # Crear comentario
            comment = request.env['second_market.comment'].sudo().create({
                'id_articulo': article.id,
                'id_emisor': user_data['user_id'],
                'id_receptor': article.id_propietario.id,
                'texto': data['texto']
            })
            
            response = {
                'success': True,
                'message': 'Comentario creado exitosamente',
                'data': {
                    'comment_id': comment.id,
                    'id_mensaje': comment.id_mensaje
                }
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al crear comentario: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al crear comentario',
                'error_code': 'CREATE_COMMENT_ERROR'
            }

    @http.route('/api/v1/comments/<int:comment_id>/read', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def mark_comment_read(self, comment_id, **kwargs):
        """Marcar comentario como leído"""
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
            
            comment = request.env['second_market.comment'].sudo().browse(comment_id)
            
            if not comment.exists():
                return {
                    'success': False,
                    'message': 'Comentario no encontrado',
                    'error_code': 'COMMENT_NOT_FOUND'
                }
            
            # Verificar que sea el receptor
            if comment.id_receptor.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes permiso',
                    'error_code': 'FORBIDDEN'
                }
            
            comment.sudo().leer()
            
            response = {
                'success': True,
                'message': 'Comentario marcado como leído'
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al marcar comentario: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al marcar comentario',
                'error_code': 'READ_COMMENT_ERROR'
            }

    @http.route('/api/v1/comments/<int:comment_id>', type='json', auth='public', methods=['DELETE'], csrf=False, cors='*')
    def delete_comment(self, comment_id, **kwargs):
        """Eliminar comentario"""
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
            
            comment = request.env['second_market.comment'].sudo().browse(comment_id)
            
            if not comment.exists():
                return {
                    'success': False,
                    'message': 'Comentario no encontrado',
                    'error_code': 'COMMENT_NOT_FOUND'
                }
            
            # Solo el emisor puede eliminar
            if comment.id_emisor.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes permiso',
                    'error_code': 'FORBIDDEN'
                }
            
            comment.sudo().eliminar()
            
            response = {
                'success': True,
                'message': 'Comentario eliminado'
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al eliminar comentario: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al eliminar comentario',
                'error_code': 'DELETE_COMMENT_ERROR'
            }

    @http.route('/api/v1/comments/received', type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_received_comments(self, **kwargs):
        """Obtener comentarios recibidos por el usuario"""
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
            
            data = request.httprequest.get_json(force=True) or {}
            limit = data.get('limit', 20)
            offset = data.get('offset', 0)
            
            comments = request.env['second_market.comment'].sudo().search([
                ('id_receptor', '=', user_data['user_id']),
                ('activo', '=', True)
            ], limit=limit, offset=offset, order='fecha_hora desc')
            
            comments_data = []
            for comment in comments:
                comments_data.append({
                    'id': comment.id,
                    'texto': comment.texto,
                    'leido': comment.leido,
                    'fecha_hora': comment.fecha_hora.isoformat() if comment.fecha_hora else None,
                    'emisor': {
                        'id': comment.id_emisor.id,
                        'nombre': comment.id_emisor.name
                    },
                    'articulo': {
                        'id': comment.id_articulo.id,
                        'nombre': comment.id_articulo.nombre
                    }
                })
            
            response = {
                'success': True,
                'data': {'comments': comments_data}
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al obtener comentarios: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener comentarios',
                'error_code': 'GET_COMMENTS_ERROR'
            }


class SecondMarketPurchaseController(http.Controller):
    """Controlador para gestión de compras"""

    def _get_authenticated_user(self):
        """
        Obtener usuario autenticado desde el token
        Incluye renovación automática de tokens si es necesario
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/purchases', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_purchase(self, **kwargs):
        """
        Iniciar el proceso de compra de un artículo.
        Cambia el estado del artículo a 'reservado' y notifica al vendedor.
        Requiere autenticación JWT. El comprador no puede ser el propietario.
        
        Parámetros requeridos:
        - articulo_id: int
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
            
            if not data.get('articulo_id'):
                return {
                    'success': False,
                    'message': 'El artículo es requerido',
                    'error_code': 'MISSING_FIELD'
                }
            
            article = request.env['second_market.article'].sudo().browse(data['articulo_id'])
            
            if not article.exists():
                return {
                    'success': False,
                    'message': 'Artículo no encontrado',
                    'error_code': 'ARTICLE_NOT_FOUND'
                }
            
            if article.estado_publicacion != 'publicado':
                return {
                    'success': False,
                    'message': 'Este artículo no está disponible para compra',
                    'error_code': 'ARTICLE_NOT_AVAILABLE'
                }
            
            if article.id_propietario.id == user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No puedes comprar tu propio artículo',
                    'error_code': 'SELF_PURCHASE'
                }
            
            # Crear compra
            purchase = request.env['second_market.purchase'].sudo().create({
                'id_comprador': user_data['user_id'],
                'id_vendedor': article.id_propietario.id,
                'id_articulo': article.id,
                'precio': article.precio,
                'estado': 'pendiente'
            })
            
            # Cambiar estado del artículo
            article.sudo().write({'estado_publicacion': 'reservado'})
            
            response = {
                'success': True,
                'message': 'Compra creada exitosamente',
                'data': {
                    'purchase_id': purchase.id,
                    'id_compra': purchase.id_compra,
                    'precio': purchase.precio
                }
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al crear compra: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al crear compra',
                'error_code': 'CREATE_PURCHASE_ERROR'
            }

    @http.route('/api/v1/purchases/<int:purchase_id>/confirm', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def confirm_purchase(self, purchase_id, **kwargs):
        """Confirmar una compra (vendedor confirma pago)"""
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
            
            purchase = request.env['second_market.purchase'].sudo().browse(purchase_id)
            
            if not purchase.exists():
                return {
                    'success': False,
                    'message': 'Compra no encontrada',
                    'error_code': 'PURCHASE_NOT_FOUND'
                }
            
            # Solo el vendedor puede confirmar
            if purchase.id_vendedor.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'Solo el vendedor puede confirmar',
                    'error_code': 'FORBIDDEN'
                }
            
            purchase.sudo().confirmar_transaccion()
            
            response = {
                'success': True,
                'message': 'Compra confirmada exitosamente'
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al confirmar compra: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al confirmar compra',
                'error_code': 'CONFIRM_PURCHASE_ERROR'
            }

    @http.route('/api/v1/purchases/<int:purchase_id>/cancel', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def cancel_purchase(self, purchase_id, **kwargs):
        """Cancelar una compra"""
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
            
            purchase = request.env['second_market.purchase'].sudo().browse(purchase_id)
            
            if not purchase.exists():
                return {
                    'success': False,
                    'message': 'Compra no encontrada',
                    'error_code': 'PURCHASE_NOT_FOUND'
                }
            
            # Comprador o vendedor pueden cancelar
            if purchase.id_comprador.id != user_data['user_id'] and purchase.id_vendedor.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes permiso',
                    'error_code': 'FORBIDDEN'
                }
            
            purchase.sudo().cancelar_compra()
            
            response = {
                'success': True,
                'message': 'Compra cancelada'
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al cancelar compra: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al cancelar compra',
                'error_code': 'CANCEL_PURCHASE_ERROR'
            }

    @http.route('/api/v1/purchases/my-purchases', type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_my_purchases(self, **kwargs):
        """Obtener compras realizadas por el usuario"""
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
            
            purchases = request.env['second_market.purchase'].sudo().search([
                ('id_comprador', '=', user_data['user_id'])
            ], order='fecha_hora desc')
            
            purchases_data = []
            for purchase in purchases:
                purchases_data.append({
                    'id': purchase.id,
                    'id_compra': purchase.id_compra,
                    'precio': purchase.precio,
                    'estado': purchase.estado,
                    'fecha_hora': purchase.fecha_hora.isoformat() if purchase.fecha_hora else None,
                    'articulo': {
                        'id': purchase.id_articulo.id,
                        'nombre': purchase.id_articulo.nombre,
                        'codigo': purchase.id_articulo.codigo
                    },
                    'vendedor': {
                        'id': purchase.id_vendedor.id,
                        'nombre': purchase.id_vendedor.name
                    }
                })
            
            response = {
                'success': True,
                'data': {'purchases': purchases_data}
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al obtener compras: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener compras',
                'error_code': 'GET_PURCHASES_ERROR'
            }

    @http.route('/api/v1/purchases/my-sales', type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_my_sales(self, **kwargs):
        """Obtener ventas del usuario"""
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
            
            sales = request.env['second_market.purchase'].sudo().search([
                ('id_vendedor', '=', user_data['user_id'])
            ], order='fecha_hora desc')
            
            sales_data = []
            for sale in sales:
                sales_data.append({
                    'id': sale.id,
                    'id_compra': sale.id_compra,
                    'precio': sale.precio,
                    'estado': sale.estado,
                    'fecha_hora': sale.fecha_hora.isoformat() if sale.fecha_hora else None,
                    'articulo': {
                        'id': sale.id_articulo.id,
                        'nombre': sale.id_articulo.nombre,
                        'codigo': sale.id_articulo.codigo
                    },
                    'comprador': {
                        'id': sale.id_comprador.id,
                        'nombre': sale.id_comprador.name
                    }
                })
            
            response = {
                'success': True,
                'data': {'sales': sales_data}
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al obtener ventas: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener ventas',
                'error_code': 'GET_SALES_ERROR'
            }


class SecondMarketRatingController(http.Controller):
    """Controlador para gestión de valoraciones"""

    def _get_authenticated_user(self):
        """
        Obtener usuario autenticado desde el token
        Incluye renovación automática de tokens si es necesario
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/ratings', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_rating(self, **kwargs):
        """
        Crear una valoración
        
        Parámetros requeridos:
        - usuario_id: int (usuario a valorar)
        - calificacion: int (1-5)
        - comentario: str (opcional)
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
            
            if not data.get('usuario_id') or not data.get('calificacion'):
                return {
                    'success': False,
                    'message': 'El usuario y la calificación son requeridos',
                    'error_code': 'MISSING_FIELD'
                }
            
            rated_user = request.env['second_market.user'].sudo().browse(data['usuario_id'])
            
            if not rated_user.exists():
                return {
                    'success': False,
                    'message': 'Usuario no encontrado',
                    'error_code': 'USER_NOT_FOUND'
                }
            
            if rated_user.id == user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No puedes valorarte a ti mismo',
                    'error_code': 'SELF_RATING'
                }
            
            # Crear valoración
            rating = request.env['second_market.rating'].sudo().create({
                'id_usuario': data['usuario_id'],
                'id_valorador': user_data['user_id'],
                'calificacion': str(data['calificacion']),
                'comentario': data.get('comentario', '')
            })
            
            response = {
                'success': True,
                'message': 'Valoración creada exitosamente',
                'data': {
                    'rating_id': rating.id
                }
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al crear valoración: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': str(e) if 'ya has valorado' in str(e).lower() else 'Error al crear valoración',
                'error_code': 'CREATE_RATING_ERROR'
            }

    @http.route('/api/v1/ratings/user/<int:user_id>', type='json', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_user_ratings(self, user_id, **kwargs):
        """Obtener valoraciones de un usuario"""
        try:
            ratings = request.env['second_market.rating'].sudo().search([
                ('id_usuario', '=', user_id),
                ('activo', '=', True)
            ], order='fecha_hora desc')
            
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
                'data': {'ratings': ratings_data}
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener valoraciones: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener valoraciones',
                'error_code': 'GET_RATINGS_ERROR'
            }
