# -*- coding: utf-8 -*-

"""
Controlador de gestión de perfiles de usuario para la API REST de Second Market.

**Endpoints disponibles:**

- ``GET/POST /api/v1/users/profile``              — Perfil del usuario autenticado.
- ``POST     /api/v1/users/update-profile``       — Actualizar perfil propio.
- ``POST     /api/v1/users/change-password``      — Cambiar contraseña.
- ``GET/POST /api/v1/users/<id>``                 — Perfil público de un usuario.
- ``GET/POST /api/v1/users/<id>/articles``        — Artículos publicados de un usuario.
- ``GET/POST /api/v1/users/<id>/ratings``         — Valoraciones de un usuario.
- ``GET/POST /api/v1/users/statistics``           — Estadísticas detalladas del usuario autenticado.
- ``POST     /api/v1/users/deactivate``           — Desactivar cuenta propia.

Todos los endpoints protegidos requieren el header ``Authorization: Bearer <token>``.
"""

from odoo import http, _
from odoo.http import request
import logging
from passlib.context import CryptContext

#: Contexto de hashing de contraseñas (mismo esquema que en ``login.py``).
crypt_context = CryptContext(schemes=["pbkdf2_sha512", "plaintext"], deprecated="auto")

from .auth_controller import verify_jwt_token, get_token_from_request, get_authenticated_user_with_refresh

_logger = logging.getLogger(__name__)


class SecondMarketUserController(http.Controller):
    """Controlador para la gestión de perfiles y cuentas de usuario.

    Todos los métodos que requieren autenticación comprueban el token JWT
    mediante :func:`~api_market.controllers.auth_controller.get_authenticated_user_with_refresh`.
    Si el token está próximo a expirar, se renueva automáticamente y se devuelve
    en el campo ``new_token`` de la respuesta.
    """

    def _get_authenticated_user(self):
        """Obtener el usuario autenticado a partir del token JWT del request.

        Delega en :func:`~api_market.controllers.auth_controller.get_authenticated_user_with_refresh`,
        que incluye renovación automática del token si es necesario.

        :return: Diccionario ``{'user_data': dict, 'new_token': str}`` o ``None``
            si el usuario no está autenticado.
        :rtype: dict or None
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/users/profile', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_my_profile(self, **kwargs):
        """Obtener el perfil completo del usuario autenticado.

        Devuelve todos los campos del perfil, incluyendo el avatar en base64,
        estadísticas de venta/compra y calificación promedio.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Respuesta exitosa:**

        .. code-block:: json

            {
                "success": true,
                "data": {
                    "id": 1,
                    "name": "Jonatan",
                    "login": "jonatan@ejemplo.com",
                    "avatar": "<base64>",
                    "calificacion_promedio": 4.5,
                    "productos_en_venta": 3
                }
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data`` (perfil del usuario).
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])

            if not user.exists():
                return {'success': False, 'message': 'Usuario no encontrado', 'error_code': 'USER_NOT_FOUND'}

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

            response_data = {'success': True, 'data': profile_data}
            if new_token:
                response_data['new_token'] = new_token
            return response_data

        except Exception as e:
            _logger.error(f"Error al obtener perfil: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener perfil', 'error_code': 'GET_PROFILE_ERROR'}

    @http.route('/api/v1/users/update-profile', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def update_profile(self, **kwargs):
        """Actualizar campos del perfil del usuario autenticado.

        Solo se actualizan los campos enviados en el body. El campo ``avatar``
        acepta una cadena base64; si se envía vacío, se ignora.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON (campos opcionales):**

        .. code-block:: json

            {
                "name": "Jonatan Cruz",
                "telefono": "612345678",
                "ubicacion": "Sevilla",
                "biografia": "Nueva bio",
                "avatar": "<base64>",
                "login": "nuevo@email.com"
            }

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

            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])
            if not user.exists():
                return {'success': False, 'message': 'Usuario no encontrado', 'error_code': 'USER_NOT_FOUND'}

            data = {}
            if request.params:
                data.update(request.params)
            if not data:
                try:
                    json_body = request.httprequest.get_json(force=True)
                    if json_body:
                        data.update(json_body.get('params', json_body))
                except Exception as e:
                    _logger.debug(f"No se pudo leer el body JSON: {str(e)}")
            if kwargs:
                data.update(kwargs)

            update_vals = {}
            for field in ['name', 'telefono', 'ubicacion', 'biografia', 'avatar', 'login']:
                if field in data and data[field] is not None:
                    if field == 'avatar' and data[field] == '':
                        continue
                    update_vals[field] = data[field]

            if update_vals:
                user.sudo().write(update_vals)

            response = {'success': True, 'message': 'Perfil actualizado exitosamente'}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al actualizar perfil: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al actualizar perfil', 'error_code': 'UPDATE_PROFILE_ERROR', 'error_detail': str(e)}

    @http.route('/api/v1/users/change-password', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def change_password(self, **kwargs):
        """Cambiar la contraseña del usuario autenticado.

        Requiere la contraseña actual para confirmar la identidad. La nueva
        contraseña debe tener al menos 8 caracteres.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON:**

        .. code-block:: json

            {
                "current_password": "contraseñaActual",
                "new_password": "nuevaContraseña123"
            }

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

            data = request.params or request.httprequest.get_json(force=True) or {}

            if not data.get('current_password') or not data.get('new_password'):
                return {'success': False, 'message': 'Se requiere la contraseña actual y la nueva', 'error_code': 'MISSING_FIELD'}

            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])
            if not user.exists():
                return {'success': False, 'message': 'Usuario no encontrado', 'error_code': 'USER_NOT_FOUND'}

            if not crypt_context.verify(data['current_password'], user.password):
                return {'success': False, 'message': 'Contraseña actual incorrecta', 'error_code': 'INVALID_PASSWORD'}

            if len(data['new_password']) < 8:
                return {'success': False, 'message': 'La nueva contraseña debe tener al menos 8 caracteres', 'error_code': 'PASSWORD_TOO_SHORT'}

            user.sudo().write({'password': data['new_password']})
            _logger.info(f"Contraseña cambiada para usuario {user.id}")

            response = {'success': True, 'message': 'Contraseña actualizada exitosamente'}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al cambiar contraseña: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al cambiar contraseña', 'error_code': 'CHANGE_PASSWORD_ERROR'}

    @http.route('/api/v1/users/<int:user_id>', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_user_profile(self, user_id, **kwargs):
        """Obtener el perfil público de un usuario por su ID.

        No requiere autenticación. Devuelve solo los campos públicos del
        perfil (no incluye email/login ni información privada).

        :param user_id: ID interno de Odoo del usuario a consultar.
        :type user_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data`` (perfil público).
        :rtype: dict
        """
        try:
            user = request.env['second_market.user'].sudo().browse(user_id)

            if not user.exists() or not user.activo:
                return {'success': False, 'message': 'Usuario no encontrado', 'error_code': 'USER_NOT_FOUND'}

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

            return {'success': True, 'data': profile_data}

        except Exception as e:
            _logger.error(f"Error al obtener perfil de usuario: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener perfil', 'error_code': 'GET_USER_PROFILE_ERROR'}

    @http.route('/api/v1/users/<int:user_id>/articles', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_user_articles(self, user_id, **kwargs):
        """Obtener los artículos publicados de un usuario.

        Devuelve solo artículos en estado ``publicado`` y activos.
        Admite paginación mediante ``limit`` y ``offset``.

        :param user_id: ID interno del usuario propietario.
        :type user_id: int
        :param kwargs: Parámetros opcionales: ``limit`` (int, por defecto 20) y
            ``offset`` (int, por defecto 0).
        :return: Diccionario con ``success`` y ``data.articles`` (lista de artículos).
        :rtype: dict
        """
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

            return {'success': True, 'data': {'articles': articles_data}}

        except Exception as e:
            _logger.error(f"Error al obtener artículos de usuario: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener artículos', 'error_code': 'GET_USER_ARTICLES_ERROR'}

    @http.route('/api/v1/users/<int:user_id>/ratings', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_user_ratings(self, user_id, **kwargs):
        """Obtener las valoraciones recibidas por un usuario.

        Devuelve la lista de valoraciones activas y el promedio de calificación.
        Admite paginación mediante ``limit`` y ``offset``.

        :param user_id: ID interno del usuario valorado.
        :type user_id: int
        :param kwargs: Parámetros opcionales: ``limit`` (int, por defecto 10) y
            ``offset`` (int, por defecto 0).
        :return: Diccionario con ``success``, ``data.ratings`` y
            ``data.calificacion_promedio``.
        :rtype: dict
        """
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
            return {'success': False, 'message': 'Error al obtener valoraciones', 'error_code': 'GET_USER_RATINGS_ERROR'}

    @http.route('/api/v1/users/statistics', type='json', auth='public', methods=['GET', 'POST'], csrf=False)
    def get_my_statistics(self, **kwargs):
        """Obtener estadísticas detalladas de actividad del usuario autenticado.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Respuesta exitosa:**

        .. code-block:: json

            {
                "success": true,
                "data": {
                    "productos_en_venta": 3,
                    "productos_vendidos": 10,
                    "calificacion_promedio": 4.2,
                    "ventas_completadas": 8,
                    "compras_pendientes": 1
                }
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data`` (estadísticas completas).
        :rtype: dict
        """
        try:
            auth_data = self._get_authenticated_user()
            user = auth_data.get('user_data', {}).get('user')

            if not user:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

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

            return {'success': True, 'data': stats}

        except Exception as e:
            _logger.error(f"Error al obtener estadísticas: {str(e)}", exc_info=True)
            return {'success': False, 'message': str(e), 'error_code': 'GET_STATISTICS_ERROR'}

    @http.route('/api/v1/users/deactivate', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def deactivate_account(self, **kwargs):
        """Desactivar la cuenta del usuario autenticado.

        El usuario confirma su identidad con la contraseña actual. Al desactivarse,
        todos sus artículos en venta también se desactivan automáticamente.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON:**

        .. code-block:: json

            {
                "password": "contraseñaActual"
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            user_data = self._get_authenticated_user()
            if not user_data:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            data = request.params or request.httprequest.get_json(force=True) or {}

            if not data.get('password'):
                return {'success': False, 'message': 'Se requiere la contraseña para confirmar', 'error_code': 'MISSING_FIELD'}

            user = request.env['second_market.user'].sudo().browse(user_data['user_id'])
            if not user.exists():
                return {'success': False, 'message': 'Usuario no encontrado', 'error_code': 'USER_NOT_FOUND'}

            if not crypt_context.verify(data['password'], user.password):
                return {'success': False, 'message': 'Contraseña incorrecta', 'error_code': 'INVALID_PASSWORD'}

            user.sudo().write({'activo': False})
            user.ids_articulos_venta.sudo().write({'activo': False})
            _logger.info(f"Usuario desactivado: {user.id}")

            return {'success': True, 'message': 'Cuenta desactivada exitosamente'}

        except Exception as e:
            _logger.error(f"Error al desactivar cuenta: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al desactivar cuenta', 'error_code': 'DEACTIVATE_ACCOUNT_ERROR'}
