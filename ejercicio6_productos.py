

productos = [
    {"nombre": "Laptop",      "precio": 15999, "stock": 10},
    {"nombre": "Teclado",     "precio":   850, "stock": 35},
    {"nombre": "Monitor",     "precio":  5400, "stock": 8},
    {"nombre": "Mouse",       "precio":   320, "stock": 50},
    {"nombre": "Auriculares", "precio":  1200, "stock": 20},
]

print("=" * 50)
print("       EJERCICIO 6 - INVENTARIO")
print("=" * 50)

# Mostrar productos
print(f"\n{'Producto':<14} {'Precio':>10} {'Stock':>7}")
print("-" * 35)
for p in productos:
    print(f"{p['nombre']:<14} ${p['precio']:>9,} {p['stock']:>7}")

#  caro
mas_caro = max(productos, key=lambda p: p["precio"])
print(f"\nProducto más caro   : {mas_caro['nombre']} (${mas_caro['precio']:,})")

# Valor inventario
total_inventario = sum(p["precio"] * p["stock"] for p in productos)
print(f"Valor del inventario: ${total_inventario:,}")
print("=" * 50)
