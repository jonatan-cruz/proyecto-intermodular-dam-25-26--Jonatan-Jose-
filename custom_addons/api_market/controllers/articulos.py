# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import logging
import base64

from .auth_controller import verify_jwt_token, get_token_from_request

_logger = logging.getLogger(__name__)


class SecondMarketArticleController(http.Controller):
    """Controlador para gestión de artículos - API v1"""

    def _get_authenticated_user(self):
        """Obtener usuario autenticado desde el token del header Authorization"""
        token = get_token_from_request()
        if not token:
            return None
        return verify_jwt_token(token)

    @http.route('/api/v1/articles', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_articles(self, **kwargs):
        """
        Obtener lista de artículos publicados filtrados por diversos criterios.
        Permite la búsqueda global por texto y filtrado por categoría, precio, estado y localidad.
        
        Parámetros opcionales:
        - limit: int (default: 20)
        - offset: int (default: 0)
        - categoria_id: int
        - search: str (búsqueda por nombre o descripción)
        - precio_min: float
        - precio_max: float
        - estado_producto: str
        - localidad: str
        """
        try:
            data = request.params
            
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
            
            # Formatear respuesta
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
                    'imagen_principal': article.imagen_principal.decode('utf-8') if article.imagen_principal else None,
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

    @http.route('/api/v1/articles/<int:article_id>', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_article_detail(self, article_id, **kwargs):
        """
        Obtener detalle de un artículo específico
        Incrementa el contador de vistas
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
        """
        Crear un nuevo artículo en estado borrador.
        Requiere autenticación mediante token JWT. El usuario autenticado se convertirá en el propietario.
        Permite subir múltiples imágenes (1-10) y asignar etiquetas existentes.
        
        Requiere autenticación mediante token JWT en header Authorization
        
        Parámetros requeridos:
        - nombre: str
        - descripcion: str
        - precio: float
        - estado_producto: str
        - localidad: str
        - categoria_id: int
        - imagenes: list de dict [{image: base64, name: str, sequence: int}]
        
        Parámetros opcionales:
        - antiguedad: int
        - latitud: float
        - longitud: float
        - etiquetas_ids: list de int
        """
        try:
            # Verificar autenticación
            user_data = self._get_authenticated_user()
            if not user_data:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
            data = request.params
            
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
                'estado_publicacion': 'borrador'
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
            
            return {
                'success': True,
                'message': 'Artículo creado exitosamente',
                'data': {
                    'article_id': article.id,
                    'codigo': article.codigo
                }
            }
            
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
        """
        Actualizar un artículo existente
        Solo el propietario puede actualizar
        Requiere autenticación mediante token JWT en header Authorization
        """
        try:
            # Verificar autenticación
            user_data = self._get_authenticated_user()
            if not user_data:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
            article = request.env['second_market.article'].sudo().browse(article_id)
            
            if not article.exists():
                return {
                    'success': False,
                    'message': 'Artículo no encontrado',
                    'error_code': 'ARTICLE_NOT_FOUND'
                }
            
            # Verificar que sea el propietario
            if article.id_propietario.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes permiso para editar este artículo',
                    'error_code': 'FORBIDDEN'
                }
            
            data = request.params
            
            # Campos actualizables
            update_vals = {}
            updatable_fields = ['nombre', 'descripcion', 'precio', 'estado_producto', 
                              'localidad', 'antiguedad', 'latitud', 'longitud', 'categoria_id']
            
            for field in updatable_fields:
                if field in data:
                    if field == 'categoria_id':
                        update_vals['id_categoria'] = data[field]
                    else:
                        update_vals[field] = data[field]
            
            if update_vals:
                article.sudo().write(update_vals)
            
            # Actualizar etiquetas si se envían
            if 'etiquetas_ids' in data:
                etiquetas_ids = data['etiquetas_ids']
                # Validar que todas las etiquetas existan
                existing_tags = request.env['second_market.tag'].sudo().search([
                    ('id', 'in', etiquetas_ids)
                ])
                existing_tag_ids = existing_tags.ids
                
                # Filtrar solo las etiquetas que existen
                valid_tag_ids = [tag_id for tag_id in etiquetas_ids if tag_id in existing_tag_ids]
                article.sudo().write({'ids_etiquetas': [(6, 0, valid_tag_ids)]})
                
                # Advertir si algunas etiquetas no existen
                invalid_tags = set(etiquetas_ids) - set(existing_tag_ids)
                if invalid_tags:
                    _logger.warning(f"Etiquetas no encontradas al actualizar (ignoradas): {invalid_tags}")
            
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
        """
        Publicar un artículo (cambiar estado a 'publicado')
        Requiere autenticación mediante token JWT en header Authorization
        """
        try:
            user_data = self._get_authenticated_user()
            if not user_data:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
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
            
            return {
                'success': True,
                'message': 'Artículo publicado exitosamente'
            }
            
        except Exception as e:
            _logger.error(f"Error al publicar artículo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al publicar artículo',
                'error_code': 'PUBLISH_ERROR'
            }

    @http.route('/api/v1/articles/<int:article_id>', type='json', auth='public', methods=['DELETE'], csrf=False, cors='*')
    def delete_article(self, article_id, **kwargs):
        """
        Eliminar (desactivar) un artículo
        Requiere autenticación mediante token JWT en header Authorization
        """
        try:
            user_data = self._get_authenticated_user()
            if not user_data:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
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
            
            return {
                'success': True,
                'message': 'Artículo eliminado exitosamente'
            }
            
        except Exception as e:
            _logger.error(f"Error al eliminar artículo: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al eliminar artículo',
                'error_code': 'DELETE_ERROR'
            }

    @http.route('/api/v1/articles/my-articles', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_my_articles(self, **kwargs):
        """
        Obtener artículos del usuario autenticado
        Requiere autenticación mediante token JWT en header Authorization
        """
        try:
            user_data = self._get_authenticated_user()
            if not user_data:
                return {
                    'success': False,
                    'message': 'No autenticado. Debe proporcionar token en header Authorization',
                    'error_code': 'UNAUTHORIZED'
                }
            
            data = request.params
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
            
            return {
                'success': True,
                'data': {
                    'articles': articles_data,
                    'total': total_count
                }
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener mis artículos: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener artículos',
                'error_code': 'GET_MY_ARTICLES_ERROR'
            }
