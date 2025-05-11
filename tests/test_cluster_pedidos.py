import pandas as pd
from app.pedidos import processar_pedidos
import io

def test_cluster_por_regiao():
    # Simula um arquivo CSV com várias regiões
    csv = io.StringIO("""
Nº Pedido,Endereço de Entrega,Bairro de Entrega,Cidade de Entrega,Estado de Entrega,Qtde. dos Itens,Peso dos Itens
1,Rua A,Campo Belo,São Paulo,SP,10,100
2,Rua B,Santana,São Paulo,SP,5,50
3,Rua C,Penha,São Paulo,SP,8,80
4,Rua D,Lapa,São Paulo,SP,12,120
5,Rua E,Sé,São Paulo,SP,7,70
6,Rua F,Centro,Campinas,SP,6,60
""")
    df = processar_pedidos(csv)
    # Verifica se cada região de SP tem um cluster distinto
    regioes_sp = df[df['Cidade de Entrega'] == 'São Paulo']['Região']
    clusters_sp = df[df['Cidade de Entrega'] == 'São Paulo']['Cluster']
    assert len(regioes_sp.unique()) == len(clusters_sp.unique()), "Cada região de SP deve ter um cluster distinto"
    # Verifica se cidades diferentes de SP também recebem cluster próprio
    assert df[df['Cidade de Entrega'] == 'Campinas']['Cluster'].nunique() == 1
    print("Teste de clusterização por região passou!")

if __name__ == "__main__":
    test_cluster_por_regiao()
