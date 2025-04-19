import pytest
from core.core_clusterizacao import clusterizar_pedidos_kmeans

def test_clusterizar_pedidos_kmeans():
    pedidos = [(0, 0), (1, 1), (2, 2)]
    n_clusters = 2
    resultado = clusterizar_pedidos_kmeans(pedidos, n_clusters)
    assert isinstance(resultado, list)
    assert len(resultado) == len(pedidos)