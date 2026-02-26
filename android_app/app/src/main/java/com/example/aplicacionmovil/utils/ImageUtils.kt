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
            val contentResolver = context.contentResolver
            
            // 1. Obtener dimensiones originales sin cargar el bitmap completo
            val options = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            contentResolver.openInputStream(uri)?.use { inputStream ->
                BitmapFactory.decodeStream(inputStream, null, options)
            }

            // 2. Calcular inSampleSize para decodear una versión ya reducida
            options.inSampleSize = calculateInSampleSize(options, maxWidth, maxHeight)
            options.inJustDecodeBounds = false
            
            // 3. Decodear el bitmap con el tamaño reducido
            val sampledBitmap = contentResolver.openInputStream(uri)?.use { inputStream ->
                BitmapFactory.decodeStream(inputStream, null, options)
            } ?: return null

            // 4. Reescalar exactamente si el sampledBitmap sigue siendo mayor que maxWidth/maxHeight
            val finalBitmap = scaleBitmapIfNeeded(sampledBitmap, maxWidth, maxHeight)
            
            // 5. Comprimir y convertir a Base64
            val outputStream = ByteArrayOutputStream()
            finalBitmap.compress(Bitmap.CompressFormat.JPEG, quality, outputStream)
            val byteArray = outputStream.toByteArray()
            
            // Liberar memoria si el bitmap fue una copia
            if (finalBitmap != sampledBitmap) {
                finalBitmap.recycle()
            }
            sampledBitmap.recycle()
            
            Base64.encodeToString(byteArray, Base64.NO_WRAP)
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    private fun calculateInSampleSize(options: BitmapFactory.Options, reqWidth: Int, reqHeight: Int): Int {
        val (height: Int, width: Int) = options.outHeight to options.outWidth
        var inSampleSize = 1

        if (height > reqHeight || width > reqWidth) {
            val halfHeight: Int = height / 2
            val halfWidth: Int = width / 2

            while (halfHeight / inSampleSize >= reqHeight && halfWidth / inSampleSize >= reqWidth) {
                inSampleSize *= 2
            }
        }
        return inSampleSize
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
