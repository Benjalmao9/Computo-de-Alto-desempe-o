

frutas = ["manzana", "pera", "uva", "manzana"]

print("=" * 40)
print("   EJERCICIO 3 - LISTA DE FRUTAS")
print("=" * 40)
print(f"Lista original     : {frutas}")

# Contar "manzana"
conteo = frutas.count("manzana")
print(f"Veces 'manzana'    : {conteo}")

# Eliminar elemento
frutas.remove("pera")
print(f"Lista sin 'pera'   : {frutas}")

# Ordenar 
frutas.sort()
print(f"Lista ordenada     : {frutas}")
print("=" * 40)
