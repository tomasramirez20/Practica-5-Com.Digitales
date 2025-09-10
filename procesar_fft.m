function procesar_fft()
    % Cargar datos de la FFT
    fft = readtable('fft.txt');
    frecuencia = fft.Frecuencia_Hz_;
    magnitud = fft.Magnitud_V_;
    
    % Encontrar pico fundamental y armónicos
    [max_mag, idx_max] = max(magnitud(2:end)); % Ignorar DC
    idx_max = idx_max + 1;
    freq_fundamental = frecuencia(idx_max);
    
    % Encontrar armónicos significativos
    umbral_armonicos = max_mag * 0.01; % 1% del fundamental
    indices_armonicos = find(magnitud > umbral_armonicos & frecuencia > 1);
    indices_armonicos = indices_armonicos(indices_armonicos ~= idx_max);
    
    % Calcular THD (Distorsión Armónica Total)
    potencia_fundamental = max_mag^2;
    potencia_armonicos = sum(magnitud(indices_armonicos).^2);
    thd = sqrt(potencia_armonicos / potencia_fundamental) * 100;
    
    % Calcular SNR
    ruido_total = sum(magnitud.^2) - potencia_fundamental;
    snr = 10 * log10(potencia_fundamental / ruido_total);
    
    % Graficar espectro
    figure('Name', 'Análisis Espectral', 'Position', [100 100 900 700]);
    
    % Espectro completo
    subplot(2,1,1);
    semilogy(frecuencia, magnitud, 'b-', 'LineWidth', 1.5);
    hold on;
    plot(frecuencia(idx_max), max_mag, 'ro', 'MarkerSize', 10, 'LineWidth', 2);
    plot(frecuencia(indices_armonicos), magnitud(indices_armonicos), 'mx', 'MarkerSize', 8, 'LineWidth', 2);
    grid on;
    xlabel('Frecuencia (Hz)');
    ylabel('Magnitud (V)');
    title('Espectro de Frecuencia (Escala Logarítmica)');
    legend('Espectro', 'Fundamental', 'Armónicos', 'Location', 'northeast');
    
    % Zoom alrededor del fundamental
    subplot(2,1,2);
    rango_zoom = 100; % ±100 Hz alrededor del fundamental
    idx_zoom = find(frecuencia >= freq_fundamental - rango_zoom & frecuencia <= freq_fundamental + rango_zoom);
    plot(frecuencia(idx_zoom), magnitud(idx_zoom), 'b-', 'LineWidth', 1.5);
    hold on;
    plot(freq_fundamental, max_mag, 'ro', 'MarkerSize', 10, 'LineWidth', 2);
    grid on;
    xlabel('Frecuencia (Hz)');
    ylabel('Magnitud (V)');
    title(sprintf('Zoom alrededor de %.1f Hz', freq_fundamental));
    
    % Mostrar resultados
    fprintf('=== ANÁLISIS ESPECTRAL ===\n');
    fprintf('Frecuencia fundamental: %.2f Hz\n', freq_fundamental);
    fprintf('Amplitud fundamental: %.4f V\n', max_mag);
    fprintf('THD: %.2f%%\n', thd);
    fprintf('SNR: %.2f dB\n', snr);
    fprintf('Número de armónicos significativos: %d\n', length(indices_armonicos));
    
    % Mostrar armónicos detectados
    if ~isempty(indices_armonicos)
        fprintf('\nArmónicos detectados:\n');
        for i = 1:length(indices_armonicos)
            idx = indices_armonicos(i);
            fprintf('  %.1f Hz: %.4f V (%.1f%% del fundamental)\n', ...
                frecuencia(idx), magnitud(idx), ...
                magnitud(idx)/max_mag*100);
        end
    end
    
    % Guardar figura
    saveas(gcf, 'analisis_espectral.png');
end