import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.express as px
import streamlit as st
import folium
from streamlit_folium import st_folium

def grafico_barras_comparativo(dados, titulo, eixo_x, eixo_y):
    """
    Gera um gráfico de barras comparativo usando Seaborn.

    :param dados: DataFrame com os dados para o gráfico.
    :param titulo: Título do gráfico.
    :param eixo_x: Nome da coluna para o eixo X.
    :param eixo_y: Nome da coluna para o eixo Y.
    """
    plt.figure(figsize=(10, 6))
    sns.barplot(data=dados, x=eixo_x, y=eixo_y, palette="viridis")
    plt.title(titulo)
    plt.xlabel(eixo_x)
    plt.ylabel(eixo_y)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def grafico_pizza_distribuicao(dados, coluna, titulo):
    """
    Gera um gráfico de pizza para visualizar a distribuição de uma coluna.

    :param dados: DataFrame com os dados para o gráfico.
    :param coluna: Nome da coluna para a distribuição.
    :param titulo: Título do gráfico.
    """
    distribuicao = dados[coluna].value_counts()
    plt.figure(figsize=(8, 8))
    distribuicao.plot.pie(autopct="%1.1f%%", startangle=90, colors=sns.color_palette("viridis", len(distribuicao)))
    plt.title(titulo)
    plt.ylabel("")
    plt.show()

def mapa_interativo_rotas(rotas, dados_pedidos):
    """
    Gera um mapa interativo com as rotas usando Plotly.

    :param rotas: Lista de rotas otimizadas (índices dos pedidos).
    :param dados_pedidos: DataFrame com informações dos pedidos, incluindo latitude e longitude.
    :return: Objeto Plotly Figure.
    """
    fig = px.scatter_mapbox(
        dados_pedidos,
        lat="latitude",
        lon="longitude",
        hover_name="ID",
        zoom=10,
        height=600
    )
    fig.update_layout(mapbox_style="open-street-map")

    for rota in rotas:
        pontos = [
            dict(lat=dados_pedidos.iloc[pedido]["latitude"], lon=dados_pedidos.iloc[pedido]["longitude"])
            for pedido in rota
        ]
        fig.add_trace(px.line_mapbox(
            pd.DataFrame(pontos),
            lat="lat",
            lon="lon"
        ).data[0])

    return fig

def visualizar_pedidos_mapa(pedidos):
    """
    Exibe os pedidos em um mapa interativo usando Folium.
    """
    mapa = folium.Map(location=[-23.55052, -46.633308], zoom_start=12)

    for _, pedido in pedidos.iterrows():
        folium.Marker(
            location=[pedido["latitude"], pedido["longitude"]],
            popup=f"Pedido ID: {pedido['id']}\nCliente: {pedido['cliente']}\nEndereço: {pedido['endereco']}"
        ).add_to(mapa)

    st_folium(mapa, width=700, height=500)