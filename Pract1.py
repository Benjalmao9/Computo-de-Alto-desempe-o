datos = [5, 10, 15, 20]
print("Números mayores a 10:")
for num in datos:
    if num > 10:
        print(num)
def promedio(lista):
    if not lista:
        return 0
    return sum(lista) / len(lista)
promedio = promedio(datos)
print(f"\nEl promedio es: {promedio}")
