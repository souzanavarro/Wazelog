import pytest
from pedidos import geocodificar_pedidos

def test_geocodificar_enderecos():
    enderecos = ["Rua A, 123", "Rua B, 456"]
    resultado = geocodificar_pedidos(enderecos)
    assert len(resultado) == len(enderecos)
    assert all(isinstance(coord, tuple) for coord in resultado)