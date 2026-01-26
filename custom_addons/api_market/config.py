# -*- coding: utf-8 -*-
"""
Configuración centralizada para la API de Second Market
"""

import os

# ============================================
# CONFIGURACIÓN JWT
# ============================================

# Obtener la clave secreta del entorno o usar una por defecto (NO USAR EN PRODUCCIÓN)
JWT_SECRET_KEY = os.environ.get('SECOND_MARKET_JWT_SECRET', 'second_market_secret_key_2025_OHYEAH')

# Algoritmo de firma JWT
JWT_ALGORITHM = 'HS256'

# Tiempo de expiración del token en segundos
# 3600 = 1 hora
# 86400 = 24 horas
# 604800 = 7 días
JWT_EXP_DELTA_SECONDS = int(os.environ.get('SECOND_MARKET_JWT_EXPIRATION', 86400))  # 24 horas por defecto

# Umbral para renovación automática de tokens (en segundos)
# Si al token le quedan menos de este tiempo, se renovará automáticamente
# 7200 = 2 horas
JWT_REFRESH_THRESHOLD_SECONDS = int(os.environ.get('SECOND_MARKET_JWT_REFRESH_THRESHOLD', 2700))  # 2 horas por defecto

# ============================================
# CONFIGURACIÓN DE API
# ============================================

# Límite de intentos de login fallidos antes de bloqueo temporal
MAX_LOGIN_ATTEMPTS = 5

# Tiempo de bloqueo temporal en segundos (después de MAX_LOGIN_ATTEMPTS)
LOGIN_LOCKOUT_SECONDS = 600  # 5 minutos

# Habilitar/deshabilitar logging detallado
API_DEBUG_MODE = os.environ.get('SECOND_MARKET_API_DEBUG', 'False').lower() == 'true'

# ============================================
# CONFIGURACIÓN DE CORS (si es necesario)
# ============================================

# Dominios permitidos para CORS
ALLOWED_ORIGINS = os.environ.get('SECOND_MARKET_ALLOWED_ORIGINS', '*').split(',')

# Métodos HTTP permitidos
ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']

# Headers permitidos
ALLOWED_HEADERS = ['Content-Type', 'Authorization']

# ============================================
# MENSAJES DE RESPUESTA
# ============================================

RESPONSE_MESSAGES = {
    # Autenticación
    'LOGIN_SUCCESS': 'Login exitoso',
    'LOGIN_FAILED': 'Credenciales inválidas',
    'ACCOUNT_DISABLED': 'Tu cuenta está deshabilitada. Contacta al soporte.',
    'REGISTRATION_SUCCESS': 'Usuario registrado exitosamente',
    'REGISTRATION_FAILED': 'Error al registrar usuario',
    
    # Tokens
    'TOKEN_VALID': 'Token válido',
    'TOKEN_INVALID': 'Token inválido',
    'TOKEN_EXPIRED': 'Token expirado',
    'TOKEN_REFRESHED': 'Token refrescado exitosamente',
    'TOKEN_MISSING': 'Token no proporcionado',
    
    # Validaciones
    'MISSING_CREDENTIALS': 'El login y la contraseña son requeridos',
    'MISSING_FIELD': 'Falta un campo requerido',
    'PASSWORD_TOO_SHORT': 'La contraseña debe tener al menos 8 caracteres',
    'LOGIN_EXISTS': 'Ya existe un usuario con este login/email',
    'USER_NOT_FOUND': 'Usuario no encontrado o deshabilitado',
    
    # Errores generales
    'INTERNAL_ERROR': 'Error interno del servidor',
    'UNAUTHORIZED': 'No autorizado',
    'FORBIDDEN': 'Acceso prohibido',
}

# ============================================
# CÓDIGOS DE ERROR
# ============================================

ERROR_CODES = {
    'INVALID_CREDENTIALS': 'ERR_AUTH_001',
    'ACCOUNT_DISABLED': 'ERR_AUTH_002',
    'MISSING_CREDENTIALS': 'ERR_AUTH_003',
    'MISSING_FIELD': 'ERR_VAL_001',
    'PASSWORD_TOO_SHORT': 'ERR_VAL_002',
    'LOGIN_EXISTS': 'ERR_VAL_003',
    'TOKEN_EXPIRED': 'ERR_TOKEN_001',
    'TOKEN_INVALID': 'ERR_TOKEN_002',
    'TOKEN_MISSING': 'ERR_TOKEN_003',
    'USER_NOT_FOUND': 'ERR_USER_001',
    'INTERNAL_ERROR': 'ERR_SYS_001',
    'UNAUTHORIZED': 'ERR_AUTH_004',
}