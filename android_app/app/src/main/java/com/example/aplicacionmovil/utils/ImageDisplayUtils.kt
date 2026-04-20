package com.example.aplicacionmovil.utils

/**
 * Utilidad centralizada para asegurar que las imágenes Base64 se muestren correctamente
 */
object ImageDisplayUtils {
    /**
     * Asegura que una cadena base64 tenga el prefijo necesario para ser mostrada por Coil
     */
    fun ensureDisplayableImage(image: String?): String? {
        if (image == null) return null
        if (image.startsWith("http")) return image
        if (image.startsWith("dataImage") || image.startsWith("data/image")) {
             // Ya tiene algún prefijo o está mal formado pero intentamos limpiar
             return image
        }
        if (image.startsWith("data:image")) return image
        
        // Si no tiene prefijo, se lo añadimos
        return "data:image/jpeg;base64,$image"
    }

    /**
     * Devuelve el modelo adecuado para Coil (String si es URL, ByteArray si es Base64).
     */
    fun getProfileImageModel(image: String?): Any? {
        if (image.isNullOrBlank()) return null
        if (image.startsWith("http")) return image
        
        try {
            val base64String = if (image.startsWith("data:image")) {
                image.substringAfter("base64,")
            } else {
                image
            }
            return android.util.Base64.decode(base64String, android.util.Base64.DEFAULT)
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }
    }
}
