# -*- coding: utf-8 -*-

"""
Controladores de chats, denuncias y categorías para la API REST de Second Market.

**Endpoints de Chats** (``SecondMarketChatController``):

- ``POST /api/v1/chats``                            — Crear o listar chats del usuario.
- ``POST /api/v1/chats/<id>/messages``              — Enviar o listar mensajes de un chat.

**Endpoints de Denuncias** (``SecondMarketReportController``):

- ``POST /api/v1/reports``                          — Crear una denuncia.
- ``POST /api/v1/reports/my-reports``               — Listar denuncias del usuario.

**Endpoints de Categorías y Etiquetas** (``SecondMarketCategoryController``):

- ``POST /api/v1/categories``                       — Listar todas las categorías activas.
- ``POST /api/v1/categories/<id>/articles``         — Artículos de una categoría.
- ``POST /api/v1/tags``                             — Listar todas las etiquetas.

Todos los endpoints de Chats y Denuncias requieren el header
``Authorization: Bearer <token>``.
"""

from odoo import http, _
from odoo.http import request
import logging

from .auth_controller import verify_jwt_token, get_token_from_request, get_authenticated_user_with_refresh

_logger = logging.getLogger(__name__)


class SecondMarketChatController(http.Controller):
    """Controlador para la gestión de chats y mensajes entre usuarios.

    Los endpoints de chat son **unificados**: la presencia o ausencia del campo
    ``articulo_id`` / ``contenido`` en el body determina la operación a realizar,
    evitando conflictos de rutas duplicadas en Odoo.
    """

    def _get_authenticated_user(self):
        """Obtener el usuario autenticado a partir del token JWT del request.

        :return: Diccionario ``{'user_data': dict, 'new_token': str}`` o ``None``.
        :rtype: dict or None
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/chats', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def handle_chats(self, **kwargs):
        """Crear un chat o listar los chats del usuario autenticado (endpoint unificado).

        La lógica depende del body recibido:

        - **Con** ``articulo_id`` → Busca o crea el chat entre el usuario y el
          propietario del artículo. Si ya existe, devuelve el ID existente.
        - **Sin** ``articulo_id`` → Devuelve la lista de todos los chats activos del
          usuario (como comprador o como vendedor).

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON para crear/recuperar chat:**

        .. code-block:: json

            { "articulo_id": 42 }

        **Body JSON para listar chats:** cuerpo vacío o sin ``articulo_id``.

        **Respuesta (crear/recuperar):**

        .. code-block:: json

            {
                "success": true,
                "data": { "chat_id": 7, "new_chat": true }
            }

        **Respuesta (listar):**

        .. code-block:: json

            {
                "success": true,
                "data": {
                    "chats": [
                        {
                            "id": 7,
                            "articulo": { "id": 42, "nombre": "Bici", "precio": 150.0 },
                            "otro_usuario": { "id": 3, "nombre": "Jose" },
                            "ultimo_mensaje": "Hola, ¿sigue disponible?",
                            "conteo_mensajes": 5
                        }
                    ]
                }
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data``.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            data = request.params or {}

            if data.get('articulo_id'):
                article = request.env['second_market.article'].sudo().browse(data['articulo_id'])

                if not article.exists():
                    return {'success': False, 'message': 'Artículo no encontrado', 'error_code': 'ARTICLE_NOT_FOUND'}

                if article.id_propietario.id == user_data['user_id']:
                    return {'success': False, 'message': 'No puedes chatear sobre tu propio artículo', 'error_code': 'SELF_CHAT'}

                existing_chat = request.env['second_market.chat'].sudo().search([
                    ('id_articulo', '=', article.id),
                    ('id_comprador', '=', user_data['user_id'])
                ], limit=1)

                if existing_chat:
                    response = {'success': True, 'message': 'Chat recuperado', 'data': {'chat_id': existing_chat.id, 'new_chat': False}}
                    if new_token:
                        response['new_token'] = new_token
                    return response

                chat = request.env['second_market.chat'].sudo().create({
                    'id_articulo': article.id,
                    'id_comprador': user_data['user_id']
                })

                response = {'success': True, 'message': 'Chat creado exitosamente', 'data': {'chat_id': chat.id, 'new_chat': True}}
                if new_token:
                    response['new_token'] = new_token
                return response

            chats = request.env['second_market.chat'].sudo().search([
                '|',
                ('id_comprador', '=', user_data['user_id']),
                ('id_vendedor', '=', user_data['user_id']),
                ('activo', '=', True)
            ], order='fecha_ultimo_mensaje desc')

            chats_data = []
            for chat in chats:
                otro_usuario = chat.id_vendedor if chat.id_comprador.id == user_data['user_id'] else chat.id_comprador
                chats_data.append({
                    'id': chat.id,
                    'articulo': {'id': chat.id_articulo.id, 'nombre': chat.id_articulo.nombre, 'precio': chat.id_articulo.precio},
                    'otro_usuario': {'id': otro_usuario.id, 'nombre': otro_usuario.name},
                    'ultimo_mensaje': chat.ultimo_mensaje,
                    'fecha_ultimo_mensaje': chat.fecha_ultimo_mensaje.isoformat() if chat.fecha_ultimo_mensaje else None,
                    'conteo_mensajes': chat.conteo_mensajes
                })

            response = {'success': True, 'data': {'chats': chats_data}}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error en handle_chats: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al procesar la petición de chats', 'error_code': 'CHATS_ERROR'}

    @http.route('/api/v1/chats/<int:chat_id>/messages', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def handle_chat_messages(self, chat_id, **kwargs):
        """Enviar un mensaje o listar los mensajes de un chat (endpoint unificado).

        La lógica depende del body recibido:

        - **Con** ``contenido`` → Crea y guarda el mensaje en la base de datos.
        - **Sin** ``contenido`` → Devuelve todos los mensajes del chat ordenados
          cronológicamente. Incluye el flag ``is_mine`` para distinguir mensajes propios.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON para enviar mensaje:**

        .. code-block:: json

            { "contenido": "Hola, ¿sigue disponible?" }

        **Respuesta (mensaje enviado):**

        .. code-block:: json

            {
                "success": true,
                "data": { "message_id": 15, "fecha_envio": "2026-03-02T18:00:00" }
            }

        :param chat_id: ID del chat sobre el que se opera.
        :type chat_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data``.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            data = request.params or {}

            chat = request.env['second_market.chat'].sudo().browse(chat_id)
            if not chat.exists():
                return {'success': False, 'message': 'Chat no encontrado', 'error_code': 'CHAT_NOT_FOUND'}

            if chat.id_comprador.id != user_data['user_id'] and chat.id_vendedor.id != user_data['user_id']:
                return {'success': False, 'message': 'No tienes acceso a este chat', 'error_code': 'FORBIDDEN'}

            if data.get('contenido'):
                message = request.env['second_market.message'].sudo().create({
                    'id_chat': chat.id,
                    'id_usuario': user_data['user_id'],
                    'contenido': data['contenido']
                })

                response = {
                    'success': True,
                    'message': 'Mensaje enviado',
                    'data': {
                        'message_id': message.id,
                        'fecha_envio': message.fecha_envio.isoformat() if message.fecha_envio else None
                    }
                }
                if new_token:
                    response['new_token'] = new_token
                return response

            messages_data = []
            for message in chat.ids_mensajes:
                messages_data.append({
                    'id': message.id,
                    'contenido': message.contenido,
                    'fecha_envio': message.fecha_envio.isoformat() if message.fecha_envio else None,
                    'leido': message.leido,
                    'usuario': {'id': message.id_usuario.id, 'nombre': message.id_usuario.name},
                    'is_mine': message.id_usuario.id == user_data['user_id']
                })

            response = {
                'success': True,
                'data': {
                    'messages': messages_data,
                    'chat_info': {'articulo': {'id': chat.id_articulo.id, 'nombre': chat.id_articulo.nombre}}
                }
            }
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error en handle_chat_messages: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al procesar la petición de mensajes', 'error_code': 'CHAT_MESSAGES_ERROR'}


class SecondMarketReportController(http.Controller):
    """Controlador para la gestión de denuncias/reportes.

    Permite a los usuarios denunciar artículos, comentarios o usuarios.
    Los registros creados son visibles para los moderadores en el backend de Odoo.
    """

    def _get_authenticated_user(self):
        """Obtener el usuario autenticado a partir del token JWT del request.

        :return: Diccionario ``{'user_data': dict, 'new_token': str}`` o ``None``.
        :rtype: dict or None
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/reports', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_report(self, **kwargs):
        """Crear una denuncia sobre un artículo, comentario o usuario.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON:**

        .. code-block:: json

            {
                "tipo_denuncia": "articulo",
                "motivo": "contenido_inapropiado",
                "descripcion": "Este artículo contiene imágenes inapropiadas",
                "articulo_id": 42
            }

        Los valores válidos para ``tipo_denuncia`` son: ``'articulo'``,
        ``'comentario'`` o ``'usuario'``. Según el tipo, se requiere el campo
        ``articulo_id``, ``comentario_id`` o ``usuario_id`` respectivamente.

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``message`` y ``data.report_id``.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            data = request.params or request.httprequest.get_json(force=True) or {}

            for field in ['tipo_denuncia', 'motivo', 'descripcion']:
                if not data.get(field):
                    return {'success': False, 'message': f'El campo {field} es requerido', 'error_code': 'MISSING_FIELD'}

            if data['tipo_denuncia'] not in ['articulo', 'comentario', 'usuario']:
                return {'success': False, 'message': 'Tipo de denuncia inválido', 'error_code': 'INVALID_TYPE'}

            report_vals = {
                'tipo_denuncia': data['tipo_denuncia'],
                'motivo': data['motivo'],
                'descripcion': data['descripcion'],
                'id_denunciante': user_data['user_id'],
                'estado': 'pendiente'
            }

            if data['tipo_denuncia'] == 'articulo':
                if not data.get('articulo_id'):
                    return {'success': False, 'message': 'El artículo es requerido', 'error_code': 'MISSING_FIELD'}
                report_vals['id_articulo'] = data['articulo_id']
            elif data['tipo_denuncia'] == 'comentario':
                if not data.get('comentario_id'):
                    return {'success': False, 'message': 'El comentario es requerido', 'error_code': 'MISSING_FIELD'}
                report_vals['id_comentario'] = data['comentario_id']
            elif data['tipo_denuncia'] == 'usuario':
                if not data.get('usuario_id'):
                    return {'success': False, 'message': 'El usuario es requerido', 'error_code': 'MISSING_FIELD'}
                report_vals['id_usuario_denunciado'] = data['usuario_id']

            report = request.env['second_market.report'].sudo().create(report_vals)

            response = {
                'success': True,
                'message': 'Denuncia creada exitosamente',
                'data': {'report_id': report.id, 'num_denuncia': report.num_denuncia}
            }
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al crear denuncia: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': str(e) if 'no puedes denunciar' in str(e).lower() else 'Error al crear denuncia',
                'error_code': 'CREATE_REPORT_ERROR'
            }

    @http.route('/api/v1/reports/my-reports', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_my_reports(self, **kwargs):
        """Obtener las denuncias realizadas por el usuario autenticado.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data.reports`` (lista de denuncias).
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {'success': False, 'message': 'No autenticado', 'error_code': 'UNAUTHORIZED'}

            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')

            reports = request.env['second_market.report'].sudo().search([
                ('id_denunciante', '=', user_data['user_id']),
                ('activo', '=', True)
            ], order='create_date desc')

            reports_data = []
            for report in reports:
                report_dict = {
                    'id': report.id,
                    'num_denuncia': report.num_denuncia,
                    'tipo_denuncia': report.tipo_denuncia,
                    'motivo': report.motivo,
                    'descripcion': report.descripcion,
                    'estado': report.estado,
                    'prioridad': report.prioridad,
                    'create_date': report.create_date.isoformat() if report.create_date else None
                }

                if report.tipo_denuncia == 'articulo' and report.id_articulo:
                    report_dict['articulo'] = {'id': report.id_articulo.id, 'nombre': report.id_articulo.nombre}
                elif report.tipo_denuncia == 'comentario' and report.id_comentario:
                    report_dict['comentario'] = {'id': report.id_comentario.id, 'texto': report.id_comentario.texto[:50]}
                elif report.tipo_denuncia == 'usuario' and report.id_usuario_denunciado:
                    report_dict['usuario'] = {'id': report.id_usuario_denunciado.id, 'nombre': report.id_usuario_denunciado.name}

                reports_data.append(report_dict)

            response = {'success': True, 'data': {'reports': reports_data}}
            if new_token:
                response['new_token'] = new_token
            return response

        except Exception as e:
            _logger.error(f"Error al obtener denuncias: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener denuncias', 'error_code': 'GET_REPORTS_ERROR'}


class SecondMarketCategoryController(http.Controller):
    """Controlador para la consulta de categorías y etiquetas.

    Todos los endpoints son públicos (no requieren autenticación).
    """

    @http.route('/api/v1/categories', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_categories(self, **kwargs):
        """Obtener todas las categorías activas de la plataforma.

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data.categories``.
        :rtype: dict

        **Respuesta exitosa:**

        .. code-block:: json

            {
                "success": true,
                "data": {
                    "categories": [
                        {
                            "id": 1,
                            "name": "Electrónica",
                            "icono": "fa-laptop",
                            "color": 3,
                            "conteo_articulos": 24
                        }
                    ]
                }
            }
        """
        try:
            categories = request.env['second_market.category'].sudo().search([('activo', '=', True)], order='name')

            categories_data = []
            for category in categories:
                try:
                    categories_data.append({
                        'id': category.id,
                        'name': category.name or '',
                        'descripcion': category.descripcion or '',
                        'icono': category.icono or '',
                        'color': int(category.color) if category.color else 0,
                        'conteo_articulos': int(category.conteo_articulos) if category.conteo_articulos else 0,
                    })
                except Exception as cat_err:
                    _logger.error(f"Error serializando categoría {category.id}: {str(cat_err)}", exc_info=True)
                    categories_data.append({'id': category.id, 'name': category.name or '', 'descripcion': '', 'icono': '', 'color': 0, 'conteo_articulos': 0})

            return {'success': True, 'data': {'categories': categories_data}}

        except Exception as e:
            _logger.error(f"Error al obtener categorías: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener categorías', 'error_code': 'GET_CATEGORIES_ERROR'}

    @http.route('/api/v1/categories/<int:category_id>/articles', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_category_articles(self, category_id, **kwargs):
        """Obtener los artículos publicados de una categoría específica.

        Admite paginación mediante los parámetros opcionales ``limit`` y ``offset``.

        :param category_id: ID de la categoría a consultar.
        :type category_id: int
        :param kwargs: Parámetros opcionales: ``limit`` (por defecto 20)
            y ``offset`` (por defecto 0).
        :return: Diccionario con ``success`` y ``data.articles``.
        :rtype: dict
        """
        try:
            data = request.params
            limit = data.get('limit', 20)
            offset = data.get('offset', 0)

            articles = request.env['second_market.article'].sudo().search([
                ('id_categoria', '=', category_id),
                ('estado_publicacion', '=', 'publicado'),
                ('activo', '=', True)
            ], limit=limit, offset=offset, order='create_date desc')

            articles_data = []
            for article in articles:
                articles_data.append({
                    'id': article.id,
                    'nombre': article.nombre,
                    'precio': article.precio,
                    'estado_producto': article.estado_producto,
                    'localidad': article.localidad,
                    'imagen_principal': article.imagen_principal.decode('utf-8') if article.imagen_principal else None
                })

            return {'success': True, 'data': {'articles': articles_data}}

        except Exception as e:
            _logger.error(f"Error al obtener artículos de categoría: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener artículos', 'error_code': 'GET_CATEGORY_ARTICLES_ERROR'}

    @http.route('/api/v1/tags', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def get_tags(self, **kwargs):
        """Obtener todas las etiquetas disponibles en la plataforma.

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data.tags`` (lista de etiquetas).
        :rtype: dict
        """
        try:
            tags = request.env['second_market.tag'].sudo().search([])

            tags_data = [{'id': tag.id, 'name': tag.name, 'color': tag.color} for tag in tags]

            return {'success': True, 'data': {'tags': tags_data}}

        except Exception as e:
            _logger.error(f"Error al obtener etiquetas: {str(e)}", exc_info=True)
            return {'success': False, 'message': 'Error al obtener etiquetas', 'error_code': 'GET_TAGS_ERROR'}
