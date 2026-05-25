import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import binom

# ==========================================
# 1. CONFIGURACIÓN DEL PROBLEMA
# ==========================================
# Datos de tu screenshot
N = 30
k = 1

# Definimos nuestra distribución objetivo (Posteriori NO normalizada)
# Recuerda: Posteriori = Verosimilitud * Priori
def posteriori_no_normalizada(theta):
    # Si el salto propone un porcentaje imposible (menor a 0 o mayor a 1), la probabilidad es 0
    if theta < 0 or theta > 1:
        return 0.0
    
    # Priori Uniforme (Vale 1 en todo el rango, no afecta la multiplicación)
    priori = 1.0 
    
    # Verosimilitud (Binomial)
    verosimilitud = binom.pmf(k, N, theta)
    
    return verosimilitud * priori

# ==========================================
# 2. EL ALGORITMO MCMC (Metropolis-Hastings)
# ==========================================
iteraciones = 10000
trace = np.zeros(iteraciones)

# Paso 1: Punto de inicio aleatorio (empezamos en el 50%)
theta_actual = 0.5 

saltos_aceptados = 0

for i in range(iteraciones):
    # Paso 2: Proponer un salto aleatorio 
    # (Usamos una distribución normal para dar un pasito cerca de donde estamos)
    theta_propuesto = np.random.normal(loc=theta_actual, scale=0.1)
    
    # Paso 3: Calcular qué tan "mejor" es el nuevo punto
    p_actual = posteriori_no_normalizada(theta_actual)
    p_propuesto = posteriori_no_normalizada(theta_propuesto)
    
    # Razón de aceptación (r)
    # Evitamos dividir por cero por seguridad
    if p_actual > 0:
        r = p_propuesto / p_actual
    else:
        r = 1.0

    # Paso 4: ¿Aceptamos o rechazamos?
    # np.random.rand() genera un número entre 0 y 1. 
    # Esto automáticamente acepta si r >= 1, y acepta con probabilidad r si r < 1.
    if np.random.rand() < r:
        theta_actual = theta_propuesto # ¡Salto aceptado! Nos movemos.
        saltos_aceptados += 1
        
    # Paso 5: Guardamos la posición en la cadena (sea la nueva o nos hayamos quedado quietos)
    trace[i] = theta_actual

# ==========================================
# 3. PROCESAMIENTO Y GRÁFICAS
# ==========================================
# Descartamos el "Burn-in" (las primeras 1,000 iteraciones donde andaba perdido)
burn_in = 1000
trace_limpio = trace[burn_in:]

print(f"Tasa de aceptación: {(saltos_aceptados/iteraciones)*100:.1f}%")

# Crear figura con dos subgráficas
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Gráfica 1: El Trace Plot (El recorrido del caminante)
ax1.plot(trace_limpio, color='#11caa0', alpha=0.7, linewidth=0.5)
ax1.set_title('Trace Plot (La Cadena de Markov)')
ax1.set_xlabel('Iteración')
ax1.set_ylabel('Valor de Theta (Tasa de clics)')
ax1.grid(True, alpha=0.3)

# ==========================================
# Gráfica 2: El Histograma (MEJORADO CON ZOOM Y RESULTADO)
# ==========================================
# Guardamos los datos del histograma para encontrar el pico
counts, bins, patches = ax2.hist(trace_limpio, bins=50, density=True, color='#005088', alpha=0.7, edgecolor='white')

# 1. Encontrar el punto exacto más alto del histograma
indice_max = np.argmax(counts)
pico_x = (bins[indice_max] + bins[indice_max+1]) / 2

# 2. Dibujar una línea roja punteada exactamente en ese pico
ax2.axvline(pico_x, color='red', linestyle='dashed', linewidth=2)

# 3. Ponerle un letrero con el número exacto
ax2.text(pico_x + 0.01, max(counts) * 0.9, f'Pico máximo: {pico_x:.3f}\n({(pico_x*100):.1f}%)', 
         color='red', fontweight='bold', fontsize=12)

# 4. Configurar ejes para que se vea claro (Zoom de 0 a 0.20)
ax2.set_title('Posteriori (Histograma de Muestras)')
ax2.set_xlabel('Tasa de Clics Posible (θ)')
ax2.set_ylabel('Densidad')
ax2.set_xlim(0, 0.20)
ax2.set_xticks(np.arange(0, 0.22, 0.02)) # Números cada 0.02
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()