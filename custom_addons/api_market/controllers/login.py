# -*- coding: utf-8 -*-

"""
Controlador de autenticación para la API REST de Second Market.

Gestiona el login, registro, verificación y logout de usuarios mediante
tokens JWT (JSON Web Tokens) firmados con el algoritmo HS256.

**Endpoints disponibles:**

- ``POST /api/v1/auth/login``    — Autenticar usuario y obtener token.
- ``POST /api/v1/auth/register`` — Registrar nuevo usuario y obtener token.
- ``POST /api/v1/auth/verify``   — Verificar validez de un token existente.
- ``POST /api/v1/auth/logout``   — Cerrar sesión (logging del evento).
"""

from odoo import http, _
from odoo.http import request
import jwt
import datetime
import logging
from passlib.context import CryptContext

#: Contexto de hashing de contraseñas (mismo esquema que en `second_market.user`).
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
    JWT_SECRET_KEY = 'second_market_secret_key_2025'
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_DELTA_SECONDS = 86400
    RESPONSE_MESSAGES = {}
    ERROR_CODES = {}

_logger = logging.getLogger(__name__)


class SecondMarketAuthController(http.Controller):
    """Controlador de autenticación para Second Market — API v1.

    Proporciona endpoints de login, registro, verificación de token y logout.
    Todos los endpoints son de tipo ``json`` y no requieren autenticación
    previa de Odoo (``auth='public'``).
    """

    @http.route('/api/v1/auth/login', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def login(self, **kwargs):
        """Autenticar un usuario y devolver un token JWT.

        Verifica las credenciales contra ``second_market.user``, comprueba que la
        cuenta esté activa y genera un token JWT con expiración configurada en
        ``JWT_EXP_DELTA_SECONDS``.

        **Body JSON esperado:**

        .. code-block:: json

            {
                "login": "usuario@ejemplo.com",
                "password": "miContraseña123"
            }

        **Respuesta exitosa:**

        .. code-block:: json

            {
                "success": true,
                "message": "Login exitoso",
                "data": {
                    "token": "<JWT>",
                    "expires_in": 86400,
                    "user": {
                        "id": 1,
                        "id_usuario": "0000001",
                        "name": "Jonatan",
                        "login": "jonatan@ejemplo.com",
                        "calificacion_promedio": 4.5,
                        "productos_en_venta": 3
                    }
                }
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo (no se usan directamente).
        :return: Diccionario con ``success``, ``message`` y ``data`` (token + datos de usuario).
        :rtype: dict
        """
        try:
            data = request.params or request.httprequest.get_json(force=True) or {}
            login = data.get('login')
            password = data.get('password')

            if not login or not password:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('MISSING_CREDENTIALS', 'El login y la contraseña son requeridos'),
                    'error_code': ERROR_CODES.get('MISSING_CREDENTIALS', 'MISSING_CREDENTIALS')
                }

            user = request.env['second_market.user'].sudo().search([
                ('login', '=', login)
            ], limit=1)

            if not user:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('LOGIN_FAILED', 'Credenciales inválidas'),
                    'error_code': ERROR_CODES.get('INVALID_CREDENTIALS', 'INVALID_CREDENTIALS')
                }

            if not user.activo:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('ACCOUNT_DISABLED', 'Tu cuenta está deshabilitada'),
                    'error_code': ERROR_CODES.get('ACCOUNT_DISABLED', 'ACCOUNT_DISABLED')
                }

            if not crypt_context.verify(password, user.password):
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('LOGIN_FAILED', 'Credenciales inválidas'),
                    'error_code': ERROR_CODES.get('INVALID_CREDENTIALS', 'INVALID_CREDENTIALS')
                }

            payload = {
                'user_id': user.id,
                'id_usuario': user.id_usuario,
                'login': user.login,
                'name': user.name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS),
                'iat': datetime.datetime.utcnow()
            }

            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

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
            }

        except Exception as e:
            _logger.error(f"Error en login: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': RESPONSE_MESSAGES.get('INTERNAL_ERROR', 'Error interno del servidor'),
                'error_code': ERROR_CODES.get('INTERNAL_ERROR', 'INTERNAL_ERROR')
            }

    @http.route('/api/v1/auth/register', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def register(self, **kwargs):
        """Registrar un nuevo usuario y devolver un token JWT.

        Valida los campos requeridos, verifica que el login no esté en uso,
        crea el usuario (la contraseña se hashea automáticamente en
        :meth:`~second_market.user.SecondMarketUser.create`) y genera un
        token JWT de sesión.

        **Body JSON esperado:**

        .. code-block:: json

            {
                "name": "Jonatan",
                "login": "jonatan@ejemplo.com",
                "password": "miContraseña123",
                "telefono": "612345678",
                "ubicacion": "Sevilla",
                "biografia": "Hola, soy Jonatan"
            }

        Los campos ``telefono``, ``ubicacion`` y ``biografia`` son opcionales.

        **Respuesta exitosa:**

        .. code-block:: json

            {
                "success": true,
                "message": "Usuario registrado exitosamente",
                "data": {
                    "token": "<JWT>",
                    "expires_in": 86400,
                    "user": { ... }
                }
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``message`` y ``data`` (token + datos de usuario).
        :rtype: dict
        """
        try:
            data = request.params or request.httprequest.get_json(force=True) or {}
            required_fields = ['name', 'login', 'password']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'message': f'El campo {field} es requerido',
                        'error_code': ERROR_CODES.get('MISSING_FIELD', 'MISSING_FIELD')
                    }

            if len(data.get('password', '')) < 8:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('PASSWORD_TOO_SHORT', 'La contraseña debe tener al menos 8 caracteres'),
                    'error_code': ERROR_CODES.get('PASSWORD_TOO_SHORT', 'PASSWORD_TOO_SHORT')
                }

            existing_user = request.env['second_market.user'].sudo().search([
                ('login', '=', data.get('login'))
            ], limit=1)

            if existing_user:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('LOGIN_EXISTS', 'Ya existe un usuario con este login'),
                    'error_code': ERROR_CODES.get('LOGIN_EXISTS', 'LOGIN_EXISTS')
                }

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

            payload = {
                'user_id': user.id,
                'id_usuario': user.id_usuario,
                'login': user.login,
                'name': user.name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS),
                'iat': datetime.datetime.utcnow()
            }

            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

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
            }

        except Exception as e:
            _logger.error(f"Error en registro: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': RESPONSE_MESSAGES.get('REGISTRATION_FAILED', 'Error al registrar usuario'),
                'error_code': 'REGISTRATION_ERROR'
            }

    @http.route('/api/v1/auth/verify', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def verify_token(self, **kwargs):
        """Verificar la validez de un token JWT.

        El token debe enviarse en el header HTTP ``Authorization``::

            Authorization: Bearer <token>

        Si el token es válido, devuelve los datos del usuario asociado.

        **Respuesta exitosa:**

        .. code-block:: json

            {
                "success": true,
                "message": "Token válido",
                "data": {
                    "user": {
                        "id": 1,
                        "name": "Jonatan",
                        "login": "jonatan@ejemplo.com",
                        "calificacion_promedio": 4.5
                    }
                }
            }

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success``, ``message`` y ``data`` (perfil del usuario).
        :rtype: dict
        """
        try:
            from .auth_controller import get_token_from_request, verify_jwt_token

            token = get_token_from_request()

            if not token:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('TOKEN_MISSING', 'Token no proporcionado en el header Authorization'),
                    'error_code': ERROR_CODES.get('TOKEN_MISSING', 'TOKEN_MISSING')
                }

            user_data = verify_jwt_token(token)

            if not user_data:
                return {
                    'success': False,
                    'message': RESPONSE_MESSAGES.get('TOKEN_INVALID', 'Token inválido o expirado'),
                    'error_code': ERROR_CODES.get('TOKEN_INVALID', 'TOKEN_INVALID')
                }

            user = user_data['user']

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
                'data': {'user': user_info}
            }

        except Exception as e:
            _logger.error(f"Error en verificación de token: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error al verificar token',
                'error_code': 'VERIFICATION_ERROR'
            }

    @http.route('/api/v1/auth/logout', type='json', auth='public', methods=['POST'], csrf=False, cors='*')
    def logout(self, **kwargs):
        """Registrar el cierre de sesión del usuario.

        JWT es stateless: el logout real se realiza en el cliente eliminando
        el token almacenado. Este endpoint se usa principalmente para registrar
        el evento en los logs del servidor.

        .. note::
            No invalida el token en el servidor. El cliente debe eliminar
            el token de su almacenamiento local tras llamar a este endpoint.

        :param kwargs: Parámetros adicionales del dispatcher de Odoo.
        :return: Diccionario con ``success = True`` y mensaje de confirmación.
        :rtype: dict
        """
        try:
            from .auth_controller import get_token_from_request

            token = get_token_from_request()

            if token:
                try:
                    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
                    _logger.info(f"Logout para usuario: {payload.get('login')} (ID: {payload.get('user_id')})")
                except Exception:
                    pass

            return {
                'success': True,
                'message': 'Logout exitoso'
            }

        except Exception as e:
            _logger.error(f"Error en logout: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': 'Error en logout',
                'error_code': 'LOGOUT_ERROR'
            }
