#Parte 2 (1)
from machine import ADC, Pin, Timer
import utime
import array
import math

# Configuración de la señal esperada
FRECUENCIA_SEÑAL = 200      # Hz
AMPLITUD_PP = 1.2           # Vpp (0.6 V de amplitud)
OFFSET_DC = 1.6             # V
VREF = 3.3                  # Voltaje de referencia ADC

# Configuración de muestreo
FRECUENCIA_MUESTREO = 2000  # Hz (10x la frecuencia de Nyquist)
N_MUESTRAS = 512            # Número de muestras
INTERVALO_US = int(1_000_000 / FRECUENCIA_MUESTREO)  # 500 μs

# Configuración hardware
adc = ADC(Pin(27))          # ADC en pin 26 (GP26) - Canal 0
muestras = array.array('H', [0] * N_MUESTRAS)  # Buffer para muestras
indice_muestra = 0
adquisicion_completada = False

# Callback del temporizador
def sample_callback(timer):
    global indice_muestra, adquisicion_completada
    
    if indice_muestra < N_MUESTRAS:
        muestras[indice_muestra] = adc.read_u16()
        indice_muestra += 1
    else:
        adquisicion_completada = True
        timer.deinit()  # Detener temporizador

# Función para inicializar y ejecutar adquisición
def adquirir_muestras_timer():
    global indice_muestra, adquisicion_completada
    
    # Reiniciar variables
    indice_muestra = 0
    adquisicion_completada = False
    
    # Configurar temporizador hardware
    timer = Timer()
    timer.init(freq=FRECUENCIA_MUESTREO, mode=Timer.PERIODIC, callback=sample_callback)
    
    # Esperar hasta completar adquisición
    start_time = utime.ticks_ms()
    while not adquisicion_completada:
        if utime.ticks_diff(utime.ticks_ms(), start_time) > 5000:  # Timeout 5s
            print("Error: Timeout en adquisición")
            timer.deinit()
            return False
        utime.sleep_ms(10)
    
    return True

# Función para análisis básico de datos
def analizar_muestras(muestras):
    # Convertir a voltaje
    voltajes = [(muestra / 65535) * VREF for muestra in muestras]
    
    # Calcular estadísticas
    voltaje_min = min(voltajes)
    voltaje_max = max(voltajes)
    voltaje_promedio = sum(voltajes) / len(voltajes)
    vpp_medido = voltaje_max - voltaje_min
    
    # Calcular componente AC (remover DC)
    voltajes_ac = [v - voltaje_promedio for v in voltajes]
    amplitud_ac = max(abs(v) for v in voltajes_ac)
    
    print("=== ANÁLISIS DE LA SEÑAL ===")
    print(f"Muestras adquiridas: {len(muestras)}")
    print(f"Voltaje mínimo: {voltaje_min:.3f} V")
    print(f"Voltaje máximo: {voltaje_max:.3f} V")
    print(f"Voltaje promedio (DC): {voltaje_promedio:.3f} V")
    print(f"Vpp medido: {vpp_medido:.3f} V")
    print(f"Amplitud AC: {amplitud_ac:.3f} V")
    print(f"Offset DC esperado: {OFFSET_DC} V")
    print(f"Offset DC medido: {voltaje_promedio:.3f} V")
    print(f"Error DC: {(voltaje_promedio - OFFSET_DC):.3f} V")
    print(f"Vpp esperado: {AMPLITUD_PP} V")
    print(f"Vpp medido: {vpp_medido:.3f} V")
    print(f"Error Vpp: {(vpp_medido - AMPLITUD_PP):.3f} V")
    
    # Guardar datos
    guardar_datos(voltajes)

def guardar_datos(voltajes):
    with open("senal_muestreada.txt", "w") as f:
        f.write("Muestra\tTiempo(s)\tVoltaje(V)\n")
        for i, voltaje in enumerate(voltajes):
            tiempo = i * (1 / FRECUENCIA_MUESTREO)
            f.write(f"{i}\t{tiempo:.6f}\t{voltaje:.6f}\n")
    print(f"Datos guardados en 'senal_muestreada.txt'")

# Programa principal
def main():
    print("Iniciando adquisición de señal con temporizador hardware")
    print(f"Señal esperada: {FRECUENCIA_SEÑAL} Hz, {AMPLITUD_PP} Vpp, {OFFSET_DC} V DC")
    print(f"Frecuencia de muestreo: {FRECUENCIA_MUESTREO} Hz")
    print(f"Número de muestras: {N_MUESTRAS}")
    print(f"Duración: {N_MUESTRAS/FRECUENCIA_MUESTREO:.3f} segundos")
    
    # Calibrar ADC (opcional)
    utime.sleep_ms(100)  # Estabilizar ADC
    
    # Adquirir muestras
    if adquirir_muestras_timer():
        print("Adquisición completada exitosamente")
        analizar_muestras(muestras)
    else:
        print("Error en la adquisición")

if __name__ == "__main__":
    main()