# -*- coding: utf-8 -*-

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
    """
    Extrae el token JWT del header Authorization ÚNICAMENTE
    
    Soporta SOLO:
    - Header: Authorization: Bearer <token>
    
    Retorna:
        str: token si se encuentra
        None: si no hay token
    """
    # Obtener del header Authorization únicamente
    auth_header = request.httprequest.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '').strip()
    
    return None


def verify_jwt_token(token):
    """
    Función auxiliar para verificar tokens JWT en otros controladores
    
    Uso en otros controladores:
        from .auth_controller import verify_jwt_token
        
        user_data = verify_jwt_token(token)
        if user_data:
            # Token válido
            user_id = user_data['user_id']
        else:
            # Token inválido
    
    Retorna:
        dict con datos del usuario si el token es válido
        None si el token es inválido
    """
    try:
        # Decodificar el token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Obtener user_id del payload
        user_id = payload.get('user_id')
        
        if not user_id:
            _logger.warning("Token sin user_id")
            return None
        
        # Buscar el usuario en second_market.user
        user = request.env['second_market.user'].sudo().browse(user_id)
        
        # Verificar que el usuario existe y está activo
        if not user.exists() or not user.activo:
            _logger.warning(f"Usuario {user_id} no encontrado o inactivo")
            return None
        
        # Retornar datos del usuario
        return {
            'user_id': user.id,
            'id_usuario': user.id_usuario,
            'login': user.login,
            'name': user.name,
            'user': user  # Objeto completo del usuario
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
    """
    Verifica si un token necesita ser renovado automáticamente
    
    Si al token le quedan menos de JWT_REFRESH_THRESHOLD_SECONDS para expirar,
    genera y retorna un nuevo token automáticamente.
    
    Args:
        token (str): Token JWT actual
    
    Returns:
        str: Nuevo token si necesita renovación
        None: Si no necesita renovación o si hay error
    """
    try:
        # Decodificar el token para obtener la fecha de expiración
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Obtener timestamp de expiración
        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return None
        
        # Calcular tiempo restante hasta la expiración
        now = datetime.datetime.utcnow()
        exp_datetime = datetime.datetime.utcfromtimestamp(exp_timestamp)
        time_remaining = (exp_datetime - now).total_seconds()
        
        # Si quedan menos de JWT_REFRESH_THRESHOLD_SECONDS, renovar el token
        if time_remaining < JWT_REFRESH_THRESHOLD_SECONDS:
            user_id = payload.get('user_id')
            
            # Verificar que el usuario existe y está activo
            user = request.env['second_market.user'].sudo().browse(user_id)
            
            if not user.exists() or not user.activo:
                _logger.warning(f"Usuario {user_id} no encontrado o inactivo durante auto-refresh")
                return None
            
            # Generar nuevo token
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
        
        # No necesita renovación
        return None
        
    except jwt.ExpiredSignatureError:
        # Token ya expirado, no se puede auto-renovar
        return None
    except Exception as e:
        _logger.error(f"Error en auto-refresh de token: {str(e)}", exc_info=True)
        return None


def get_authenticated_user_with_refresh():
    """
    Función helper completa para autenticación con auto-refresh
    
    Esta función:
    1. Obtiene el token del request
    2. Verifica que sea válido
    3. Verifica si necesita renovación automática
    4. Retorna los datos del usuario y el nuevo token (si aplica)
    
    Uso en controladores:
        auth_result = get_authenticated_user_with_refresh()
        if not auth_result:
            return {'success': False, 'message': 'No autenticado'}, 401
        
        user_data = auth_result['user_data']
        new_token = auth_result.get('new_token')  # Puede ser None
        
        # ... tu lógica aquí ...
        
        # Al retornar, agregar el nuevo token si existe
        response_data = {'success': True, 'data': ...}
        if new_token:
            # El cliente debe leer este header y actualizar su token
            request.httprequest.environ['HTTP_X_NEW_TOKEN'] = new_token
        
        return response_data
    
    Returns:
        dict: {
            'user_data': dict con datos del usuario,
            'new_token': str (opcional, solo si se renovó)
        }
        None: Si no está autenticado o el token es inválido
    """
    token = get_token_from_request()
    
    if not token:
        return None
    
    # Verificar el token
    user_data = verify_jwt_token(token)
    
    if not user_data:
        return None
    
    # Verificar si necesita renovación automática
    new_token = auto_refresh_token_if_needed(token)
    
    result = {
        'user_data': user_data
    }
    
    if new_token:
        result['new_token'] = new_token
    
    return result
