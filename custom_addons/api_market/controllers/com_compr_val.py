# -*- coding: utf-8 -*-

"""
Controladores de comentarios, compras y valoraciones para la API REST de Second Market.

**Endpoints de Comentarios** (``SecondMarketCommentController``):

- ``POST   /api/v1/comments``                     — Publicar un comentario en un artículo.
- ``POST   /api/v1/comments/<id>/read``           — Marcar un comentario como leído.
- ``DELETE /api/v1/comments/<id>``                — Eliminar (borrado lógico) un comentario.
- ``POST   /api/v1/comments/received``            — Listar comentarios recibidos.

**Endpoints de Compras** (``SecondMarketPurchaseController``):

- ``POST /api/v1/purchases``                      — Iniciar una compra.
- ``POST /api/v1/purchases/<id>/confirm``         — Confirmar una compra (vendedor).
- ``POST /api/v1/purchases/<id>/cancel``          — Cancelar una compra.
- ``POST /api/v1/purchases/my-purchases``         — Listar compras del usuario.
- ``POST /api/v1/purchases/my-sales``             — Listar ventas del usuario.

**Endpoints de Valoraciones** (``SecondMarketRatingController``):

- ``POST /api/v1/ratings``                        — Crear una valoración.
- ``POST /api/v1/ratings/user/<id>``              — Listar valoraciones de un usuario.

Todos los endpoints requieren el header ``Authorization: Bearer <token>``,
excepto ``GET /api/v1/ratings/user/<id>`` que es público.
"""

from odoo import http, _
from odoo.http import request
import logging

from .auth_controller import verify_jwt_token, get_token_from_request, get_authenticated_user_with_refresh

_logger = logging.getLogger(__name__)


class SecondMarketCommentController(http.Controller):
    """Controlador para la gestión de comentarios en artículos.

    Los comentarios vinculan a un emisor, un receptor (el propietario del
    artículo) y un artículo concreto. El receptor recibe una notificación
    en el chatter de Odoo al crearse el comentario.
    """

    def _get_authenticated_user(self):
        """Obtener el usuario autenticado a partir del token JWT del request.

        :return: Diccionario ``{'user_data': dict, 'new_token': str}`` o ``None``.
        :rtype: dict or None
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/comments', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_comment(self, **kwargs):
        """Publicar un comentario público en un artículo.

        El receptor del comentario es automáticamente el propietario del artículo.
        Se envía una notificación en el chatter del artículo y del receptor.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON:**

        .. code-block:: json

            {
                "articulo_id": 42,
                "texto": "¿Tiene algún defecto el artículo?"
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``message`` y ``data.comment_id``.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            data = request.params or request.httprequest.get_json(force=True) or {}

            if not data.get('articulo_id') or not data.get('texto'):
                return {'success': False, 'message': 'El artículo y el texto son requeridos', 'error_code': 'MISSING_FIELD'}

            article = request.env['second_market.article'].sudo().browse(data['articulo_id'])
            if not article.exists():
                return {'success': False, 'message': 'Artículo no encontrado', 'error_code': 'ARTICLE_NOT_FOUND'}

            comment = request.env['second_market.comment'].sudo().create({
                'id_articulo': article.id,
                'id_emisor': user_data['user_id'],
                'id_receptor': article.id_propietario.id,
                'texto': data['texto']
            })

            response = {
                'success': True,
                'message': 'Comentario creado exitosamente',
                'data': {'comment_id': comment.id, 'id_mensaje': comment.id_mensaje}
            }
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al crear comentario: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al crear comentario', 'error_code': 'CREATE_COMMENT_ERROR'}

    @http.route('/api/v1/comments/<int:comment_id>/read', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def mark_comment_read(self, comment_id, **kwargs):
        """Marcar un comentario como leído.

        Solo el receptor del comentario puede marcarlo como leído.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param comment_id: ID del comentario a marcar como leído.
        :type comment_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            comment = request.env['second_market.comment'].sudo().browse(comment_id)
            if not comment.exists():
                return {'success': False, 'message': 'Comentario no encontrado', 'error_code': 'COMMENT_NOT_FOUND'}

            if comment.id_receptor.id != user_data['user_id']:
                return {'success': False, 'message': 'No tienes permiso', 'error_code': 'FORBIDDEN'}

            comment.sudo().leer()

            response = {'success': True, 'message': 'Comentario marcado como leído'}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al marcar comentario: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al marcar comentario', 'error_code': 'READ_COMMENT_ERROR'}

    @http.route('/api/v1/comments/<int:comment_id>', type='json', auth='public', methods=['DELETE'], csrf=False, cors='*')
    def delete_comment(self, comment_id, **kwargs):
        """Eliminar (borrado lógico) un comentario.

        Solo el emisor del comentario puede eliminarlo. Se establece
        ``activo = False`` sin borrar el registro de la base de datos.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param comment_id: ID del comentario a eliminar.
        :type comment_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            comment = request.env['second_market.comment'].sudo().browse(comment_id)
            if not comment.exists():
                return {'success': False, 'message': 'Comentario no encontrado', 'error_code': 'COMMENT_NOT_FOUND'}

            if comment.id_emisor.id != user_data['user_id']:
                return {'success': False, 'message': 'No tienes permiso', 'error_code': 'FORBIDDEN'}

            comment.sudo().eliminar()

            response = {'success': True, 'message': 'Comentario eliminado'}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al eliminar comentario: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al eliminar comentario', 'error_code': 'DELETE_COMMENT_ERROR'}

    @http.route('/api/v1/comments/received', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_received_comments(self, **kwargs):
        """Obtener los comentarios recibidos por el usuario autenticado.

        Admite paginación mediante los parámetros opcionales ``limit`` y ``offset``.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param kwargs: Parámetros opcionales: ``limit`` (por defecto 20)
            y ``offset`` (por defecto 0).
        :return: Diccionario con ``success`` y ``data.comments``.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

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
                    'emisor': {'id': comment.id_emisor.id, 'nombre': comment.id_emisor.name},
                    'articulo': {'id': comment.id_articulo.id, 'nombre': comment.id_articulo.nombre}
                })

            response = {'success': True, 'data': {'comments': comments_data}}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al obtener comentarios: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener comentarios', 'error_code': 'GET_COMMENTS_ERROR'}


class SecondMarketPurchaseController(http.Controller):
    """Controlador para la gestión del ciclo de vida de compras.

    El flujo típico de una compra es:

    1. El comprador llama a ``POST /api/v1/purchases`` → estado ``pendiente``, artículo ``reservado``.
    2. El vendedor llama a ``POST /api/v1/purchases/<id>/confirm`` → estado ``completada``, artículo ``vendido``.
    3. Cualquiera puede llamar a ``POST /api/v1/purchases/<id>/cancel`` → estado ``cancelada``, artículo vuelve a ``publicado``.
    """

    def _get_authenticated_user(self):
        """Obtener el usuario autenticado a partir del token JWT del request.

        :return: Diccionario ``{'user_data': dict, 'new_token': str}`` o ``None``.
        :rtype: dict or None
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/purchases', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_purchase(self, **kwargs):
        """Iniciar el proceso de compra de un artículo.

        Crea la compra en estado ``pendiente`` y cambia el artículo a ``reservado``.
        El comprador no puede ser el propietario del artículo.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON:**

        .. code-block:: json

            { "articulo_id": 42 }

        **Respuesta exitosa:**

        .. code-block:: json

            {
                "success": true,
                "data": {
                    "purchase_id": 5,
                    "id_compra": "0000005",
                    "precio": 150.0
                }
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``message`` y ``data`` de la compra.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            data = request.params or request.httprequest.get_json(force=True) or {}

            if not data.get('articulo_id'):
                return {'success': False, 'message': 'El artículo es requerido', 'error_code': 'MISSING_FIELD'}

            article = request.env['second_market.article'].sudo().browse(data['articulo_id'])
            if not article.exists():
                return {'success': False, 'message': 'Artículo no encontrado', 'error_code': 'ARTICLE_NOT_FOUND'}

            if article.estado_publicacion != 'publicado':
                return {'success': False, 'message': 'Este artículo no está disponible para compra', 'error_code': 'ARTICLE_NOT_AVAILABLE'}

            if article.id_propietario.id == user_data['user_id']:
                return {'success': False, 'message': 'No puedes comprar tu propio artículo', 'error_code': 'SELF_PURCHASE'}

            purchase = request.env['second_market.purchase'].sudo().create({
                'id_comprador': user_data['user_id'],
                'id_vendedor': article.id_propietario.id,
                'id_articulo': article.id,
                'precio': article.precio,
                'estado': 'pendiente'
            })

            article.sudo().write({'estado_publicacion': 'reservado'})

            response = {
                'success': True,
                'message': 'Compra creada exitosamente',
                'data': {'purchase_id': purchase.id, 'id_compra': purchase.id_compra, 'precio': purchase.precio}
            }
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al crear compra: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al crear compra', 'error_code': 'CREATE_PURCHASE_ERROR'}

    @http.route('/api/v1/purchases/<int:purchase_id>/confirm', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def confirm_purchase(self, purchase_id, **kwargs):
        """Confirmar la entrega y marcar la compra como completada.

        Solo el vendedor puede confirmar la transacción. Al confirmar,
        el artículo pasa a estado ``vendido``.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param purchase_id: ID de la compra a confirmar.
        :type purchase_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            purchase = request.env['second_market.purchase'].sudo().browse(purchase_id)
            if not purchase.exists():
                return {'success': False, 'message': 'Compra no encontrada', 'error_code': 'PURCHASE_NOT_FOUND'}

            if purchase.id_vendedor.id != user_data['user_id']:
                return {'success': False, 'message': 'Solo el vendedor puede confirmar', 'error_code': 'FORBIDDEN'}

            purchase.sudo().confirmar_transaccion()

            response = {'success': True, 'message': 'Compra confirmada exitosamente'}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al confirmar compra: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al confirmar compra', 'error_code': 'CONFIRM_PURCHASE_ERROR'}

    @http.route('/api/v1/purchases/<int:purchase_id>/cancel', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def cancel_purchase(self, purchase_id, **kwargs):
        """Cancelar una compra y devolver el artículo a estado publicado.

        Tanto el comprador como el vendedor pueden cancelar la compra,
        siempre que no esté ya completada.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param purchase_id: ID de la compra a cancelar.
        :type purchase_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            purchase = request.env['second_market.purchase'].sudo().browse(purchase_id)
            if not purchase.exists():
                return {'success': False, 'message': 'Compra no encontrada', 'error_code': 'PURCHASE_NOT_FOUND'}

            if purchase.id_comprador.id != user_data['user_id'] and purchase.id_vendedor.id != user_data['user_id']:
                return {'success': False, 'message': 'No tienes permiso', 'error_code': 'FORBIDDEN'}

            purchase.sudo().cancelar_compra()

            response = {'success': True, 'message': 'Compra cancelada'}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al cancelar compra: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al cancelar compra', 'error_code': 'CANCEL_PURCHASE_ERROR'}

    @http.route('/api/v1/purchases/my-purchases', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_my_purchases(self, **kwargs):
        """Obtener todas las compras realizadas por el usuario autenticado.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data.purchases`` (lista de compras).
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

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
                    'articulo': {'id': purchase.id_articulo.id, 'nombre': purchase.id_articulo.nombre, 'codigo': purchase.id_articulo.codigo},
                    'vendedor': {'id': purchase.id_vendedor.id, 'nombre': purchase.id_vendedor.name}
                })

            response = {'success': True, 'data': {'purchases': purchases_data}}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al obtener compras: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener compras', 'error_code': 'GET_PURCHASES_ERROR'}

    @http.route('/api/v1/purchases/my-sales', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_my_sales(self, **kwargs):
        """Obtener todas las ventas realizadas por el usuario autenticado.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data.sales`` (lista de ventas).
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

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
                    'articulo': {'id': sale.id_articulo.id, 'nombre': sale.id_articulo.nombre, 'codigo': sale.id_articulo.codigo},
                    'comprador': {'id': sale.id_comprador.id, 'nombre': sale.id_comprador.name}
                })

            response = {'success': True, 'data': {'sales': sales_data}}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al obtener ventas: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener ventas', 'error_code': 'GET_SALES_ERROR'}


class SecondMarketRatingController(http.Controller):
    """Controlador para la gestión de valoraciones entre usuarios.

    Permite a los usuarios calificarse mutuamente tras una transacción.
    Las valoraciones son únicas por par valorador-valorado.
    """

    def _get_authenticated_user(self):
        """Obtener el usuario autenticado a partir del token JWT del request.

        :return: Diccionario ``{'user_data': dict, 'new_token': str}`` o ``None``.
        :rtype: dict or None
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/ratings', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_rating(self, **kwargs):
        """Crear una valoración para otro usuario.

        Un usuario no puede valorarse a sí mismo ni valorar al mismo usuario
        dos veces (restricción del modelo).

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON:**

        .. code-block:: json

            {
                "usuario_id": 3,
                "calificacion": 5,
                "comentario": "Trato muy amable y envío rápido"
            }

        El campo ``comentario`` es opcional.

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``message`` y ``data.rating_id``.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            data = request.params or request.httprequest.get_json(force=True) or {}

            if not data.get('usuario_id') or not data.get('calificacion'):
                return {'success': False, 'message': 'El usuario y la calificación son requeridos', 'error_code': 'MISSING_FIELD'}

            rated_user = request.env['second_market.user'].sudo().browse(data['usuario_id'])
            if not rated_user.exists():
                return {'success': False, 'message': 'Usuario no encontrado', 'error_code': 'USER_NOT_FOUND'}

            if rated_user.id == user_data['user_id']:
                return {'success': False, 'message': 'No puedes valorarte a ti mismo', 'error_code': 'SELF_RATING'}

            rating = request.env['second_market.rating'].sudo().create({
                'id_usuario': data['usuario_id'],
                'id_valorador': user_data['user_id'],
                'calificacion': str(data['calificacion']),
                'comentario': data.get('comentario', '')
            })

            response = {
                'success': True,
                'message': 'Valoración creada exitosamente',
                'data': {'rating_id': rating.id}
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

    @http.route('/api/v1/ratings/user/<int:user_id>', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_user_ratings(self, user_id, **kwargs):
        """Obtener las valoraciones recibidas por un usuario.

        Endpoint público — no requiere autenticación.

        :param user_id: ID del usuario cuyas valoraciones se quieren listar.
        :type user_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data.ratings``.
        :rtype: dict
        """
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
                    'valorador': {'id': rating.id_valorador.id, 'nombre': rating.id_valorador.name}
                })

            return {'success': True, 'data': {'ratings': ratings_data}}

        except Exception as e:
            _logger.error(f"Error al obtener valoraciones: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener valoraciones', 'error_code': 'GET_RATINGS_ERROR'}
