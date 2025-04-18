import folium
import pandas as pd

def gerar_mapa_rotas(rotas, dados_pedidos):
    """
    Gera um mapa interativo com as rotas usando Folium.
    
    :param rotas: Lista de rotas otimizadas (índices dos pedidos).
    :param dados_pedidos: DataFrame com informações dos pedidos, incluindo latitude e longitude.
    :return: Objeto Folium Map.
    """
    mapa = folium.Map(location=[-23.55052, -46.633308], zoom_start=12)  # Localização inicial (exemplo: São Paulo)

    for rota in rotas:
        pontos = [
            (dados_pedidos.iloc[pedido]["latitude"], dados_pedidos.iloc[pedido]["longitude"])
            for pedido in rota
        ]
        folium.PolyLine(pontos, color="blue", weight=2.5, opacity=1).add_to(mapa)
        for ponto in pontos:
            folium.Marker(location=ponto).add_to(mapa)

    return mapa

def exportar_rotas_excel(rotas, dados_pedidos, caminho="rotas.xlsx"):
    """
    Exporta as rotas otimizadas para um arquivo Excel.
    
    :param rotas: Lista de rotas otimizadas (índices dos pedidos).
    :param dados_pedidos: DataFrame com informações dos pedidos.
    :param caminho: Caminho para salvar o arquivo Excel.
    """
    rotas_exportadas = []
    for veiculo_id, rota in enumerate(rotas):
        for ordem, pedido_idx in enumerate(rota):
            pedido = dados_pedidos.iloc[pedido_idx].to_dict()
            pedido["Veículo"] = f"Veículo {veiculo_id + 1}"
            pedido["Ordem"] = ordem + 1
            rotas_exportadas.append(pedido)

    df_rotas = pd.DataFrame(rotas_exportadas)
    df_rotas.to_excel(caminho, index=False)
    print(f"Rotas exportadas para {caminho}")

def salvar_historico(rotas, dados_pedidos, caminho="historico_rotas.xlsx"):
    """
    Salva as rotas no histórico para aprendizado futuro.
    
    :param rotas: Lista de rotas otimizadas (índices dos pedidos).
    :param dados_pedidos: DataFrame com informações dos pedidos.
    :param caminho: Caminho para salvar o histórico.
    """
    try:
        historico = pd.read_excel(caminho)
    except FileNotFoundError:
        historico = pd.DataFrame()

    rotas_exportadas = []
    for veiculo_id, rota in enumerate(rotas):
        for ordem, pedido_idx in enumerate(rota):
            pedido = dados_pedidos.iloc[pedido_idx].to_dict()
            pedido["Veículo"] = f"Veículo {veiculo_id + 1}"
            pedido["Ordem"] = ordem + 1
            rotas_exportadas.append(pedido)

    df_rotas = pd.DataFrame(rotas_exportadas)
    historico = pd.concat([historico, df_rotas], ignore_index=True)
    historico.to_excel(caminho, index=False)
    print(f"Histórico atualizado em {caminho}")
