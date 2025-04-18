import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN

def clusterizar_pedidos_kmeans(pedidos, n_clusters=5):
    """
    Agrupa pedidos por proximidade geográfica usando KMeans.
    
    :param pedidos: DataFrame com colunas 'latitude' e 'longitude'.
    :param n_clusters: Número de clusters.
    :return: DataFrame com os clusters atribuídos.
    """
    coordenadas = pedidos[["latitude", "longitude"]].dropna()
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    pedidos["cluster"] = kmeans.fit_predict(coordenadas)
    pedidos["centroide_latitude"] = pedidos["cluster"].map(
        lambda c: kmeans.cluster_centers_[c][0]
    )
    pedidos["centroide_longitude"] = pedidos["cluster"].map(
        lambda c: kmeans.cluster_centers_[c][1]
    )
    return pedidos

def clusterizar_pedidos_dbscan(pedidos, eps=0.5, min_samples=5):
    """
    Agrupa pedidos por proximidade geográfica usando DBSCAN.
    
    :param pedidos: DataFrame com colunas 'latitude' e 'longitude'.
    :param eps: Distância máxima entre dois pontos para serem considerados no mesmo cluster.
    :param min_samples: Número mínimo de pontos para formar um cluster.
    :return: DataFrame com os clusters atribuídos.
    """
    coordenadas = pedidos[["latitude", "longitude"]].dropna()
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    pedidos["cluster"] = dbscan.fit_predict(coordenadas)
    return pedidos

def priorizar_clusters(pedidos, criterio="volume_total"):
    """
    Prioriza clusters com base em um critério (volume total ou urgência).
    
    :param pedidos: DataFrame com colunas 'cluster' e o critério escolhido.
    :param criterio: Critério de priorização ('volume_total' ou 'urgencia').
    :return: DataFrame com clusters ordenados por prioridade.
    """
    prioridades = pedidos.groupby("cluster")[criterio].sum().sort_values(ascending=False)
    pedidos["prioridade_cluster"] = pedidos["cluster"].map(prioridades.rank(ascending=True))
    return pedidos
