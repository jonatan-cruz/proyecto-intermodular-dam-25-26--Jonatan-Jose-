# Documentación de la API - Second Market

Esta API permite el funcionamiento de una aplicación móvil de compra-venta integrada con Odoo. Cumple con los requisitos de seguridad (JWT) y gestión de entidades.

## 1. Seguridad y Autenticación

- **Mecanismo**: Autenticación basada en JSON Web Token (JWT).
- **Librería**: `PyJWT`.
- **Cabecera**: `Authorization: Bearer <token>`.
- **Endpoints protegidos**: Todos excepto Registro, Login y Consulta de artículos/categorías.

## 2. Entidades Gestionadas

| Entidad | Descripción | Acciones Disponibles |
| :--- | :--- | :--- |
| **Usuarios** | Gestión de perfiles y acceso | Registro, Login, Ver Perfil, Editar Perfil, Listar artículos de usuario. |
| **Artículos** | Productos en venta | Listar, Ver detalle, Crear (con imágenes), Editar, Publicar, Eliminar. |
| **Categorías** | Clasificación de productos | Listar categorías y sus artículos, Listar etiquetas. |
| **Compras** | Transacciones comerciales | Crear compra (reserva), Confirmar pago, Cancelar, Listar compras/ventas. |
| **Comentarios** | Social / Dudas sobre productos | Crear comentario, Listar comentarios recibidos, Eliminar. |
| **Valoraciones** | Reputación de usuarios | Crear valoración (1-5 estrellas), Listar valoraciones de usuario. |
| **Chats** | Comunicación directa | Crear chat, Enviar mensaje, Listar chats, Ver historial. |
| **Denuncias** | Moderación de contenidos | Crear denuncia de artículo o comentario. |

## 3. Acciones Funcionales Clave

- **Registro y Perfil**: Endpoints `/api/v1/auth/register` y `/api/v1/users/profile`.
- **Compra-Venta**: Al crear una compra (`/api/v1/purchases`), el artículo pasa a `reservado`. Al confirmar el vendedor, pasa a `vendido`.
- **Notificaciones**: 
    - El propietario recibe un mensaje en Odoo cuando alguien comenta su artículo.
    - El vendedor y comprador reciben notificaciones al iniciar una transacción.
- **Imágenes**: Se envían en Base64 en el endpoint `POST /api/v1/articles`.
- **Moderación**: Las denuncias crean registros en el modelo `second_market.report`, visibles en el backend de Odoo con sistema de prioridades.

## 4. Evidencias de Funcionamiento

### A. Autenticación Exitosa (Login)
```bash
curl -X POST http://localhost:8069/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"login": "usuario@test.com", "password": "password123"}'
```
*Respuesta*: Token JWT y datos básicos del usuario.

### B. Creación de Artículo (Protegido)
```bash
curl -X POST http://localhost:8069/api/v1/articles \
     -H "Authorization: Bearer <token_aqui>" \
     -H "Content-Type: application/json" \
     -d '{
       "nombre": "iPhone 13 Pro",
       "descripcion": "Como nuevo, 128GB",
       "precio": 650.0,
       "estado_producto": "bueno",
       "localidad": "Madrid",
       "categoria_id": 1,
       "imagenes": [{"image": "base64_data...", "name": "iphone.jpg"}]
     }'
```

### C. Error de Autorización (Sin Token)
```bash
curl -X GET http://localhost:8069/api/v1/users/profile
```
*Respuesta*: `401 Unauthorized` con mensaje "No autenticado".
