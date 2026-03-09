# -*- coding: utf-8 -*-

"""
Módulo de autenticación JWT para la API de Second Market.

Proporciona funciones auxiliares reutilizables para extraer, verificar
y renovar automáticamente tokens JWT en los distintos controladores
de la API.

Variables de configuración (importadas desde ``config.py`` con fallback):

- ``JWT_SECRET_KEY``: Clave secreta para firmar/verificar tokens.
- ``JWT_ALGORITHM``: Algoritmo de cifrado (por defecto ``HS256``).
- ``JWT_EXP_DELTA_SECONDS``: Duración del token en segundos (por defecto 86 400 = 24h).
- ``JWT_REFRESH_THRESHOLD_SECONDS``: Segundos restantes a partir de los cuales se
  renueva automáticamente el token (por defecto 7 200 = 2h).
"""

from odoo.http import request
import jwt
import datetime
import logging

_logger = logging.getLogger(__name__)

# Importar configuración
try:
    from ..config import (
        JWT_SECRET_KEY,
        JWT_ALGORITHM,
        JWT_EXP_DELTA_SECONDS,
        JWT_REFRESH_THRESHOLD_SECONDS,
    )
except ImportError:
    # Fallback si no existe config.py
    JWT_SECRET_KEY = 'second_market_secret_key_2025'
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_DELTA_SECONDS = 86400
    JWT_REFRESH_THRESHOLD_SECONDS = 7200


def get_token_from_request():
    """Extraer el token JWT del header ``Authorization`` de la petición actual.

    Solo se admite el formato ``Authorization: Bearer <token>``.

    :return: Token JWT como cadena de texto, o ``None`` si no está presente.
    :rtype: str or None

    Ejemplo de header esperado::

        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    auth_header = request.httprequest.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '').strip()
    return None


def verify_jwt_token(token):
    """Verificar un token JWT y devolver los datos del usuario asociado.

    Decodifica el token, extrae el ``user_id`` del payload, y comprueba
    que el usuario exista y esté activo en ``second_market.user``.

    Uso típico desde otros controladores::

        from .auth_controller import verify_jwt_token

        user_data = verify_jwt_token(token)
        if user_data:
            user_id = user_data['user_id']
        else:
            # Token inválido o usuario inactivo

    :param token: Token JWT a verificar.
    :type token: str
    :return: Diccionario con datos del usuario si el token es válido:

        .. code-block:: python

            {
                'user_id': int,
                'id_usuario': str,
                'login': str,
                'name': str,
                'user': second_market.user  # Recordset completo
            }

        Devuelve ``None`` si el token ha expirado, es inválido o el
        usuario no existe / está inactivo.
    :rtype: dict or None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')

        if not user_id:
            _logger.warning("Token sin user_id")
            return None

        user = request.env['second_market.user'].sudo().browse(user_id)

        if not user.exists() or not user.activo:
            _logger.warning(f"Usuario {user_id} no encontrado o inactivo")
            return None

        return {
            'user_id': user.id,
            'id_usuario': user.id_usuario,
            'login': user.login,
            'name': user.name,
            'user': user
        }

    except jwt.ExpiredSignatureError:
        _logger.warning("Token expirado")
        return None
    except jwt.InvalidTokenError as e:
        _logger.warning(f"Token inválido: {str(e)}")
        return None
    except Exception as e:
        _logger.error(f"Error al verificar token: {str(e)}", exc_info=True)
        return None


def auto_refresh_token_if_needed(token):
    """Renovar automáticamente un token JWT si está próximo a expirar.

    Si al token le quedan menos de ``JWT_REFRESH_THRESHOLD_SECONDS`` segundos
    de vida, genera y devuelve un nuevo token con la fecha de expiración
    reiniciada. El usuario no nota la renovación.

    :param token: Token JWT actual del cliente.
    :type token: str
    :return: Nuevo token JWT si la renovación fue necesaria, o ``None`` si
        todavía le queda suficiente tiempo de vida o si ocurre algún error.
    :rtype: str or None

    .. note::
        Si el token ya está expirado (``ExpiredSignatureError``), esta función
        devuelve ``None`` sin intentar la renovación.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return None

        now = datetime.datetime.utcnow()
        exp_datetime = datetime.datetime.utcfromtimestamp(exp_timestamp)
        time_remaining = (exp_datetime - now).total_seconds()

        if time_remaining < JWT_REFRESH_THRESHOLD_SECONDS:
            user_id = payload.get('user_id')
            user = request.env['second_market.user'].sudo().browse(user_id)

            if not user.exists() or not user.activo:
                _logger.warning(f"Usuario {user_id} no encontrado o inactivo durante auto-refresh")
                return None

            new_payload = {
                'user_id': user.id,
                'id_usuario': user.id_usuario,
                'login': user.login,
                'name': user.name,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXP_DELTA_SECONDS),
                'iat': datetime.datetime.utcnow()
            }

            new_token = jwt.encode(new_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            _logger.info(f"Token auto-renovado para usuario: {user.login} (ID: {user.id})")
            return new_token

        return None

    except jwt.ExpiredSignatureError:
        return None
    except Exception as e:
        _logger.error(f"Error en auto-refresh de token: {str(e)}", exc_info=True)
        return None


def get_authenticated_user_with_refresh():
    """Verificar la autenticación del usuario actual e incluir auto-refresh del token.

    Función helper completa que encadena:

    1. Extracción del token del header ``Authorization``.
    2. Verificación de validez y existencia del usuario.
    3. Comprobación de si el token necesita renovación automática.

    Uso típico en controladores::

        auth_result = get_authenticated_user_with_refresh()
        if not auth_result:
            return {'success': False, 'message': 'No autenticado'}

        user_data = auth_result['user_data']
        new_token = auth_result.get('new_token')  # None si no se renovó

        # ...lógica de negocio...

        response = {'success': True, 'data': ...}
        if new_token:
            response['new_token'] = new_token  # El cliente debe guardar el nuevo token
        return response

    :return: Diccionario con los datos de autenticación:

        .. code-block:: python

            {
                'user_data': dict,      # Resultado de verify_jwt_token()
                'new_token': str        # Solo presente si el token fue renovado
            }

        Devuelve ``None`` si no hay token, el token es inválido o el usuario
        está inactivo.
    :rtype: dict or None
    """
    token = get_token_from_request()

    if not token:
        return None

    user_data = verify_jwt_token(token)

    if not user_data:
        return None

    new_token = auto_refresh_token_if_needed(token)

    result = {'user_data': user_data}

    if new_token:
        result['new_token'] = new_token

    return result
