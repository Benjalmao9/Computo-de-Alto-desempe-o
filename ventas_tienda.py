import csv
import random
from datetime import date, timedelta

start_date = date(2024, 1, 1)
end_date   = date(2025, 12, 31)
date_range = (end_date - start_date).days

catalog = {
    "Electrónica": [
        ("Laptop",            8000, 25000),
        ("Mouse",              150,   500),
        ("Teclado",            200,   800),
        ("Auriculares",        300,  2000),
        ("Monitor",           2500,  8000),
        ("USB Flash Drive",     80,   250),
        ("Cargador",           100,   400),
    ],
    "Papelería": [
        ("Cuaderno",    30, 120),
        ("Bolígrafo",   10,  50),
        ("Grapadora",   80, 200),
        ("Marcadores",  40, 150),
        ("Folder",      20,  60),
        ("Tijeras",     25,  80),
    ],
    "Ropa": [
        ("Camiseta",   150, 400),
        ("Pantalón",   300, 800),
        ("Sudadera",   250, 600),
        ("Calcetines",  30, 100),
        ("Gorra",       80, 250),
    ],
    "Alimentos": [
        ("Café",      80, 250),
        ("Galletas",  25,  80),
        ("Chocolate", 30, 100),
        ("Agua",      15,  40),
        ("Jugo",      20,  60),
    ],
    "Deportes": [
        ("Pelota de Fútbol",   200,  600),
        ("Guantes de Box",     400, 1200),
        ("Zapatos Deportivos", 800, 2500),
        ("Colchoneta",         300,  900),
    ],
    "Hogar": [
        ("Lámpara",    200, 800),
        ("Almohada",   150, 400),
        ("Toalla",      80, 250),
        ("Detergente",  50, 150),
    ],
    "Juguetes": [
        ("Rompecabezas",      150, 400),
        ("Muñeca",            200, 600),
        ("Carro de Juguete",  180, 500),
        ("Bloques Didácticos",120, 350),
    ],
    "Belleza": [
        ("Shampoo",      80,  200),
        ("Crema Facial", 150, 500),
        ("Perfume",      300, 1500),
        ("Labial",        50, 200),
        ("Esmalte",       30, 120),
    ],
}

clientes = [
    "Ana García",       "Carlos López",     "María Martínez",   "José Rodríguez",  "Laura Hernández",
    "Miguel González",  "Sofía Pérez",      "David Torres",     "Isabel Ramírez",  "Fernando Flores",
    "Valentina Cruz",   "Roberto Reyes",    "Alejandra Morales","Eduardo Jiménez", "Natalia Ruiz",
    "Andrés Vargas",    "Camila Díaz",      "Ricardo Castillo", "Paola Mendoza",   "Jorge Romero",
    "Daniela Herrera",  "Sergio Gutiérrez", "Gabriela Moreno",  "Arturo Navarro",  "Lucía Ramos",
    "Pablo Álvarez",    "Mariana Medina",   "Héctor Soto",      "Carolina Castro", "Óscar Ríos",
    "Renata Suárez",    "Ignacio Miranda",  "Verónica Aguilar", "Ramón Ortega",    "Adriana Molina",
    "Alberto Varela",   "Silvia Fuentes",   "Enrique Guerrero", "Patricia Muñoz",  "Tomás Vega",
    "Fernanda Luna",    "Marco Sánchez",    "Beatriz Rojas",    "Guillermo León",  "Ximena Paredes",
    "Felipe Núñez",     "Mónica Ibáñez",    "Diego Cabrera",    "Sandra Peña",     "Luis Espinoza",
    "Rebeca Campos",    "Julio Cortez",     "Elena Delgado",    "Víctor Salinas",  "Alicia Ponce",
    "Sebastián Fuentes","Cecilia Trujillo", "Juan Cervantes",   "Rosa Ávila",      "Manuel Bravo",
]

sucursales = {
    "Ciudad de México": ["Sucursal Norte", "Sucursal Centro", "Sucursal Sur"],
    "Guadalajara":      ["Sucursal Norte", "Sucursal Centro", "Sucursal Sur"],
    "Monterrey":        ["Sucursal Norte", "Sucursal Centro", "Sucursal Sur"],
    "Puebla":           ["Sucursal Norte", "Sucursal Centro"],
    "Tijuana":          ["Sucursal Norte", "Sucursal Centro"],
    "Mérida":           ["Sucursal Norte", "Sucursal Centro"],
    "León":             ["Sucursal Norte", "Sucursal Centro"],
}

metodos_pago = ["Efectivo", "Tarjeta de Crédito", "Tarjeta de Débito", "Transferencia"]

cities    = list(sucursales.keys())
categories = list(catalog.keys())

with open("ventas.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "id_venta", "fecha", "producto", "categoria",
        "precio", "cantidad", "cliente",
        "ciudad", "sucursal", "metodo_pago",
    ])

    for i in range(1, 5001):
        fecha    = start_date + timedelta(days=random.randint(0, date_range))
        categoria = random.choice(categories)
        producto, precio_min, precio_max = random.choice(catalog[categoria])
        precio   = round(random.uniform(precio_min, precio_max), 2)
        cantidad = random.randint(1, 20)
        cliente  = random.choice(clientes)
        ciudad   = random.choice(cities)
        sucursal = random.choice(sucursales[ciudad])
        metodo   = random.choice(metodos_pago)
        writer.writerow([i, fecha, producto, categoria, precio, cantidad,
                         cliente, ciudad, sucursal, metodo])

print("ventas.csv generado con 5000 registros.")
