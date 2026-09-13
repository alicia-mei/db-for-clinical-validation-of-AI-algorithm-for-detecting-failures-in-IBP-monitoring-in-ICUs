import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
import os

def generate_oscillation(t, omega_n, zeta, amplitude, baseline):
    """
    Gera o sinal oscilatório de um sistema subamortecido de segunda ordem.
    
    Parâmetros:
    - t: array de tempo (segundos) após a queda do flush test
    - omega_n: frequência natural (rad/s)
    - zeta: coeficiente de amortecimento (0 < zeta < 1 para subamortecido)
    - amplitude: amplitude da oscilação (mmHg)
    - baseline: pressão basal após a queda (mmHg)
    
    Retorna:
    - sinal oscilatório: array com os valores de pressão
    """
    # Resposta livre subamortecida
    oscillation = (np.exp(-zeta * omega_n * t) * (np.cos(omega_n * np.sqrt(1 - zeta**2) * t) + (zeta / np.sqrt(1 - zeta**2)) * np.sin(omega_n * np.sqrt(1 - zeta**2) * t))) * amplitude
    
    return baseline + oscillation

# tipos de pacientes 
patient_types = {
    'normotensive': {
        'heart_rate_range': (60, 100),
        'pressure_base_range': (80, 90),
        'pressure_amp_range': (20, 40),
        'clip_range': (60, 140),
        'flush_pressure_range': (250, 300)
    },
    'septic': {
        'heart_rate_range': (60, 100),
        'pressure_base_range': (61.8, 96.54),
        'pressure_amp_range': (30, 50),
        'clip_range': (45.34, 142.73),
        'flush_pressure_range': (250, 300)
    },
    'shock': {
        'heart_rate_range': (50, 80),
        'pressure_base_range': (63, 83.5),
        'pressure_amp_range': (10, 36.5),
        'clip_range': (47, 120),
        'flush_pressure_range': (250, 300)
    },
    'onNorepinephrine': {
        'heart_rate_range': (50, 80),
        'pressure_base_range': (61.6, 83.8),
        'pressure_amp_range': (10, 36.5),
        'clip_range': (47.1, 128.5),
        'flush_pressure_range': (250, 300)
    }
}

def generate_arterial_pressure_signal(duration_hours=1, fs=250, save_csv=False, filename='arterial_pressure_signal.csv', num_flush_tests=5, num_fake_flush_tests=3, patient_type='normotensive', omega_n=20, zeta=0.1):
    duration_sec = duration_hours * 3600  # converter horas para segundos
    num_samples = duration_sec * fs
    time = np.linspace(0, duration_sec, num_samples)  # vetor de tempo (início, fim, num_amostras)
    
    # Get patient type configuration
    config = patient_types[patient_type]
    
    # Gerar sinal
    heart_rate = np.random.uniform(config['heart_rate_range'][0], config['heart_rate_range'][1])  # batimentos por minuto
    heart_rate_hz = heart_rate / 60  # converter para Hz
    pressure = np.random.uniform(config['pressure_base_range'][0], config['pressure_base_range'][1]) + np.random.uniform(config['pressure_amp_range'][0], config['pressure_amp_range'][1]) * np.sin(2 * np.pi * heart_rate_hz * time)
    
    # Limitar valores de pressão
    pressure = np.clip(pressure, config['clip_range'][0], config['clip_range'][1])
    
    # Calcular estatísticas
    pressure_max = np.max(pressure)
    pressure_min = np.min(pressure)
    pressure_mean = np.mean(pressure)
    
    # Inicializar listas de tempos
    real_flush_times = []
    fake_flush_times = []
    
    # Adicionar flush tests randômicos
    if num_flush_tests > 0:
        pressure, real_flush_times, real_flush_omega_n, real_flush_zeta = add_flush_tests(pressure, time, fs, num_flush_tests, patient_type, omega_n, zeta)
    
    if num_fake_flush_tests > 0:
        pressure, fake_flush_times, fake_flush_omega_n, fake_flush_zeta = add_fake_flush(pressure, time, fs, num_fake_flush_tests, real_flush_times, patient_type, omega_n, zeta)
    
    # Salvar o CSV se necessário
    if save_csv:
        df = pd.DataFrame({'time': time, 'pressure': pressure})
        df.to_csv(filename, index=False)
    
    return time, pressure, pressure_max, pressure_min, pressure_mean, heart_rate, real_flush_times, fake_flush_times, real_flush_omega_n, real_flush_zeta, fake_flush_omega_n, fake_flush_zeta

def add_flush_tests(pressure, time, fs, num_tests, patient_type, omega_n=15, zeta=0.2):
    """
    Parâmetros:
    - pressure: array com valores de pressão
    - time: array com valores de tempo
    - fs: frequência de amostragem
    - num_tests: número de flush tests a adicionar
    - patient_type: tipo de paciente para configuração
    
    Retorna:
    - pressure_modified: sinal de pressão com flush tests adicionados
    - flush_times_fall: lista com os tempos de INÍCIO DA DESCIDA dos flush tests
    """
    duration_sec = time[-1]
    pressure_modified = pressure.copy()
    
    config = patient_types[patient_type]
    flush_pressure_min, flush_pressure_max = config['flush_pressure_range']
    flush_duration_min = 2.0
    flush_duration_max = 15.0
    min_interval = 3
    
    flush_times = []
    for i in range(num_tests):
        valid_time = False
        attempts = 0
        while not valid_time and attempts < 100: 
            candidate_time = np.random.uniform(30, duration_sec - 30)
            if all(abs(candidate_time - t) > min_interval for t in flush_times):
                flush_times.append(candidate_time) 
                valid_time = True
            attempts += 1
    
    flush_times.sort()
    
    # Lista para armazenar os tempos de início da descida
    flush_times_fall = []

    #Lista para armazenar parâmetros das oscilações
    omega_n_list = []
    zeta_list = []
    
    # Adicionar cada flush test
    for flush_time in flush_times:
        flush_duration = np.random.uniform(flush_duration_min, flush_duration_max)
        flush_pressure = np.random.uniform(flush_pressure_min, flush_pressure_max)
        
        start_idx = int(flush_time * fs)
        end_idx = int((flush_time + flush_duration) * fs)
        
        start_idx = max(0, min(start_idx, len(pressure_modified) - 1)) 
        end_idx = max(0, min(end_idx, len(pressure_modified) - 1))
        
        rise_samples = int(0.1 * fs)
        fall_samples = int(0.2 * fs)
        
        # Subida
        if start_idx + rise_samples < len(pressure_modified):
            pressure_modified[start_idx:start_idx + rise_samples] = np.linspace(
                pressure_modified[start_idx],
                flush_pressure,
                rise_samples
            )
        
        # Platô
        plateau_start = start_idx + rise_samples
        plateau_end = end_idx - fall_samples
        if plateau_start < plateau_end and plateau_end < len(pressure_modified):
            pressure_modified[plateau_start:plateau_end] = flush_pressure
        
        # Descida - guardar o tempo de início da descida
        fall_start_time = (end_idx - fall_samples) / fs  # converter índice para tempo
        flush_times_fall.append(round(fall_start_time, 2))
        omega_n_list.append(omega_n)
        zeta_list.append(zeta)
        
        if end_idx < len(pressure_modified) and end_idx - fall_samples >= 0:
            pressure_modified[end_idx - fall_samples:end_idx] = np.linspace(
                flush_pressure,
                pressure_modified[min(end_idx, len(pressure_modified) - 1)],
                fall_samples
            )
        
        # Adicionar oscilação após a descida
        oscillation_duration = 0.5  # segundos
        osc_samples = int(oscillation_duration * fs)
        if end_idx + osc_samples < len(pressure_modified):  
            t_osc = np.linspace(0, oscillation_duration, osc_samples)
            normal_pressure = pressure_modified[min(end_idx, len(pressure_modified) - 1)]
            osc_amplitude = (flush_pressure - pressure.min())/2
            osc_signal = generate_oscillation(t_osc, omega_n, zeta, osc_amplitude, normal_pressure)
            pressure_modified[end_idx:end_idx + osc_samples] = osc_signal
    
    return pressure_modified, flush_times_fall, omega_n_list, zeta_list


def add_fake_flush(pressure, time, fs, num_tests, real_flush_times=None, patient_type='normotensive', omega_n=15, zeta=0.2):
    """
    Parâmetros:
    - pressure: array com valores de pressão
    - time: array com valores de tempo
    - fs: frequência de amostragem
    - num_tests: número de fake flush tests a adicionar
    - real_flush_times: lista com os tempos dos flush tests reais (opcional)
    - patient_type: tipo de paciente para configuração
    
    Retorna:
    - pressure_modified: sinal de pressão com fake flush tests adicionados
    - fake_flush_times_fall: lista com os tempos de INÍCIO DA DESCIDA dos fake flush tests
    """
    duration_sec = time[-1]
    pressure_modified = pressure.copy()
    
    config = patient_types[patient_type]
    flush_pressure_min, flush_pressure_max = config['flush_pressure_range']
    flush_duration_min = 2.0
    flush_duration_max = 30.0 #ajustar com base na análise dos sinais reais
    min_interval = 3

    if real_flush_times is None:
        real_flush_times = []
    
    fake_flush_times = []

    for i in range(num_tests):
        valid_time = False
        attempts = 0
        while not valid_time and attempts < 100: 
            candidate_time = np.random.uniform(30, duration_sec - 30)
            valid_fake = all(abs(candidate_time - t) > min_interval for t in fake_flush_times)
            valid_real = all(abs(candidate_time - t) > min_interval for t in real_flush_times)

            if valid_fake and valid_real:
                fake_flush_times.append(candidate_time) 
                valid_time = True
            attempts += 1
    
    fake_flush_times.sort()
    
    # Lista para armazenar os tempos de início da descida
    fake_flush_times_fall = []

    omega_n_list = []
    zeta_list = []
    
    # Adicionar cada fake flush test
    for flush_time in fake_flush_times:
        flush_duration = np.random.uniform(flush_duration_min, flush_duration_max)
        flush_pressure = np.random.uniform(flush_pressure_min, flush_pressure_max)
        
        start_idx = int(flush_time * fs)
        end_idx = int((flush_time + flush_duration) * fs)
        
        start_idx = max(0, min(start_idx, len(pressure_modified) - 1)) 
        end_idx = max(0, min(end_idx, len(pressure_modified) - 1))
        
        rise_samples = int(flush_duration * fs)
        
        # Subida logarítmica
        if start_idx + rise_samples < len(pressure_modified):
            x = np.linspace(0.01, 1, rise_samples)
            log_curve = np.log10(x * 99 + 1)
            log_curve = log_curve / np.max(log_curve)
            
            pressure_modified[start_idx:start_idx + rise_samples] = (
                pressure_modified[start_idx] + 
                log_curve * (flush_pressure - pressure_modified[start_idx])
            )
        
        # Descida em degrau - guardar o tempo de início da descida
        fall_idx = start_idx + rise_samples
        fall_start_time = fall_idx / fs  # converter índice para tempo
        fake_flush_times_fall.append(round(fall_start_time, 2))

        omega_n_list.append(omega_n)
        zeta_list.append(zeta)
        
        if fall_idx < len(pressure_modified):
            normal_pressure = pressure[min(fall_idx, len(pressure) - 1)]
            pressure_modified[fall_idx] = normal_pressure
        
        # Adicionar oscilação após a descida
        oscillation_duration = 0.5
        osc_samples = int(oscillation_duration * fs)
        if fall_idx + osc_samples < len(pressure_modified):
            t_osc = np.linspace(0, oscillation_duration, osc_samples)
            osc_amplitude = (flush_pressure - pressure.min())/2
            osc_signal = generate_oscillation(t_osc, omega_n, zeta, osc_amplitude, normal_pressure)
            pressure_modified[fall_idx:fall_idx + osc_samples] = osc_signal
    
    return pressure_modified, fake_flush_times_fall, omega_n_list, zeta_list


def generate_batch_simulations(num_simulations=100, output_folder='simulacoes_pressao', patient_type='normotensive'):
    """
    Gera simulações de pressão arterial e um arquivo de resumo
    
    Parâmetros:
    - num_simulations: qtd de simulações 
    - output_folder: pasta onde os arquivos serão salvos
    """
    
    # Criar pasta se não existir
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Lista para armazenar estatísticas
    statistics = []
    
    print(f"Gerando {num_simulations} simulações...")
    print("-" * 60)
    
    for i in range(num_simulations):
        # Número aleatório de flush tests para cada simulação
        num_flush_tests = int(np.random.uniform(0, 10))
        num_fake_flush_tests = int(np.random.uniform(0, 5))
        
        # Nome do arquivo
        filename = os.path.join(output_folder, f'pressao_sim_{i+1:03d}.csv')
        
        # Gerar sinal
        time, pressure, p_max, p_min, p_mean, hr, real_flush_times, fake_flush_times, real_flush_omega_n, real_flush_zeta, fake_flush_omega_n, fake_flush_zeta = generate_arterial_pressure_signal(
            duration_hours=1,
            fs=125,
            save_csv=True,
            filename=filename,
            num_flush_tests=num_flush_tests,
            num_fake_flush_tests=num_fake_flush_tests,
            patient_type=patient_type,
            omega_n=np.random.uniform(10, 50),  # frequência natural randômica
            zeta=np.random.uniform(0.1, 0.9)     # coef
        )
        
        # Converter listas de tempos para strings formatadas
        real_flush_str = ' - '.join([str(t) for t in real_flush_times]) if real_flush_times else ''
        fake_flush_str = ' - '.join([str(t) for t in fake_flush_times]) if fake_flush_times else ''

        real_flush_omega_n_str = ' - '.join([str(round(o, 2)) for o in real_flush_omega_n]) if real_flush_omega_n else ''
        real_flush_zeta_str = ' - '.join([str(round(z, 2)) for z in real_flush_zeta]) if real_flush_zeta else ''
        fake_flush_omega_n_str = ' - '.join([str(round(o, 2)) for o in fake_flush_omega_n]) if fake_flush_omega_n else ''
        fake_flush_zeta_str = ' - '.join([str(round(z, 2)) for z in fake_flush_zeta]) if fake_flush_zeta else ''

        # Armazenar estatísticas
        statistics.append({
            'arquivo': f'pressao_sim_{i+1:03d}.csv',
            'tipo_paciente': patient_type,
            'pressao_maxima_mmHg': round(p_max, 2),
            'pressao_minima_mmHg': round(p_min, 2),
            'pressao_media_mmHg': round(p_mean, 2),
            'frequencia_cardiaca_bpm': round(hr, 2),
            'num_flush_tests': num_flush_tests,
            'num_fake_flush_tests': num_fake_flush_tests,
            'tempos_inicio_descida_flush_real_seg': real_flush_str,
            'tempos_inicio_descida_fake_flush_seg': fake_flush_str,
            'real_flush_fn': real_flush_omega_n_str,
            'real_flush_coef_amort': real_flush_zeta_str,
            'fake_flush_fn': fake_flush_omega_n_str,
            'fake_flush_coef_amort': fake_flush_zeta_str,
        })
        
        # Mostrar progresso
        if (i + 1) % 10 == 0:
            print(f"Progresso: {i+1}/{num_simulations} simulações geradas")
    
    # Criar DataFrame com estatísticas
    df_stats = pd.DataFrame(statistics)
    
    # Salvar arquivo de resumo
    summary_filename = os.path.join(output_folder, 'resumo_simulacoes.xlsx')
    df_stats.to_excel(summary_filename, index=False)
    
    print("-" * 60)
    print(f"\n✓ {num_simulations} simulações geradas com sucesso!")
    print(f"✓ Arquivos salvos em: {output_folder}/")
    print(f"✓ Resumo salvo em: {summary_filename}")
    
    # Mostrar estatísticas gerais
    print("\n" + "=" * 60)
    print("ESTATÍSTICAS GERAIS DAS SIMULAÇÕES")
    print("=" * 60)
    print(f"Pressão máxima média: {df_stats['pressao_maxima_mmHg'].mean():.2f} mmHg")
    print(f"Pressão mínima média: {df_stats['pressao_minima_mmHg'].mean():.2f} mmHg")
    print(f"Pressão média geral: {df_stats['pressao_media_mmHg'].mean():.2f} mmHg")
    print(f"Frequência cardíaca média: {df_stats['frequencia_cardiaca_bpm'].mean():.2f} bpm")
    print(f"Média de flush tests reais por simulação: {df_stats['num_flush_tests'].mean():.2f}")
    print(f"Média de fake flush tests por simulação: {df_stats['num_fake_flush_tests'].mean():.2f}")
    print(f"Total de flush tests reais: {df_stats['num_flush_tests'].sum()}")
    print(f"Total de fake flush tests: {df_stats['num_fake_flush_tests'].sum()}")
    
    return df_stats


# Executar a geração em lote
if __name__ == "__main__":
    # Gerar simulações para cada tipo de paciente com quantidade randômica
    all_summaries = []
    for patient_type in patient_types.keys():
        num_sim = np.random.randint(2, 10)  # quantidade randômica entre 20 e 100
        output_folder = f'simulacoes_pressao_{patient_type}'
        print(f"\nGerando {num_sim} simulações para {patient_type}...")
        df_resumo = generate_batch_simulations(num_simulations=num_sim, output_folder=output_folder, patient_type=patient_type)
        all_summaries.append(df_resumo)
        
        # Mostrar primeiras linhas do resumo
        print(f"\nPrimeiras 5 simulações para {patient_type}:")
        print(df_resumo.head(5).to_string(index=False))
    
    # Combinar todos os resumos em um único arquivo
    combined_df = pd.concat(all_summaries, ignore_index=True)
    combined_filename = 'resumo_todas_simulacoes.xlsx'
    combined_df.to_excel(combined_filename, index=False)
    print(f"\n✓ Resumo combinado salvo em: {combined_filename}")
    print(f"Total de simulações: {len(combined_df)}")