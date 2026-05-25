import numpy as np

# Generar arreglo aleatorio con 1500 números enteros entre 0 y 1000
arreglo = np.random.randint(0, 1001, size=1500)

print("=" * 60)
print("         ANÁLISIS DE ARREGLO ALEATORIO CON NUMPY")
print("=" * 60)

# Tamaño del arreglo
print(f"\nTamaño del arreglo: {arreglo.size} elementos")

# Total (suma)
total = np.sum(arreglo)
print(f"Total (suma):       {total}")

# Promedio
promedio = np.mean(arreglo)
print(f"Promedio:           {promedio:.2f}")

# Números menores a 300
menores_300 = arreglo[arreglo < 300]
print(f"\n{'=' * 60}")
print(f"Números MENORES a 300 ({len(menores_300)} encontrados):")
print(menores_300)

# Números mayores a 900
mayores_900 = arreglo[arreglo > 900]
print(f"\n{'=' * 60}")
print(f"Números MAYORES a 900 ({len(mayores_900)} encontrados):")
print(mayores_900)

print("=" * 60)
