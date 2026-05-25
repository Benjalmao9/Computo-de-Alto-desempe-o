import sys
import unicodedata
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")


def normalizar(texto):
    if not isinstance(texto, str):
        return texto
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# ── 1. Lectura y normalización ────────────────────────────────────────────────
df = pd.read_csv("ventas.csv", parse_dates=["fecha"])

columnas_texto = [
    "producto", "categoria", "cliente",
    "ciudad", "sucursal", "metodo_pago", "vendedor", "turno",
]
for col in columnas_texto:
    df[col] = df[col].apply(normalizar)

# ── 2. Validación ─────────────────────────────────────────────────────────────
print("=" * 60)
print("VALIDACIÓN")
print("=" * 60)

nulos = df.isnull().sum()
if nulos.sum() == 0:
    print("Sin valores nulos en ninguna columna.")
else:
    print("Columnas con nulos:")
    print(nulos[nulos > 0].to_string())

tipos_esperados = {
    "id_venta": "int64",
    "fecha":    ("datetime64[ns]", "datetime64[us]"),
    "precio":   "float64",
    "cantidad": "int64",
}
for col, tipo in tipos_esperados.items():
    tipos_validos = tipo if isinstance(tipo, tuple) else (tipo,)
    ok = str(df[col].dtype) in tipos_validos
    estado = "OK" if ok else f"ADVERTENCIA (se esperaba {tipo}, hay {df[col].dtype})"
    print(f"  {col}: {estado}")

# ── 3. Columna total ──────────────────────────────────────────────────────────
df["total"] = (df["precio"] * df["cantidad"]).round(2)

# ── 4. Análisis ───────────────────────────────────────────────────────────────

def titulo(texto):
    print(f"\n{'=' * 60}")
    print(texto)
    print("=" * 60)

# Total de ventas por categoría
titulo("TOTAL DE VENTAS POR CATEGORÍA")
por_categoria = df.groupby("categoria")["total"].sum().sort_values(ascending=False)
for cat, val in por_categoria.items():
    print(f"  {cat:<20} ${val:>12,.2f}")

# Total de ventas por ciudad
titulo("TOTAL DE VENTAS POR CIUDAD")
por_ciudad = df.groupby("ciudad")["total"].sum().sort_values(ascending=False)
for ciudad, val in por_ciudad.items():
    print(f"  {ciudad:<20} ${val:>12,.2f}")

# Sucursal con mayor ingreso
titulo("SUCURSAL CON MAYOR INGRESO")
por_sucursal = (
    df.groupby(["ciudad", "sucursal"])["total"]
    .sum()
    .sort_values(ascending=False)
)
ciudad_top, suc_top = por_sucursal.idxmax()
print(f"  {ciudad_top} — {suc_top}: ${por_sucursal.max():,.2f}")

# Método de pago más usado (transacciones)
titulo("MÉTODO DE PAGO — USO Y TOTAL")
por_metodo = df.groupby("metodo_pago").agg(
    transacciones=("id_venta", "count"),
    ingreso=("total", "sum"),
).sort_values("transacciones", ascending=False)
print(por_metodo.to_string())
mas_usado   = por_metodo["transacciones"].idxmax()
mayor_ingreso = por_metodo["ingreso"].idxmax()
print(f"\n  -> Más usado (transacciones): {mas_usado} ({por_metodo.loc[mas_usado, 'transacciones']})")
print(f"  -> Mayor ingreso total:        {mayor_ingreso} (${por_metodo.loc[mayor_ingreso, 'ingreso']:,.2f})")

# Producto más vendido por cantidad
titulo("PRODUCTO MÁS VENDIDO POR CANTIDAD")
por_producto = df.groupby("producto")["cantidad"].sum().sort_values(ascending=False)
print(f"  -> {por_producto.idxmax()}: {por_producto.max():,} unidades")
print()
print(por_producto.head(10).to_string())

# Cliente con mayor gasto total
titulo("CLIENTE CON MAYOR GASTO TOTAL")
por_cliente = df.groupby("cliente")["total"].sum().sort_values(ascending=False)
print(f"  -> {por_cliente.idxmax()}: ${por_cliente.max():,.2f}")
print()
print(por_cliente.head(10).to_string())

# Vendedor con mayor ingreso generado
titulo("VENDEDOR CON MAYOR INGRESO GENERADO")
por_vendedor = df.groupby("vendedor")["total"].sum().sort_values(ascending=False)
print(f"  -> {por_vendedor.idxmax()}: ${por_vendedor.max():,.2f}")
print()
print(por_vendedor.head(10).to_string())

# Turno con más ventas y mayor ingreso
titulo("VENTAS POR TURNO")
por_turno = df.groupby("turno").agg(
    transacciones=("id_venta", "count"),
    ingreso_total=("total", "sum"),
).sort_values("transacciones", ascending=False)
print(por_turno.to_string())
print(f"\n  -> Turno con más transacciones: {por_turno['transacciones'].idxmax()}")
print(f"  -> Turno con mayor ingreso:     {por_turno['ingreso_total'].idxmax()}")

# Ventas por mes
titulo("VENTAS POR MES")
df["mes"] = df["fecha"].dt.to_period("M")
por_mes = df.groupby("mes")["total"].sum().sort_index()
for mes, val in por_mes.items():
    print(f"  {mes}   ${val:>12,.2f}")

# ── 5. Exportar resúmenes ─────────────────────────────────────────────────────
titulo("EXPORTANDO ARCHIVOS CSV")

resumen_categorias = (
    df.groupby("categoria")
    .agg(transacciones=("id_venta", "count"),
         cantidad_total=("cantidad", "sum"),
         ingreso_total=("total", "sum"))
    .reset_index()
    .sort_values("ingreso_total", ascending=False)
)
resumen_categorias.to_csv("resumen_categorias.csv", index=False, encoding="utf-8")
print("  OK resumen_categorias.csv")

resumen_ciudades = (
    df.groupby("ciudad")
    .agg(transacciones=("id_venta", "count"),
         cantidad_total=("cantidad", "sum"),
         ingreso_total=("total", "sum"))
    .reset_index()
    .sort_values("ingreso_total", ascending=False)
)
resumen_ciudades.to_csv("resumen_ciudades.csv", index=False, encoding="utf-8")
print("  OK resumen_ciudades.csv")

resumen_sucursales = (
    df.groupby(["ciudad", "sucursal"])
    .agg(transacciones=("id_venta", "count"),
         cantidad_total=("cantidad", "sum"),
         ingreso_total=("total", "sum"))
    .reset_index()
    .sort_values("ingreso_total", ascending=False)
)
resumen_sucursales.to_csv("resumen_sucursales.csv", index=False, encoding="utf-8")
print("  OK resumen_sucursales.csv")

resumen_metodos_pago = (
    df.groupby("metodo_pago")
    .agg(transacciones=("id_venta", "count"),
         ingreso_total=("total", "sum"))
    .reset_index()
    .sort_values("ingreso_total", ascending=False)
)
resumen_metodos_pago.to_csv("resumen_metodos_pago.csv", index=False, encoding="utf-8")
print("  OK resumen_metodos_pago.csv")

resumen_vendedores = (
    df.groupby("vendedor")
    .agg(transacciones=("id_venta", "count"),
         cantidad_total=("cantidad", "sum"),
         ingreso_total=("total", "sum"))
    .reset_index()
    .sort_values("ingreso_total", ascending=False)
)
resumen_vendedores.to_csv("resumen_vendedores.csv", index=False, encoding="utf-8")
print("  OK resumen_vendedores.csv")

resumen_turnos = (
    df.groupby("turno")
    .agg(transacciones=("id_venta", "count"),
         cantidad_total=("cantidad", "sum"),
         ingreso_total=("total", "sum"))
    .reset_index()
    .sort_values("ingreso_total", ascending=False)
)
resumen_turnos.to_csv("resumen_turnos.csv", index=False, encoding="utf-8")
print("  OK resumen_turnos.csv")
