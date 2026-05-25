import pymongo 
from pymongo import MongoClient

cliente = MongoClient("mongodb://localhost:27017")
bd = cliente["ecommerce_db"]
usuarios = bd["usuarios"]
productos = bd["productos"]
ordenes = bd["ordenes"]
resenas = bd["resenas"]
pagos = bd["pagos"]

# ── Insertar nueva reseña ──────────────────────────────────────
nueva_resena = {
    "orden_ref": "ORD-001",
    "calificacion": 5,
    "comentario": "Producto excelente, muy satisfecho con la compra.",
    "fecha_resena": "2025-01-27T00:02:21.575+00:00",
    "usuario": {
        "nombre": "Juan"
    }
}
resultado_resena = resenas.insert_one(nueva_resena)
print("Reseña insertada con id:", resultado_resena.inserted_id)

# ── Actualizar stock de un producto ───────────────────────────
# Reducir en 1 el stock del producto "GPU Jabra 1"
resultado_stock = productos.update_one(
    { "nombre": "GPU Jabra 1" },
    { "$inc": { "stock": +10} }
)
print("Documentos modificados:", resultado_stock.modified_count)