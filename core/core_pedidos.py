import pandas as pd
from fuzzywuzzy import process
from geopy.geocoders import Nominatim

def carregar_dados_pedidos(caminho_planilha="pedidos.xlsx"):
    """
    Carrega os dados da planilha de pedidos e retorna um DataFrame.
    """
    try:
        df = pd.read_excel(caminho_planilha)
        return df
    except Exception as e:
        print(f"Erro ao carregar a planilha de pedidos: {e}")
        return pd.DataFrame()

def corrigir_enderecos(df, col_endereco, lista_enderecos_validos):
    """
    Corrige endereços com erros usando fuzzy matching.
    """
    df[col_endereco] = df[col_endereco].apply(
        lambda x: process.extractOne(x, lista_enderecos_validos)[0] if x else x
    )
    return df

def geocodificar_enderecos(df, col_endereco):
    """
    Geocodifica endereços para obter latitude e longitude.
    """
    geolocator = Nominatim(user_agent="roteirizador")
    coordenadas = []

    for endereco in df[col_endereco]:
        try:
            location = geolocator.geocode(endereco)
            if location:
                coordenadas.append((location.latitude, location.longitude))
            else:
                coordenadas.append((None, None))
        except Exception as e:
            print(f"Erro ao geocodificar o endereço '{endereco}': {e}")
            coordenadas.append((None, None))

    df["latitude"], df["longitude"] = zip(*coordenadas)
    return df

def validar_dados(df):
    """
    Valida os dados dos pedidos, como peso, volume e janela de entrega.
    """
    df["valido"] = df.apply(
        lambda row: row["Peso dos Itens"] > 0 and row["Qtde. dos Itens"] > 0 and row["Endereço de Entrega"] is not None,
        axis=1
    )
    return df[df["valido"]]

def calcular_peso_volume_total(df):
    """
    Calcula o peso e volume total por pedido.
    """
    df["peso_total"] = df["Peso dos Itens"] * df["Qtde. dos Itens"]
    # Supondo que o volume por item seja fornecido em uma coluna "Volume por Item"
    if "Volume por Item" in df.columns:
        df["volume_total"] = df["Volume por Item"] * df["Qtde. dos Itens"]
    else:
        df["volume_total"] = 0  # Caso não exista a coluna
    return df