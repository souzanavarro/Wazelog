import random
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import numpy as np
from transformers import pipeline

class ModeloIA:
    def __init__(self):
        """
        Inicializa um modelo de IA gratuito usando a biblioteca Hugging Face Transformers.
        """
        self.modelo = pipeline("text-classification", model="distilbert-base-uncased")

    def ajustar_dados(self, dados):
        """
        Ajusta os dados de roteirização com base em previsões do modelo de IA.

        :param dados: Dicionário com dados de pedidos e veículos.
        :return: Dados ajustados com base nas previsões do modelo de IA.
        """
        for pedido in dados['pedidos']:
            texto = f"Prioridade: {pedido['prioridade']}, Volume: {pedido['volume']}, Distância: {pedido['distancia']}"
            previsao = self.modelo(texto)[0]
            pedido['ajuste_ia'] = previsao['label']
        return dados

def simulated_annealing(dados, parametros):
    """
    Implementação básica de simulated annealing para otimização de rotas.
    """
    # Inicializar solução
    solucao_atual = gerar_solucao_inicial(dados)
    melhor_solucao = solucao_atual
    temperatura = parametros.get('temperatura_inicial', 1000)
    resfriamento = parametros.get('taxa_resfriamento', 0.99)

    while temperatura > 1:
        nova_solucao = perturbar_solucao(solucao_atual)
        delta = calcular_custo(nova_solucao, dados) - calcular_custo(solucao_atual, dados)

        if delta < 0 or random.uniform(0, 1) < aceitar(delta, temperatura):
            solucao_atual = nova_solucao
            if calcular_custo(solucao_atual, dados) < calcular_custo(melhor_solucao, dados):
                melhor_solucao = solucao_atual

        temperatura *= resfriamento

    return melhor_solucao

def gerar_solucao_inicial(dados):
    # Gerar uma solução inicial aleatória
    return random.sample(range(len(dados['distancias'])), len(dados['distancias']))

def perturbar_solucao(solucao):
    # Perturbar a solução atual (swap aleatório)
    nova_solucao = solucao[:]
    i, j = random.sample(range(len(solucao)), 2)
    nova_solucao[i], nova_solucao[j] = nova_solucao[j], nova_solucao[i]
    return nova_solucao

def calcular_custo(solucao, dados):
    # Calcular o custo total da solução
    custo = 0
    for i in range(len(solucao) - 1):
        custo += dados['distancias'][solucao[i]][solucao[i + 1]]
    return custo

def aceitar(delta, temperatura):
    # Função de aceitação para simulated annealing
    import math
    return math.exp(-delta / temperatura)

def clustering_entregas(dados, metodo="kmeans", n_clusters=3):
    """
    Realiza clustering de entregas baseado em localização e tipo de carga.
    """
    coordenadas = np.array(dados['coordenadas'])  # Exemplo: [(lat1, lon1), (lat2, lon2), ...]
    if metodo == "kmeans":
        modelo = KMeans(n_clusters=n_clusters, random_state=42)
    elif metodo == "dbscan":
        modelo = DBSCAN(eps=0.5, min_samples=5)
    else:
        raise ValueError("Método de clustering não suportado.")
    
    clusters = modelo.fit_predict(coordenadas)
    return clusters

def predicao_tempo_entrega(dados_historicos, novas_entregas):
    """
    Prediz tempos de entrega com base em dados históricos usando regressão linear.
    """
    # Dados históricos: {'distancia': [10, 20, ...], 'tempo': [15, 30, ...]}
    X = np.array(dados_historicos['distancia']).reshape(-1, 1)
    y = np.array(dados_historicos['tempo'])
    
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    # Predizer tempos para novas entregas
    novas_distancias = np.array(novas_entregas['distancia']).reshape(-1, 1)
    tempos_preditos = modelo.predict(novas_distancias)
    return tempos_preditos

def aprendizado_regras_negocio(dados_historicos):
    """
    Aprende padrões de regras de negócio, como preferências de horário de entrega.
    """
    # Exemplo de dados_historicos: [{'cliente': 'X', 'horario': 'tarde'}, ...]
    regras = {}
    for registro in dados_historicos:
        cliente = registro['cliente']
        horario = registro['horario']
        if cliente not in regras:
            regras[cliente] = {}
        if horario not in regras[cliente]:
            regras[cliente][horario] = 0
        regras[cliente][horario] += 1
    
    # Determinar o horário preferido para cada cliente
    preferencias = {cliente: max(horarios, key=horarios.get) for cliente, horarios in regras.items()}
    return preferencias

def treinar_modelo_previsao_atrasos(dados_historicos):
    """
    Treina um modelo de aprendizado de máquina para prever atrasos nas rotas.

    :param dados_historicos: DataFrame com dados históricos contendo as colunas 'distancia', 'tempo_estimado' e 'atraso'.
    :return: Modelo treinado e erro médio absoluto (MAE).
    """
    # Verificar se as colunas necessárias estão presentes
    colunas_necessarias = ['distancia', 'tempo_estimado', 'atraso']
    if not all(col in dados_historicos.columns for col in colunas_necessarias):
        raise ValueError(f"O DataFrame deve conter as colunas: {colunas_necessarias}")

    # Dividir os dados em recursos (X) e alvo (y)
    X = dados_historicos[['distancia', 'tempo_estimado']]
    y = dados_historicos['atraso']

    # Dividir os dados em conjuntos de treino e teste
    X_treino, X_teste, y_treino, y_teste = train_test_split(X, y, test_size=0.2, random_state=42)

    # Treinar o modelo
    modelo = RandomForestRegressor(random_state=42)
    modelo.fit(X_treino, y_treino)

    # Avaliar o modelo
    previsoes = modelo.predict(X_teste)
    mae = mean_absolute_error(y_teste, previsoes)

    return modelo, mae

def prever_atrasos(modelo, dados_novos):
    """
    Usa o modelo treinado para prever atrasos em novos dados.

    :param modelo: Modelo treinado.
    :param dados_novos: DataFrame com as colunas 'distancia' e 'tempo_estimado'.
    :return: Série com os atrasos previstos.
    """
    colunas_necessarias = ['distancia', 'tempo_estimado']
    if not all(col in dados_novos.columns for col in colunas_necessarias):
        raise ValueError(f"O DataFrame deve conter as colunas: {colunas_necessarias}")

    return modelo.predict(dados_novos)