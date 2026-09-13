import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_simulation(csv_filename):
    """
    Parâmetros:
    - csv_filename: caminho do arquivo CSV
    """
    # Carregar dados
    df = pd.read_csv(csv_filename)
    time = df['time'].values
    pressure = df['pressure'].values
    
    # Criar figura
    plt.figure(figsize=(14, 6))
    plt.plot(time, pressure, linewidth=0.5, color='darkblue')
    plt.title(f'Sinal de Pressão Arterial - {os.path.basename(csv_filename)}')
    plt.xlabel('Tempo (s)')
    plt.ylabel('Pressão (mmHg)')
    plt.grid(alpha=0.3)
    plt.ylim(0, 320)
    
    plt.tight_layout()
    
    plt.show()
    
    return plt.gcf()

# Exemplos de uso
if __name__ == "__main__":
    folder = 'simulacoes_pressao_onNorepinephrine'
    
    print("=" * 60)
    print("VISUALIZADOR DE SIMULAÇÕES DE PRESSÃO ARTERIAL")
    print("=" * 60)

    print("\n1. Plotando simulação")
    plot_simulation(os.path.join(folder, 'pressao_sim_003.csv'))
    