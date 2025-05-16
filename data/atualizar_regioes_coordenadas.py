
import pandas as pd
import os
import sys
# Adiciona o diretório raiz do projeto ao sys.path para importar 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.pedidos import definir_regiao

# Caminho do arquivo de coordenadas
csv_path = os.path.join(os.path.dirname(__file__), 'Coordenadas.csv')

def atualizar_regioes():
    if not os.path.exists(csv_path):
        print('Arquivo Coordenadas.csv não encontrado!')
        return
    df = pd.read_csv(csv_path, dtype=str)
    # Garante que as colunas existam
    for col in ['Latitude', 'Longitude']:
        if col not in df.columns:
            df[col] = None
    # Aplica a função de região para cada linha
    df['Região'] = df.apply(definir_regiao, axis=1)
    df.to_csv(csv_path, index=False)
    print('Regiões atualizadas com sucesso em Coordenadas.csv!')

if __name__ == '__main__':
    atualizar_regioes()
