package com.example.aplicacionmovil.utils

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Base64
import java.io.ByteArrayOutputStream
import java.io.InputStream

object ImageUtils {

    /**
     * Convierte una Uri de imagen a una cadena Base64 comprimida.
     * @param context El contexto de la aplicación.
     * @param uri La Uri de la imagen seleccionada.
     * @param maxWidth El ancho máximo para el reescalado.
     * @param maxHeight El alto máximo para el reescalado.
     * @param quality La calidad de compresión (0-100).
     * @return La cadena Base64 resultante o null si falla.
     */
    fun uriToBase64(
        context: Context,
        uri: Uri,
        maxWidth: Int = 1024,
        maxHeight: Int = 1024,
        quality: Int = 80
    ): String? {
        return try {
            val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
            val originalBitmap = BitmapFactory.decodeStream(inputStream)
            inputStream?.close()

            if (originalBitmap == null) return null

            // Reescalar si es necesario para ahorrar espacio y memoria
            val scaledBitmap = scaleBitmapIfNeeded(originalBitmap, maxWidth, maxHeight)
            
            val outputStream = ByteArrayOutputStream()
            scaledBitmap.compress(Bitmap.CompressFormat.JPEG, quality, outputStream)
            val byteArray = outputStream.toByteArray()
            
            Base64.encodeToString(byteArray, Base64.NO_WRAP)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    private fun scaleBitmapIfNeeded(bitmap: Bitmap, maxWidth: Int, maxHeight: Int): Bitmap {
        val width = bitmap.width
        val height = bitmap.height

        if (width <= maxWidth && height <= maxHeight) return bitmap

        val aspectRatio: Float = width.toFloat() / height.toFloat()
        var newWidth = maxWidth
        var newHeight = (maxWidth / aspectRatio).toInt()

        if (newHeight > maxHeight) {
            newHeight = maxHeight
            newWidth = (maxHeight * aspectRatio).toInt()
        }

        return Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
    }
}
