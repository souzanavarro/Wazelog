import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import json
import os

def registrar_feedback(rotas_executadas, feedbacks, caminho="database/feedback_rotas.json"):
    """
    Registra o feedback fornecido pelos motoristas sobre as rotas executadas.

    :param rotas_executadas: Lista de rotas realmente executadas.
    :param feedbacks: Lista de dicionários com feedbacks para cada rota.
    :param caminho: Caminho para salvar o arquivo JSON com os feedbacks.
    """
    dados_feedback = []

    for i, rota in enumerate(rotas_executadas):
        dados_feedback.append({
            "rota": rota,
            "feedback": feedbacks[i]
        })

    if os.path.exists(caminho):
        with open(caminho, "r") as arquivo:
            feedback_existente = json.load(arquivo)
    else:
        feedback_existente = []

    feedback_existente.extend(dados_feedback)

    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w") as arquivo:
        json.dump(feedback_existente, arquivo, indent=4)

def carregar_feedback(caminho="database/feedback_rotas.json"):
    """
    Carrega o feedback registrado sobre as rotas executadas.

    :param caminho: Caminho do arquivo JSON com os feedbacks.
    :return: Lista de feedbacks registrados.
    """
    if os.path.exists(caminho):
        with open(caminho, "r") as arquivo:
            return json.load(arquivo)
    return []

def registrar_feedback(entregas_realizadas, feedbacks):
    """
    Registra o feedback das entregas realizadas.
    
    :param entregas_realizadas: Lista de entregas realizadas (dicionários).
    :param feedbacks: Lista de feedbacks (dicionários com atrasos, desvios, etc.).
    :return: DataFrame consolidado com entregas e feedbacks.
    """
    df_entregas = pd.DataFrame(entregas_realizadas)
    df_feedbacks = pd.DataFrame(feedbacks)
    df_consolidado = pd.merge(df_entregas, df_feedbacks, on="Nº Pedido", how="left")
    return df_consolidado

def avaliar_performance(df_consolidado):
    """
    Avalia a performance das entregas com base nos feedbacks.
    
    :param df_consolidado: DataFrame consolidado com entregas e feedbacks.
    :return: Métricas de performance.
    """
    total_entregas = len(df_consolidado)
    atrasos = df_consolidado["atraso"].sum()
    desvios = df_consolidado["desvio"].sum()
    media_tempo_real = df_consolidado["tempo_real"].mean()
    
    return {
        "total_entregas": total_entregas,
        "atrasos": atrasos,
        "desvios": desvios,
        "media_tempo_real": media_tempo_real
    }

def aprendizado_continuo(df_consolidado):
    """
    Aprende com os dados históricos para reforçar rotas que funcionaram bem.
    
    :param df_consolidado: DataFrame consolidado com entregas e feedbacks.
    :return: Modelo treinado para predição de tempos futuros.
    """
    # Treinar um modelo de regressão para prever tempos reais com base em dados históricos
    X = df_consolidado[["distancia", "tempo_estimado"]]
    y = df_consolidado["tempo_real"]
    
    modelo = LinearRegression()
    modelo.fit(X, y)
    
    return modelo
