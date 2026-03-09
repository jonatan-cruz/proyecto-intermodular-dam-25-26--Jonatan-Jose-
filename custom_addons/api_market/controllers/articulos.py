# -*- coding: utf-8 -*-

"""
Controlador de artículos para la API REST de Second Market.

**Endpoints disponibles:**

- ``GET/POST /api/v1/articles/list``             — Listar artículos con filtros.
- ``GET       /api/v1/articles/<id>/image``       — Servir imagen principal (binario HTTP).
- ``GET/POST /api/v1/articles/<id>``             — Detalle completo de un artículo.
- ``POST      /api/v1/articles``                 — Crear un nuevo artículo.
- ``PUT       /api/v1/articles/<id>``            — Actualizar un artículo existente.
- ``POST      /api/v1/articles/<id>/publish``    — Publicar un artículo en borrador.
- ``DELETE    /api/v1/articles/<id>``            — Desactivar (borrado lógico) un artículo.
- ``GET/POST /api/v1/articles/my-articles``     — Listar artículos del usuario autenticado.

Los endpoints de creación, edición y eliminación requieren autenticación JWT
mediante el header ``Authorization: Bearer <token>``.
"""

from odoo import http, _
from odoo.http import request
import logging
import base64

from .auth_controller import verify_jwt_token, get_token_from_request, get_authenticated_user_with_refresh

_logger = logging.getLogger(__name__)


class SecondMarketArticleController(http.Controller):
    """Controlador para la gestión de artículos de segunda mano — API v1.

    Proporciona endpoints para listar, consultar, crear, editar, publicar y
    eliminar artículos. Los endpoints de escritura requieren autenticación JWT.
    """

    def _get_authenticated_user(self):
        """Obtener el usuario autenticado a partir del token JWT del request.

        Delega en :func:`~api_market.controllers.auth_controller.get_authenticated_user_with_refresh`,
        incluyendo renovación automática del token si le queda poco tiempo de vida.

        :return: Diccionario ``{'user_data': dict, 'new_token': str}`` o ``None``
            si el usuario no está autenticado.
        :rtype: dict or None
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/articles/list', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_articles(self, **kwargs):
        """Obtener la lista paginada de artículos publicados con filtros opcionales.

        La imagen principal **no** se incluye en la respuesta de lista; en su lugar se
        devuelve ``imagen_url`` apuntando al endpoint binario
        ``GET /api/v1/articles/<id>/image``, que Android carga de forma lazy con Coil.

        **Body JSON (todos los campos son opcionales):**

        .. code-block:: json

            {
                "limit": 20,
                "offset": 0,
                "categoria_id": 1,
                "search": "bicicleta",
                "precio_min": 10.0,
                "precio_max": 500.0,
                "estado_producto": "bueno",
                "localidad": "Sevilla"
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``data.articles``, ``data.total``,
            ``data.limit`` y ``data.offset``.
        :rtype: dict
        """
        try:
            data = request.params or request.httprequest.get_json(force=True) or {}
            
            limit = data.get('limit', 20)
            offset = data.get('offset', 0)
            
            # Construir dominio de búsqueda
            domain = [
                ('estado_publicacion', '=', 'publicado'),
                ('activo', '=', True)
            ]
            
            # Filtros opcionales
            if data.get('categoria_id'):
                domain.append(('id_categoria', '=', data.get('categoria_id')))
            
            if data.get('search'):
                search_term = data.get('search')
                domain.append('|')
                domain.append(('nombre', 'ilike', search_term))
                domain.append(('descripcion', 'ilike', search_term))
            
            if data.get('precio_min'):
                domain.append(('precio', '>=', data.get('precio_min')))
            
            if data.get('precio_max'):
                domain.append(('precio', '<=', data.get('precio_max')))
            
            if data.get('estado_producto'):
                domain.append(('estado_producto', '=', data.get('estado_producto')))
            
            if data.get('localidad'):
                domain.append(('localidad', 'ilike', data.get('localidad')))
            
            # Buscar artículos
            articles = request.env['second_market.article'].sudo().search(
                domain,
                limit=limit,
                offset=offset,
                order='create_date desc'
            )
            
            total_count = request.env['second_market.article'].sudo().search_count(domain)
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    'id': article.id,
                    'codigo': article.codigo,
                    'nombre': article.nombre,
                    'descripcion': article.descripcion,
                    'precio': article.precio,
                    'estado_producto': article.estado_producto,
                    'antiguedad': article.antiguedad,
                    'localidad': article.localidad,
                    'categoria': {
                        'id': article.id_categoria.id,
                        'nombre': article.id_categoria.name
                    } if article.id_categoria else None,
                    'propietario': {
                        'id': article.id_propietario.id,
                        'nombre': article.id_propietario.name,
                        'calificacion_promedio': article.id_propietario.calificacion_promedio
                    } if article.id_propietario else None,
                    # Sin base64 en la lista — la imagen se carga por URL desde Android
                    'imagen_principal': None,
                    'imagen_url': f'/api/v1/articles/{article.id}/image' if article.imagen_principal else None,
                    'conteo_imagenes': article.conteo_imagenes,
                    'conteo_favoritos': article.conteo_favoritos,
                    'conteo_vistas': article.conteo_vistas,
                    'etiquetas': [{'id': tag.id, 'nombre': tag.name} for tag in article.ids_etiquetas],
                    'create_date': article.create_date.isoformat() if article.create_date else None
                })

            return {
                'success': True,
                'data': {
                    'articles': articles_data,
                    'total': total_count,
                    'limit': limit,
                    'offset': offset
                }
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener artículos: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener artículos',
                'error_code': 'GET_ARTICLES_ERROR'
            }

    @http.route('/api/v1/articles/<int:article_id>/image', type='http', auth='public', methods=['GET'], csrf=False, cors='*')
    def get_article_image(self, article_id, **kwargs):
        """Servir la imagen principal de un artículo en formato binario.

        Endpoint de tipo ``http`` (no JSON) que devuelve los bytes de la imagen
        directamente con su ``Content-Type``. Usado por Android con Coil para
        carga lazy de imágenes (solo cuando la tarjeta es visible en pantalla).

        Incluye ``Cache-Control: public, max-age=86400`` para evitar peticiones
        repetidas durante 24 horas.

        :param article_id: ID del artículo cuya imagen se quiere servir.
        :type article_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Respuesta HTTP con la imagen en binario, o ``404 Not Found``
            si el artículo no existe o no tiene imagen.
        :rtype: :class:`odoo.http.Response`
        """
        try:
            article = request.env['second_market.article'].sudo().browse(article_id)
            if not article.exists() or not article.imagen_principal:
                return request.not_found()

            image_data = base64.b64decode(article.imagen_principal)
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', 'image/jpeg'),
                    ('Content-Length', str(len(image_data))),
                    ('Cache-Control', 'public, max-age=86400'),
                ]
            )
        except Exception as e:
            _logger.error(f"Error al servir imagen del artículo {article_id}: {e}")
            return request.not_found()

    @http.route('/api/v1/articles/<int:article_id>', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_article_detail(self, article_id, **kwargs):
        """Obtener el detalle completo de un artículo e incrementar su contador de vistas.

        Devuelve todos los campos del artículo, sus imágenes en base64, los comentarios
        activos y datos públicos del propietario.

        :param article_id: ID del artículo a consultar.
        :type article_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y ``data`` (detalle completo del artículo).
        :rtype: dict
        """
        try:
            article = request.env['second_market.article'].sudo().browse(article_id)
            
            if not article.exists() or not article.activo:
                return {
                    'success': False,
                    'message': 'Artículo no encontrado',
                    'error_code': 'ARTICLE_NOT_FOUND'
                }
            
            # Incrementar vistas
            article.sudo().write({'conteo_vistas': article.conteo_vistas + 1})
            
            # Obtener imágenes
            imagenes = []
            for img in article.ids_imagenes:
                imagenes.append({
                    'id': img.id,
                    'name': img.name,
                    'image': img.image.decode('utf-8') if img.image else None,
                    'sequence': img.sequence
                })
            
            # Obtener comentarios
            comentarios = []
            for com in article.ids_comentarios.filtered(lambda c: c.activo):
                comentarios.append({
                    'id': com.id,
                    'texto': com.texto,
                    'emisor': {
                        'id': com.id_emisor.id,
                        'nombre': com.id_emisor.name
                    },
                    'fecha_hora': com.fecha_hora.isoformat() if com.fecha_hora else None
                })
            
            article_data = {
                'id': article.id,
                'codigo': article.codigo,
                'nombre': article.nombre,
                'descripcion': article.descripcion,
                'precio': article.precio,
                'estado_producto': article.estado_producto,
                'estado_publicacion': article.estado_publicacion,
                'antiguedad': article.antiguedad,
                'localidad': article.localidad,
                'latitud': article.latitud,
                'longitud': article.longitud,
                'categoria': {
                    'id': article.id_categoria.id,
                    'nombre': article.id_categoria.name,
                    'descripcion': article.id_categoria.descripcion
                } if article.id_categoria else None,
                'propietario': {
                    'id': article.id_propietario.id,
                    'id_usuario': article.id_propietario.id_usuario,
                    'nombre': article.id_propietario.name,
                    'calificacion_promedio': article.id_propietario.calificacion_promedio,
                    'total_valoraciones': article.id_propietario.total_valoraciones,
                    'productos_vendidos': article.id_propietario.productos_vendidos,
                    'antiguedad': article.id_propietario.antiguedad
                } if article.id_propietario else None,
                'imagenes': imagenes,
                'etiquetas': [{'id': tag.id, 'nombre': tag.name} for tag in article.ids_etiquetas],
                'comentarios': comentarios,
                'conteo_vistas': article.conteo_vistas,
                'conteo_favoritos': article.conteo_favoritos,
                'conteo_comentarios': article.conteo_comentarios,
                'create_date': article.create_date.isoformat() if article.create_date else None
            }
            
            return {
                'success': True,
                'data': article_data
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener artículo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener artículo',
                'error_code': 'GET_ARTICLE_ERROR'
            }

    @http.route('/api/v1/articles', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_article(self, **kwargs):
        """Crear un nuevo artículo y publicarlo directamente.

        El usuario autenticado se convierte en el propietario. El artículo se crea
        directamente en estado ``publicado``. Se admiten entre 1 y 10 imágenes.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON:**

        .. code-block:: json

            {
                "nombre": "Bicicleta de montaña",
                "descripcion": "En buen estado",
                "precio": 150.0,
                "estado_producto": "bueno",
                "localidad": "Sevilla",
                "categoria_id": 1,
                "antiguedad": 2,
                "latitud": 37.38,
                "longitud": -5.99,
                "etiquetas_ids": [1, 3],
                "imagenes": [
                    {"image": "<base64>", "name": "foto1.jpg", "sequence": 10}
                ]
            }

        Los campos ``antiguedad``, ``latitud``, ``longitud`` y ``etiquetas_ids`` son opcionales.

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``message`` y ``data.article_id`` + ``data.codigo``.
        :rtype: dict
        """
        try:
            # Verificar autenticación
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
            data = request.params or request.httprequest.get_json(force=True) or {}
            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            
            # Validar campos requeridos
            required_fields = ['nombre', 'descripcion', 'precio', 'estado_producto', 'localidad', 'categoria_id', 'imagenes']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'El campo {field} es requerido',
                        'error_code': 'MISSING_FIELD'
                    }
            
            # Validar imágenes
            imagenes = data.get('imagenes', [])
            if len(imagenes) < 1 or len(imagenes) > 10:
                return {
                    'success': False,
                    'message': 'Debes subir entre 1 y 10 imágenes',
                    'error_code': 'INVALID_IMAGE_COUNT'
                }
            
            # Crear artículo
            article_vals = {
                'nombre': data.get('nombre'),
                'descripcion': data.get('descripcion'),
                'precio': data.get('precio'),
                'estado_producto': data.get('estado_producto'),
                'localidad': data.get('localidad'),
                'id_categoria': data.get('categoria_id'),
                'id_propietario': user_data['user_id'],
                'antiguedad': data.get('antiguedad', 0),
                'latitud': data.get('latitud'),
                'longitud': data.get('longitud'),
                'estado_publicacion': 'publicado'
            }
            
            article = request.env['second_market.article'].sudo().create(article_vals)
            
            # Agregar imágenes
            for img_data in imagenes:
                request.env['second_market.image'].sudo().create({
                    'article_id': article.id,
                    'image': img_data.get('image'),
                    'name': img_data.get('name', ''),
                    'sequence': img_data.get('sequence', 10)
                })
            
            # Agregar etiquetas si existen
            if data.get('etiquetas_ids'):
                etiquetas_ids = data.get('etiquetas_ids')
                # Validar que todas las etiquetas existan
                existing_tags = request.env['second_market.tag'].sudo().search([
                    ('id', 'in', etiquetas_ids)
                ])
                existing_tag_ids = existing_tags.ids
                
                # Filtrar solo las etiquetas que existen
                valid_tag_ids = [tag_id for tag_id in etiquetas_ids if tag_id in existing_tag_ids]
                
                if valid_tag_ids:
                    article.sudo().write({'ids_etiquetas': [(6, 0, valid_tag_ids)]})
                
                # Advertir si algunas etiquetas no existen
                invalid_tags = set(etiquetas_ids) - set(existing_tag_ids)
                if invalid_tags:
                    _logger.warning(f"Etiquetas no encontradas (ignoradas): {invalid_tags}")
            
            _logger.info(f"Artículo creado: {article.codigo} por usuario {user_data['user_id']}")
            
            response = {
                'success': True,
                'message': 'Artículo creado exitosamente',
                'data': {
                    'article_id': article.id,
                    'codigo': article.codigo
                }
            }
            
            # Agregar nuevo token si fue renovado
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al crear artículo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al crear artículo',
                'error_code': 'CREATE_ARTICLE_ERROR',
                'error_detail': str(e)
            }

    @http.route('/api/v1/articles/<int:article_id>', type='json', auth='public', methods=['PUT'], csrf=False, cors='*')
    def update_article(self, article_id, **kwargs):
        """Actualizar uno o varios campos de un artículo existente.

        Solo el propietario del artículo puede editarlo. Se actualizan únicamente
        los campos enviados en el body.

        **Header requerido:** ``Authorization: Bearer <token>``

        **Body JSON (campos editables):**

        .. code-block:: json

            {
                "nombre": "Nuevo nombre",
                "precio": 120.0,
                "localidad": "Málaga",
                "categoria_id": 2
            }

        :param article_id: ID del artículo a actualizar.
        :type article_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado',
                    'error_code': 'UNAUTHORIZED'
                }

            user = auth_result['user_data']['user']

            article = request.env['second_market.article'].sudo().browse(article_id)
            if not article.exists():
                return {
                    'success': False,
                    'message': 'Artículo no encontrado',
                    'error_code': 'ARTICLE_NOT_FOUND'
                }

            if article.id_propietario.id != user.id:
                return {
                    'success': False,
                    'message': 'No tienes permiso para editar este artículo',
                    'error_code': 'FORBIDDEN'
                }

            data = request.params or request.httprequest.get_json(force=True) or {}
            _logger.debug(f"DATA RECIBIDA => {data}")

            updatable_fields = [
                'nombre', 'descripcion', 'precio', 'estado_producto',
                'localidad', 'antiguedad', 'latitud', 'longitud'
            ]

            update_vals = {}
            for field in updatable_fields:
                if field in data:
                    update_vals[field] = data[field]

            if 'categoria_id' in data:
                update_vals['id_categoria'] = data['categoria_id']

            if not update_vals:
                return {
                    'success': False,
                    'message': 'No se enviaron campos para actualizar',
                    'error_code': 'NO_DATA'
                }

            article.sudo().write(update_vals)

            return {
                'success': True,
                'message': 'Artículo actualizado exitosamente'
            }

        except Exception as e:
            _logger.error(f"Error al actualizar artículo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al actualizar artículo',
                'error_code': 'UPDATE_ARTICLE_ERROR'
            }

    @http.route('/api/v1/articles/<int:article_id>/publish', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def publish_article(self, article_id, **kwargs):
        """Cambiar el estado de un artículo a ``publicado``.

        Solo el propietario puede publicar su artículo. Útil para artículos
        creados previamente en estado ``borrador``.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param article_id: ID del artículo a publicar.
        :type article_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            
            article = request.env['second_market.article'].sudo().browse(article_id)
            
            if not article.exists():
                return {
                    'success': False,
                    'message': 'Artículo no encontrado',
                    'error_code': 'ARTICLE_NOT_FOUND'
                }
            
            if article.id_propietario.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes permiso',
                    'error_code': 'FORBIDDEN'
                }
            
            article.sudo().write({'estado_publicacion': 'publicado'})
            
            response = {
                'success': True,
                'message': 'Artículo publicado exitosamente'
            }
            
            # Agregar nuevo token si fue renovado
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al publicar artículo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al publicar artículo',
                'error_code': 'PUBLISH_ERROR'
            }

    @http.route('/api/v1/articles/<int:article_id>', type='json', auth='public', methods=['DELETE'], csrf=False, cors='*')
    def delete_article(self, article_id, **kwargs):
        """Desactivar (borrado lógico) un artículo.

        Solo el propietario puede eliminar su artículo. El artículo pasa a
        ``activo = False`` y ``estado_publicacion = 'eliminado'``, sin borrar
        el registro de la base de datos.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param article_id: ID del artículo a desactivar.
        :type article_id: int
        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            
            article = request.env['second_market.article'].sudo().browse(article_id)
            
            if not article.exists():
                return {
                    'success': False,
                    'message': 'Artículo no encontrado',
                    'error_code': 'ARTICLE_NOT_FOUND'
                }
            
            if article.id_propietario.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes permiso',
                    'error_code': 'FORBIDDEN'
                }
            
            article.sudo().write({
                'activo': False,
                'estado_publicacion': 'eliminado'
            })
            
            response = {
                'success': True,
                'message': 'Artículo eliminado exitosamente'
            }
            
            # Agregar nuevo token si fue renovado
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al eliminar artículo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al eliminar artículo',
                'error_code': 'DELETE_ERROR'
            }

    @http.route('/api/v1/articles/my-articles', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_my_articles(self, **kwargs):
        """Obtener todos los artículos del usuario autenticado (todos los estados).

        Incluye artículos en borrador, publicados, reservados y eliminados.
        Admite paginación mediante los parámetros ``limit`` y ``offset``.

        **Header requerido:** ``Authorization: Bearer <token>``

        :param kwargs: Parámetros opcionales: ``limit`` (por defecto 20)
            y ``offset`` (por defecto 0).
        :return: Diccionario con ``success``, ``data.articles`` y ``data.total``.
        :rtype: dict
        """
        try:
            auth_result = self._get_authenticated_user()
            if not auth_result:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
            user_data = auth_result['user_data']
            new_token = auth_result.get('new_token')
            
            data = request.httprequest.get_json(force=True) or {}
            limit = data.get('limit', 20)
            offset = data.get('offset', 0)
            
            articles = request.env['second_market.article'].sudo().search([
                ('id_propietario', '=', user_data['user_id'])
            ], limit=limit, offset=offset, order='create_date desc')
            
            total_count = request.env['second_market.article'].sudo().search_count([
                ('id_propietario', '=', user_data['user_id'])
            ])
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    'id': article.id,
                    'codigo': article.codigo,
                    'nombre': article.nombre,
                    'precio': article.precio,
                    'estado_producto': article.estado_producto,
                    'estado_publicacion': article.estado_publicacion,
                    'activo': article.activo,
                    'conteo_vistas': article.conteo_vistas,
                    'conteo_comentarios': article.conteo_comentarios,
                    'imagen_principal': article.imagen_principal.decode('utf-8') if article.imagen_principal else None,
                    'create_date': article.create_date.isoformat() if article.create_date else None
                })
            
            response = {
                'success': True,
                'data': {
                    'articles': articles_data,
                    'total': total_count
                }
            }
            
            # Agregar nuevo token si fue renovado
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al obtener mis artículos: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener artículos',
                'error_code': 'GET_MY_ARTICLES_ERROR'
            }
