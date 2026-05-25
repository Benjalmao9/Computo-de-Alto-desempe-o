datos = [12, 7, 25, 30, 18, 5, 40]

print("Todos los numeros:")
for x in datos:
    print(x)

print("\nmayores a 20:")
for x in datos:
    if x > 20:
        print(x)

menores_10 = sum(1 for num in datos if num < 10)
print(f"\nCantidad de menores a 10: {menores_10}")

suma_total = sum(datos)
print(f"\nSuma total numeros: {suma_total}")
 