# -*- coding: utf-8 -*-

from odoo.http import request
import jwt
import logging

_logger = logging.getLogger(__name__)

# Importar configuración
try:
    from ..config import (
        JWT_SECRET_KEY, 
        JWT_ALGORITHM, 
        JWT_EXP_DELTA_SECONDS,
    )
except ImportError:
    # Fallback si no existe config.py
    JWT_SECRET_KEY = 'second_market_secret_key_2025'
    JWT_ALGORITHM = 'HS256'
    JWT_EXP_DELTA_SECONDS = 86400


def get_token_from_request():
    """
    Extrae el token JWT del header Authorization o del body
    
    Soporta:
    - Header: Authorization: Bearer <token>
    - Body: {"token": "<token>"}
    
    Retorna:
        str: token si se encuentra
        None: si no hay token
    """
    # Intentar obtener del header Authorization
    auth_header = request.httprequest.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '').strip()
    
    # Intentar obtener del body
    try:
        data = request.httprequest.get_json(force=True) or {}
        if data.get('token'):
            return data.get('token')
    except:
        pass
    
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