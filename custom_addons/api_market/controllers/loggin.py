# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.http import request
import jwt
import datetime
import logging
from passlib.context import CryptContext

# Configuración de hashing (mismo que en second_market.user)
crypt_context = CryptContext(schemes=["pbkdf2_sha512", "plaintext"], deprecated="auto")

# Importar configuración
try:
    from ..config import (
        JWT_SECRET_KEY, 
        JWT_ALGORITHM, 
        JWT_EXP_DELTA_SECONDS,
        RESPONSE_MESSAGES,
        ERROR_CODES
    )
except ImportError:
    # Fallback si no existe config.py
    JWT_SECRET_KEY = 'second_market_secret_key_2025'
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_DELTA_SECONDS = 86400
    RESPONSE_MESSAGES = {}
    ERROR_CODES = {}

_logger = logging.getLogger(__name__)


class SecondMarketAuthController(http.Controller):
    """Controlador de autenticación para Second Market - API v1"""

    @http.route('/api/v1/auth/login', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def login(self, **kwargs):
        """
        Endpoint de login para usuarios
        
        Parámetros esperados en el body (JSON):
        - login: str (email o nombre de usuario)
        - password: str (contraseña)
        
        Retorna:
        - success: bool
        - message: str
        - data: dict con token y datos del usuario (si success=True)
        """
        try:
            # Obtener datos del request
            data = request.httprequest.get_json(force=True) or {}
            login = data.get('login')
            password = data.get('password')
            
            # Validar que se enviaron los campos requeridos
            if not login or not password:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('MISSING_CREDENTIALS', 'El login y la contraseña son requeridos'),
                    'error_code': ERROR_CODES.get('MISSING_CREDENTIALS', 'MISSING_CREDENTIALS')
                }, 400
            
            # Buscar el usuario en el módulo second_market
            user = request.env['second_market.user'].sudo().search([
                ('login', '=', login)
            ], limit=1)
            
            # Validar que el usuario existe
            if not user:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('LOGIN_FAILED', 'Credenciales inválidas'),
                    'error_code': ERROR_CODES.get('INVALID_CREDENTIALS', 'INVALID_CREDENTIALS')
                }, 401
            
            # Validar que el usuario está activo
            if not user.activo:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('ACCOUNT_DISABLED', 'Tu cuenta está deshabilitada'),
                    'error_code': ERROR_CODES.get('ACCOUNT_DISABLED', 'ACCOUNT_DISABLED')
                }, 403
            
            # Validar la contraseña usando verificación de hash
            if not crypt_context.verify(password, user.password):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('LOGIN_FAILED', 'Credenciales inválidas'),
                    'error_code': ERROR_CODES.get('INVALID_CREDENTIALS', 'INVALID_CREDENTIALS')
                }, 401
            
            # Generar el token JWT con caducidad
            payload = {
                'user_id': user.id,
                'id_usuario': user.id_usuario,
                'login': user.login,
                'name': user.name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS),
                'iat': datetime.datetime.utcnow()
            }
            
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            
            # Preparar datos del usuario para la respuesta
            user_data = {
                'id': user.id,
                'id_usuario': user.id_usuario,
                'name': user.name,
                'login': user.login,
                'telefono': user.telefono,
                'ubicacion': user.ubicacion,
                'biografia': user.biografia,
                'calificacion_promedio': user.calificacion_promedio,
                'total_valoraciones': user.total_valoraciones,
                'productos_en_venta': user.productos_en_venta,
                'productos_vendidos': user.productos_vendidos,
                'productos_comprados': user.productos_comprados,
                'antiguedad': user.antiguedad,
                'fecha_registro': user.fecha_registro.isoformat() if user.fecha_registro else None,
            }
            
            _logger.info(f"Login exitoso para usuario: {user.login} (ID: {user.id})")
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES.get('LOGIN_SUCCESS', 'Login exitoso'),
                'data': {
                    'token': token,
                    'user': user_data,
                    'expires_in': JWT_EXP_DELTA_SECONDS
                }
            }, 200
            
        except Exception as e:
            _logger.error(f"Error en login: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': RESPONSE_MESSAGES.get('INTERNAL_ERROR', 'Error interno del servidor'),
                'error_code': ERROR_CODES.get('INTERNAL_ERROR', 'INTERNAL_ERROR')
            }, 500

    @http.route('/api/v1/auth/register', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def register(self, **kwargs):
        """
        Endpoint de registro para nuevos usuarios
        
        Parámetros esperados en el body (JSON):
        - name: str
        - login: str (email)
        - password: str
        - telefono: str (opcional)
        - ubicacion: str (opcional)
        - biografia: str (opcional)
        
        Retorna:
        - success: bool
        - message: str
        - data: dict con token y datos del usuario (si success=True)
        """
        try:
            data = request.httprequest.get_json(force=True) or {}
            
            # Validar campos requeridos
            required_fields = ['name', 'login', 'password']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'El campo {field} es requerido',
                        'error_code': ERROR_CODES.get('MISSING_FIELD', 'MISSING_FIELD')
                    }, 400
            
            # Validar longitud de contraseña
            if len(data.get('password', '')) < 8:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('PASSWORD_TOO_SHORT', 'La contraseña debe tener al menos 8 caracteres'),
                    'error_code': ERROR_CODES.get('PASSWORD_TOO_SHORT', 'PASSWORD_TOO_SHORT')
                }, 400
            
            # Verificar si el login ya existe
            existing_user = request.env['second_market.user'].sudo().search([
                ('login', '=', data.get('login'))
            ], limit=1)
            
            if existing_user:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('LOGIN_EXISTS', 'Ya existe un usuario con este login'),
                    'error_code': ERROR_CODES.get('LOGIN_EXISTS', 'LOGIN_EXISTS')
                }, 409
            
            # Crear el nuevo usuario
            # NOTA: La contraseña se hashea automáticamente en el método create() del modelo
            user_vals = {
                'name': data.get('name'),
                'login': data.get('login'),
                'password': data.get('password'),
                'telefono': data.get('telefono'),
                'ubicacion': data.get('ubicacion'),
                'biografia': data.get('biografia'),
                'activo': True
            }
            
            user = request.env['second_market.user'].sudo().create(user_vals)
            
            # Generar token JWT con caducidad
            payload = {
                'user_id': user.id,
                'id_usuario': user.id_usuario,
                'login': user.login,
                'name': user.name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS),
                'iat': datetime.datetime.utcnow()
            }
            
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            
            # Preparar datos del usuario
            user_data = {
                'id': user.id,
                'id_usuario': user.id_usuario,
                'name': user.name,
                'login': user.login,
                'telefono': user.telefono,
                'ubicacion': user.ubicacion,
                'biografia': user.biografia,
                'fecha_registro': user.fecha_registro.isoformat() if user.fecha_registro else None,
            }
            
            _logger.info(f"Registro exitoso para usuario: {user.login} (ID: {user.id})")
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES.get('REGISTRATION_SUCCESS', 'Usuario registrado exitosamente'),
                'data': {
                    'token': token,
                    'user': user_data,
                    'expires_in': JWT_EXP_DELTA_SECONDS
                }
            }, 201
            
        except Exception as e:
            _logger.error(f"Error en registro: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': RESPONSE_MESSAGES.get('REGISTRATION_FAILED', 'Error al registrar usuario'),
                'error_code': 'REGISTRATION_ERROR'
            }, 500

    @http.route('/api/v1/auth/verify', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def verify_token(self, **kwargs):
        """
        Endpoint para verificar la validez de un token JWT
        El token debe enviarse en el header Authorization: Bearer <token>
        
        Retorna:
        - success: bool
        - message: str
        - data: dict con datos del usuario (si el token es válido)
        """
        try:
            from .auth_controller import get_token_from_request, verify_jwt_token
            
            token = get_token_from_request()
            
            if not token:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('TOKEN_MISSING', 'Token no proporcionado en el header Authorization'),
                    'error_code': ERROR_CODES.get('TOKEN_MISSING', 'TOKEN_MISSING')
                }, 401
            
            # Verificar el token
            user_data = verify_jwt_token(token)
            
            if not user_data:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('TOKEN_INVALID', 'Token inválido o expirado'),
                    'error_code': ERROR_CODES.get('TOKEN_INVALID', 'TOKEN_INVALID')
                }, 401
            
            user = user_data['user']
            
            # Retornar datos del usuario
            user_info = {
                'id': user.id,
                'id_usuario': user.id_usuario,
                'name': user.name,
                'login': user.login,
                'telefono': user.telefono,
                'ubicacion': user.ubicacion,
                'biografia': user.biografia,
                'calificacion_promedio': user.calificacion_promedio,
                'total_valoraciones': user.total_valoraciones,
                'productos_en_venta': user.productos_en_venta,
                'productos_vendidos': user.productos_vendidos,
                'productos_comprados': user.productos_comprados,
            }
            
            return {
                'success': True,
                'message': RESPONSE_MESSAGES.get('TOKEN_VALID', 'Token válido'),
                'data': {
                    'user': user_info
                }
            }, 200
            
        except Exception as e:
            _logger.error(f"Error en verificación de token: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al verificar token',
                'error_code': 'VERIFICATION_ERROR'
            }, 500

    @http.route('/api/v1/auth/logout', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def logout(self, **kwargs):
        """
        Endpoint de logout (principalmente para logging)
        
        NOTA: JWT es stateless, por lo que el logout real se maneja en el cliente
        eliminando el token. Este endpoint es opcional y se usa principalmente para logging.
        """
        try:
            from .auth_controller import get_token_from_request
            
            token = get_token_from_request()
            
            if token:
                try:
                    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
                    _logger.info(f"Logout para usuario: {payload.get('login')} (ID: {payload.get('user_id')})")
                except:
                    pass
            
            return {
                'success': True,
                'message': 'Logout exitoso'
            }, 200
            
        except Exception as e:
            _logger.error(f"Error en logout: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error en logout',
                'error_code': 'LOGOUT_ERROR'
            }, 500
