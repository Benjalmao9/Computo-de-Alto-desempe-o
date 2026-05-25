import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
from scipy.stats import binom, beta

# 1. Configuración de la Cuadrícula
theta_grid = np.linspace(0, 1, 200)

# Configurar la ventana de la gráfica
fig, ax = plt.subplots(figsize=(10, 7))
plt.subplots_adjust(bottom=0.4, left=0.15) # Hacemos espacio abajo para los sliders

# Colores
col_posterior = '#005088'
col_likelihood = '#228B22'
col_priori = '#A9A9A9'

# Variables iniciales
N_init = 10
k_init = 3
prior_init = 'Uniforme'

# Líneas de las gráficas
line_prior, = ax.plot(theta_grid, np.ones(200)/np.sum(np.ones(200)), label='Priori', color=col_priori, linestyle='--')
line_likelihood, = ax.plot(theta_grid, np.ones(200), label='Verosimilitud', color=col_likelihood)
line_posterior, = ax.plot(theta_grid, np.ones(200), label='Posteriori', color=col_posterior, linewidth=3)
fill_posterior = ax.fill_between(theta_grid, 0, np.ones(200), color=col_posterior, alpha=0.15)

ax.set_title('Actualización Bayesiana', pad=15)
ax.set_xlabel('Tasa de Clics Posible (θ)')
ax.set_ylabel('Densidad de Probabilidad')
ax.set_xlim(0, 1)
ax.set_ylim(0, 0.1) # Se ajustará dinámicamente
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

# ==========================================
# CREAR LOS SLIDERS NATIVOS (MATPLOTLIB)
# ==========================================
ax_N = plt.axes([0.15, 0.25, 0.65, 0.03])
ax_k = plt.axes([0.15, 0.15, 0.65, 0.03])
ax_radio = plt.axes([0.15, 0.02, 0.65, 0.10], facecolor='lightgoldenrodyellow')

slider_N = Slider(ax_N, 'Usuarios (N)', 1, 100, valinit=N_init, valstep=1)
slider_k = Slider(ax_k, 'Clics (k)', 0, N_init, valinit=k_init, valstep=1)
radio_prior = RadioButtons(ax_radio, ('Uniforme', 'Pesimista', 'Optimista'), active=0)

# ==========================================
# FUNCIÓN DE ACTUALIZACIÓN
# ==========================================
def update(val):
    N = int(slider_N.val)
    k = int(slider_k.val)
    tipo = radio_prior.value_selected
    
    # Restringir que k no sea mayor que N
    if k > N:
        k = N
        slider_k.set_val(N)
        
    # Calcular Priori
    if tipo == 'Uniforme':
        a, b = 1, 1
    elif tipo == 'Pesimista':
        a, b = 2, 5
    else: # Optimista
        a, b = 5, 2
        
    p_prior = beta.pdf(theta_grid, a, b)
    p_prior_norm = p_prior / p_prior.sum()
    
    # Calcular Verosimilitud
    likelihood = binom.pmf(k, N, theta_grid)
    likelihood_norm = likelihood / likelihood.sum()
    
    # Calcular Posteriori
    p_posterior_sin_norm = likelihood * p_prior
    p_posterior = p_posterior_sin_norm / p_posterior_sin_norm.sum()
    
    # Actualizar datos en la gráfica
    line_prior.set_ydata(p_prior_norm)
    line_likelihood.set_ydata(likelihood_norm)
    line_posterior.set_ydata(p_posterior)
    
    # Actualizar relleno
    global fill_posterior
    fill_posterior.remove()
    fill_posterior = ax.fill_between(theta_grid, 0, p_posterior, color=col_posterior, alpha=0.15)
    
    # Ajustar el límite Y para que se vea bien
    ax.set_ylim(0, max(p_posterior) * 1.2)
    ax.set_title(f'Actualización Bayesiana: {k} clics de {N} usuarios')
    
    fig.canvas.draw_idle()

# Conectar los controles con la función de actualización
slider_N.on_changed(update)
slider_k.on_changed(update)
radio_prior.on_clicked(update)

# Ejecutar una vez para inicializar
update(None)

# Mostrar la ventana
plt.show()