import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

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
