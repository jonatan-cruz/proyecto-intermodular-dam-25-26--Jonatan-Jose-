# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import logging

from .auth_controller import verify_jwt_token, get_token_from_request, get_authenticated_user_with_refresh

_logger = logging.getLogger(__name__)


class SecondMarketChatController(http.Controller):
    """Controlador para gestión de chats y mensajes"""

    def _get_authenticated_user(self):
        """
        Obtener usuario autenticado desde el token
        Incluye renovación automática de tokens si es necesario
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/chats', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_chat(self, **kwargs):
        """
        Crear o recuperar un chat existente sobre un artículo
        
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
            
            # Verificar que no sea el propietario
            if article.id_propietario.id == user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No puedes chatear sobre tu propio artículo',
                    'error_code': 'SELF_CHAT'
                }
            
            # Buscar chat existente
            existing_chat = request.env['second_market.chat'].sudo().search([
                ('id_articulo', '=', article.id),
                ('id_comprador', '=', user_data['user_id'])
            ], limit=1)
            
            if existing_chat:
                response = {
                    'success': True,
                    'message': 'Chat recuperado',
                    'data': {
                        'chat_id': existing_chat.id,
                        'new_chat': False
                    }
                }
                
                if new_token:
                    response['new_token'] = new_token
                    
                return response
            
            # Crear nuevo chat
            chat = request.env['second_market.chat'].sudo().create({
                'id_articulo': article.id,
                'id_comprador': user_data['user_id']
            })
            
            response = {
                'success': True,
                'message': 'Chat creado exitosamente',
                'data': {
                    'chat_id': chat.id,
                    'new_chat': True
                }
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al crear chat: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al crear chat',
                'error_code': 'CREATE_CHAT_ERROR'
            }

    @http.route('/api/v1/chats', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_chats(self, **kwargs):
        """Obtener todos los chats del usuario autenticado"""
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
            
            # Chats donde el usuario es comprador o vendedor
            chats = request.env['second_market.chat'].sudo().search([
                '|',
                ('id_comprador', '=', user_data['user_id']),
                ('id_vendedor', '=', user_data['user_id']),
                ('activo', '=', True)
            ], order='fecha_ultimo_mensaje desc')
            
            chats_data = []
            for chat in chats:
                # Determinar el otro usuario
                if chat.id_comprador.id == user_data['user_id']:
                    otro_usuario = chat.id_vendedor
                else:
                    otro_usuario = chat.id_comprador
                
                chats_data.append({
                    'id': chat.id,
                    'articulo': {
                        'id': chat.id_articulo.id,
                        'nombre': chat.id_articulo.nombre,
                        'precio': chat.id_articulo.precio
                    },
                    'otro_usuario': {
                        'id': otro_usuario.id,
                        'nombre': otro_usuario.name
                    },
                    'ultimo_mensaje': chat.ultimo_mensaje,
                    'fecha_ultimo_mensaje': chat.fecha_ultimo_mensaje.isoformat() if chat.fecha_ultimo_mensaje else None,
                    'conteo_mensajes': chat.conteo_mensajes
                })
            
            response = {
                'success': True,
                'data': {'chats': chats_data}
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al obtener chats: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener chats',
                'error_code': 'GET_CHATS_ERROR'
            }

    @http.route('/api/v1/chats/<int:chat_id>/messages', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_chat_messages(self, chat_id, **kwargs):
        """Obtener mensajes de un chat"""
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
            
            chat = request.env['second_market.chat'].sudo().browse(chat_id)
            
            if not chat.exists():
                return {
                    'success': False,
                    'message': 'Chat no encontrado',
                    'error_code': 'CHAT_NOT_FOUND'
                }
            
            # Verificar que el usuario sea parte del chat
            if chat.id_comprador.id != user_data['user_id'] and chat.id_vendedor.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes acceso a este chat',
                    'error_code': 'FORBIDDEN'
                }
            
            messages_data = []
            for message in chat.ids_mensajes:
                messages_data.append({
                    'id': message.id,
                    'contenido': message.contenido,
                    'fecha_envio': message.fecha_envio.isoformat() if message.fecha_envio else None,
                    'leido': message.leido,
                    'usuario': {
                        'id': message.id_usuario.id,
                        'nombre': message.id_usuario.name
                    },
                    'is_mine': message.id_usuario.id == user_data['user_id']
                })
            
            response = {
                'success': True,
                'data': {
                    'messages': messages_data,
                    'chat_info': {
                        'articulo': {
                            'id': chat.id_articulo.id,
                            'nombre': chat.id_articulo.nombre
                        }
                    }
                }
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al obtener mensajes: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener mensajes',
                'error_code': 'GET_MESSAGES_ERROR'
            }

    @http.route('/api/v1/chats/<int:chat_id>/messages', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def send_message(self, chat_id, **kwargs):
        """
        Enviar un mensaje en un chat
        
        Parámetros requeridos:
        - contenido: str
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
            
            if not data.get('contenido'):
                return {
                    'success': False,
                    'message': 'El contenido del mensaje es requerido',
                    'error_code': 'MISSING_FIELD'
                }
            
            chat = request.env['second_market.chat'].sudo().browse(chat_id)
            
            if not chat.exists():
                return {
                    'success': False,
                    'message': 'Chat no encontrado',
                    'error_code': 'CHAT_NOT_FOUND'
                }
            
            # Verificar que el usuario sea parte del chat
            if chat.id_comprador.id != user_data['user_id'] and chat.id_vendedor.id != user_data['user_id']:
                return {
                    'success': False,
                    'message': 'No tienes acceso a este chat',
                    'error_code': 'FORBIDDEN'
                }
            
            # Crear mensaje
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
            
        except Exception as e:
            _logger.error(f"Error al enviar mensaje: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al enviar mensaje',
                'error_code': 'SEND_MESSAGE_ERROR'
            }


class SecondMarketReportController(http.Controller):
    """Controlador para gestión de denuncias"""

    def _get_authenticated_user(self):
        """
        Obtener usuario autenticado desde el token
        Incluye renovación automática de tokens si es necesario
        """
        return get_authenticated_user_with_refresh()

    @http.route('/api/v1/reports', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def create_report(self, **kwargs):
        """
        Crear una denuncia sobre un artículo, comentario o usuario.
        Genera un registro visible para los moderadores/empleados en Odoo.
        Requiere autenticación JWT.
        
        Parámetros requeridos:
        - tipo_denuncia: str ('articulo', 'comentario' o 'usuario')
        - motivo: str
        - descripcion: str
        - articulo_id: int (si tipo_denuncia='articulo')
        - comentario_id: int (si tipo_denuncia='comentario')
        - usuario_id: int (si tipo_denuncia='usuario')
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
            
            # Validar campos requeridos
            required_fields = ['tipo_denuncia', 'motivo', 'descripcion']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'El campo {field} es requerido',
                        'error_code': 'MISSING_FIELD'
                    }
            
            # Validar tipo de denuncia
            if data['tipo_denuncia'] not in ['articulo', 'comentario', 'usuario']:
                return {
                    'success': False,
                    'message': 'Tipo de denuncia inválido',
                    'error_code': 'INVALID_TYPE'
                }
            
            # Preparar valores
            report_vals = {
                'tipo_denuncia': data['tipo_denuncia'],
                'motivo': data['motivo'],
                'descripcion': data['descripcion'],
                'id_denunciante': user_data['user_id'],
                'estado': 'pendiente'
            }
            
            if data['tipo_denuncia'] == 'articulo':
                if not data.get('articulo_id'):
                    return {
                        'success': False,
                        'message': 'El artículo es requerido',
                        'error_code': 'MISSING_FIELD'
                    }
                report_vals['id_articulo'] = data['articulo_id']
            elif data['tipo_denuncia'] == 'comentario':
                if not data.get('comentario_id'):
                    return {
                        'success': False,
                        'message': 'El comentario es requerido',
                        'error_code': 'MISSING_FIELD'
                    }
                report_vals['id_comentario'] = data['comentario_id']
            elif data['tipo_denuncia'] == 'usuario':
                if not data.get('usuario_id'):
                    return {
                        'success': False,
                        'message': 'El usuario es requerido',
                        'error_code': 'MISSING_FIELD'
                    }
                report_vals['id_usuario_denunciado'] = data['usuario_id']
            
            # Crear denuncia
            report = request.env['second_market.report'].sudo().create(report_vals)
            
            response = {
                'success': True,
                'message': 'Denuncia creada exitosamente',
                'data': {
                    'report_id': report.id,
                    'num_denuncia': report.num_denuncia
                }
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

    @http.route('/api/v1/reports/my-reports', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_my_reports(self, **kwargs):
        """Obtener denuncias realizadas por el usuario"""
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
                    report_dict['articulo'] = {
                        'id': report.id_articulo.id,
                        'nombre': report.id_articulo.nombre
                    }
                elif report.tipo_denuncia == 'comentario' and report.id_comentario:
                    report_dict['comentario'] = {
                        'id': report.id_comentario.id,
                        'texto': report.id_comentario.texto[:50]
                    }
                elif report.tipo_denuncia == 'usuario' and report.id_usuario_denunciado:
                    report_dict['usuario'] = {
                        'id': report.id_usuario_denunciado.id,
                        'nombre': report.id_usuario_denunciado.name
                    }
                
                reports_data.append(report_dict)
            
            response = {
                'success': True,
                'data': {'reports': reports_data}
            }
            
            if new_token:
                response['new_token'] = new_token
                
            return response
            
        except Exception as e:
            _logger.error(f"Error al obtener denuncias: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener denuncias',
                'error_code': 'GET_REPORTS_ERROR'
            }


class SecondMarketCategoryController(http.Controller):
    """Controlador para categorías y etiquetas"""

    @http.route('/api/v1/categories', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_categories(self, **kwargs):
        """Obtener todas las categorías activas"""
        try:
            categories = request.env['second_market.category'].sudo().search([
                ('activo', '=', True)
            ], order='name')
            
            categories_data = []
            for category in categories:
                categories_data.append({
                    'id': category.id,
                    'name': category.name,
                    'descripcion': category.descripcion,
                    'icono': category.icono,
                    'color': category.color,
                    'conteo_articulos': category.conteo_articulos,
                    'imagen': category.imagen.decode('utf-8') if category.imagen else None
                })
            
            return {
                'success': True,
                'data': {'categories': categories_data}
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener categorías: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener categorías',
                'error_code': 'GET_CATEGORIES_ERROR'
            }

    @http.route('/api/v1/categories/<int:category_id>/articles', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_category_articles(self, category_id, **kwargs):
        """Obtener artículos de una categoría específica"""
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
            
            return {
                'success': True,
                'data': {'articles': articles_data}
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener artículos de categoría: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener artículos',
                'error_code': 'GET_CATEGORY_ARTICLES_ERROR'
            }

    @http.route('/api/v1/tags', type='json', auth='public', methods=['GET', 'POST'], csrf=False, cors='*')
    def get_tags(self, **kwargs):
        """Obtener todas las etiquetas disponibles"""
        try:
            tags = request.env['second_market.tag'].sudo().search([])
            
            tags_data = []
            for tag in tags:
                tags_data.append({
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color
                })
            
            return {
                'success': True,
                'data': {'tags': tags_data}
            }
            
        except Exception as e:
            _logger.error(f"Error al obtener etiquetas: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al obtener etiquetas',
                'error_code': 'GET_TAGS_ERROR'
            }
