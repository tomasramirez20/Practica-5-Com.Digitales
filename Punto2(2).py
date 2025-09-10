#Parte 2 (2)
from machine import ADC, Pin, Timer
import utime
import array
import math
import gc

# Configuración de la señal esperada
FRECUENCIA_SEÑAL = 200      # Hz
AMPLITUD_PP = 1.2           # Vpp (0.6 V de amplitud)
OFFSET_DC = 1.6             # V
VREF = 3.3                  # Voltaje de referencia ADC

# Configuración de muestreo
FRECUENCIA_MUESTREO = 2000  # Hz
N_MUESTRAS = 512            # Número de muestras
INTERVALO_IDEAL_US = int(1_000_000 / FRECUENCIA_MUESTREO)  # 500 μs

# Configuración hardware
adc = ADC(Pin(27))
muestras = array.array('H', [0] * N_MUESTRAS)
tiempos_real_us = array.array('L', [0] * N_MUESTRAS)  # Tiempos reales de muestreo
indice_muestra = 0
adquisicion_completada = False

# Variables para medición de jitter
jitter_accumulator = 0
jitter_max = 0
jitter_min = 0

def sample_callback(timer):
    global indice_muestra, adquisicion_completada, jitter_accumulator, jitter_max, jitter_min
    
    if indice_muestra < N_MUESTRAS:
        tiempo_actual = utime.ticks_us()
        
        # Guardar tiempo real de muestreo
        tiempos_real_us[indice_muestra] = tiempo_actual
        
        # Leer ADC
        muestras[indice_muestra] = adc.read_u16()
        
        # Calcular jitter después de la primera muestra
        if indice_muestra > 0:
            intervalo_real = utime.ticks_diff(tiempo_actual, tiempos_real_us[indice_muestra - 1])
            jitter = abs(intervalo_real - INTERVALO_IDEAL_US)
            
            jitter_accumulator += jitter
            jitter_max = max(jitter_max, jitter)
            if indice_muestra == 1:
                jitter_min = jitter
            else:
                jitter_min = min(jitter_min, jitter)
        
        indice_muestra += 1
    else:
        adquisicion_completada = True
        timer.deinit()

def adquirir_muestras_con_jitter():
    global indice_muestra, adquisicion_completada, jitter_accumulator, jitter_max, jitter_min
    
    # Reiniciar variables
    indice_muestra = 0
    adquisicion_completada = False
    jitter_accumulator = 0
    jitter_max = 0
    jitter_min = 0
    
    # Forzar garbage collection para minimizar interrupciones
    gc.collect()
    
    # Configurar temporizador
    timer = Timer()
    timer.init(freq=FRECUENCIA_MUESTREO, mode=Timer.PERIODIC, callback=sample_callback)
    
    # Esperar completación
    start_time = utime.ticks_ms()
    while not adquisicion_completada:
        if utime.ticks_diff(utime.ticks_ms(), start_time) > 5000:
            timer.deinit()
            return False
        utime.sleep_ms(1)
    
    return True

def calcular_metricas_jitter():
    if indice_muestra < 2:
        return 0, 0, 0, 0, 0
    
    # Calcular intervalos reales
    intervalos_real_us = []
    for i in range(1, indice_muestra):
        intervalo = utime.ticks_diff(tiempos_real_us[i], tiempos_real_us[i-1])
        intervalos_real_us.append(intervalo)
    
    # Métricas de jitter
    jitter_promedio = jitter_accumulator / (indice_muestra - 1)
    jitter_rms = math.sqrt(sum((x - INTERVALO_IDEAL_US)**2 for x in intervalos_real_us) / len(intervalos_real_us))
    
    return jitter_promedio, jitter_rms, jitter_max, jitter_min, intervalos_real_us

def analizar_muestras_completo():
    # Convertir a voltaje
    voltajes = [(muestra / 65535) * VREF for muestra in muestras[:indice_muestra]]
    
    # Calcular métricas de jitter
    jitter_prom, jitter_rms, jitter_max, jitter_min, intervalos = calcular_metricas_jitter()
    
    # Calcular estadísticas de señal
    voltaje_min = min(voltajes)
    voltaje_max = max(voltajes)
    voltaje_promedio = sum(voltajes) / len(voltajes)
    vpp_medido = voltaje_max - voltaje_min
    
    # Análisis espectral básico (DFT para frecuencia fundamental)
    señal_ac = [v - voltaje_promedio for v in voltajes]
    frecuencia_medida = estimar_frecuencia(señal_ac, intervalos)
    
    # Calcular error de frecuencia
    error_frecuencia = abs(frecuencia_medida - FRECUENCIA_SEÑAL)
    
    # Generar reporte
    generar_reporte(voltajes, jitter_prom, jitter_rms, jitter_max, jitter_min, 
                   frecuencia_medida, error_frecuencia)

def estimar_frecuencia(señal_ac, intervalos):
    # Estimación simple de frecuencia mediante cruces por cero
    cruces_cero = 0
    for i in range(1, len(señal_ac)):
        if señal_ac[i-1] * señal_ac[i] < 0:
            cruces_cero += 1
    
    if cruces_cero < 2:
        return 0
    
    # Calcular período promedio
    tiempo_total = sum(intervalos) / 1_000_000  # Convertir a segundos
    periodo_medio = (2 * tiempo_total) / cruces_cero
    return 1 / periodo_medio

def generar_reporte(voltajes, jitter_prom, jitter_rms, jitter_max, jitter_min,
                   frecuencia_medida, error_frecuencia):
    
    print("\n" + "="*60)
    print("REPORTE DE ANÁLISIS DE JITTER Y CALIDAD DE MUESTREO")
    print("="*60)
    
    print(f"\n● CONFIGURACIÓN DE MUESTREO:")
    print(f"  Frecuencia deseada: {FRECUENCIA_MUESTREO} Hz")
    print(f"  Intervalo ideal: {INTERVALO_IDEAL_US} μs")
    print(f"  Muestras adquiridas: {indice_muestra}")
    
    print(f"\n● MÉTRICAS DE JITTER TEMPORAL:")
    print(f"  Jitter promedio: {jitter_prom:.2f} μs")
    print(f"  Jitter RMS: {jitter_rms:.2f} μs")
    print(f"  Jitter máximo: {jitter_max} μs")
    print(f"  Jitter mínimo: {jitter_min} μs")
    print(f"  Error temporal relativo: {(jitter_rms/INTERVALO_IDEAL_US*100):.2f}%")
    
    print(f"\n● CALIDAD DE LA SEÑAL RECONSTRUIDA:")
    print(f"  Frecuencia esperada: {FRECUENCIA_SEÑAL} Hz")
    print(f"  Frecuencia medida: {frecuencia_medida:.2f} Hz")
    print(f"  Error de frecuencia: {error_frecuencia:.2f} Hz ({(error_frecuencia/FRECUENCIA_SEÑAL*100):.2f}%)")
    
    # Calcular SNR estimado debido al jitter
    snr_jitter = calcular_snr_teorico(jitter_rms, FRECUENCIA_SEÑAL)
    print(f"\n● IMPACTO EN CALIDAD:")
    print(f"  SNR teórico por jitter: {snr_jitter:.2f} dB")
    print(f"  ENOB limitado por jitter: {(snr_jitter - 1.76) / 6.02:.2f} bits")
    
    # Guardar datos detallados
    guardar_datos_completos(voltajes, jitter_prom, jitter_rms)

def calcular_snr_teorico(jitter_rms, frecuencia):
    # SNR debido a jitter = 20*log10(1/(2*π*f*jitter))
    if jitter_rms == 0:
        return float('inf')
    jitter_sec = jitter_rms * 1e-6  # Convertir a segundos
    snr = 20 * math.log10(1 / (2 * math.pi * frecuencia * jitter_sec))
    return snr

def guardar_datos_completos(voltajes, jitter_prom, jitter_rms):
    with open("reporte_jitter.txt", "w") as f:
        f.write("Análisis de Jitter en Muestreo de Señal\n")
        f.write("="*50 + "\n\n")
        f.write(f"Frecuencia de muestreo objetivo: {FRECUENCIA_MUESTREO} Hz\n")
        f.write(f"Intervalo ideal: {INTERVALO_IDEAL_US} μs\n")
        f.write(f"Jitter promedio: {jitter_prom:.2f} μs\n")
        f.write(f"Jitter RMS: {jitter_rms:.2f} μs\n")
        f.write(f"Error temporal: {(jitter_rms/INTERVALO_IDEAL_US*100):.2f}%\n\n")
        
        f.write("Muestra\tTiempo(μs)\tVoltaje(V)\n")
        for i in range(min(100, len(voltajes))):  # Mostrar primeras 100 muestras
            f.write(f"{i}\t{tiempos_real_us[i]}\t{voltajes[i]:.6f}\n")

def main():
    print("Iniciando medición de jitter en proceso de muestreo")
    print("Adquiriendo datos con temporizador hardware...")
    
    if adquirir_muestras_con_jitter():
        analizar_muestras_completo()
        print("\n● Análisis completado. Ver 'reporte_jitter.txt' para detalles.")
    else:
        print("Error en la adquisición de datos")

if __name__ == "__main__":
    main()