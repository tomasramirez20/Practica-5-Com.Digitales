function procesar_muestras_txt()
    % Cargar datos del archivo
    muestras = readtable('muestras.txt');
    tiempo = muestras.Tiempo_s_;
    voltaje = muestras.Voltaje_V_;
    
    % Calcular estadísticas básicas
    fs_real = 1 / mean(diff(tiempo));
    offset_dc = mean(voltaje);
    voltaje_ac = voltaje - offset_dc;
    vpp = max(voltaje) - min(voltaje);
    
    % Graficar señal en tiempo
    figure('Name', 'Señal en Dominio Temporal', 'Position', [100 100 800 600]);
    subplot(2,1,1);
    plot(tiempo, voltaje, 'b-', 'LineWidth', 1.5);
    grid on;
    xlabel('Tiempo (s)');
    ylabel('Voltaje (V)');
    title('Señal Original con DC');
    legend(sprintf('DC: %.3f V', offset_dc));
    
    subplot(2,1,2);
    plot(tiempo, voltaje_ac, 'r-', 'LineWidth', 1.5);
    grid on;
    xlabel('Tiempo (s)');
    ylabel('Voltaje (V)');
    title('Señal sin Componente DC');
    
    % Mostrar resultados en consola
    fprintf('=== ANÁLISIS DE MUESTRAS ===\n');
    fprintf('Muestras totales: %d\n', length(tiempo));
    fprintf('Frecuencia de muestreo real: %.2f Hz\n', fs_real);
    fprintf('Offset DC: %.3f V\n', offset_dc);
    fprintf('Voltaje pico-pico: %.3f V\n', vpp);
    fprintf('Duración total: %.3f s\n', tiempo(end));
    
    % Guardar figura
    saveas(gcf, 'analisis_temporal.png');
end