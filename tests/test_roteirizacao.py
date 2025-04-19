import pytest
from roteirizacao import otimizar_rotas

def test_otimizar_rotas():
    pedidos = [(0, 0), (1, 1), (2, 2)]
    resultado = otimizar_rotas(pedidos)
    assert isinstance(resultado, list)
    assert len(resultado) == len(pedidos)