package com.example.aplicacionmovil.domain.models

import com.google.gson.annotations.SerializedName

data class Purchase(
    val id: Int,
    @SerializedName("id_compra")
    val idCompra: String,
    val precio: Double,
    val estado: String, // "pendiente", "confirmado", "enviado", "recibido", "cancelado"
    @SerializedName("fecha_hora")
    val fechaHora: String? = null,
    val articulo: PurchaseArticle,
    val vendedor: PurchaseUser
)

data class Sale(
    val id: Int,
    @SerializedName("id_compra")
    val idCompra: String,
    val precio: Double,
    val estado: String,
    @SerializedName("fecha_hora")
    val fechaHora: String? = null,
    val articulo: PurchaseArticle,
    val comprador: PurchaseUser
)

data class PurchaseArticle(
    val id: Int,
    val nombre: String,
    val codigo: String
)

data class PurchaseUser(
    val id: Int,
    val nombre: String
)