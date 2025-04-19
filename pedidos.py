import streamlit as st
import pandas as pd
import os
import requests
import json

# Caminho para o arquivo local da base de dados de pedidos e coordenadas
CAMINHO_BASE_PEDIDOS = "database/pedidos.csv"
CAMINHO_CACHE_COORDENADAS = "database/cache_coordenadas.csv"

# Lista de chaves da API do OpenCage Geocoder
API_KEYS_OPENCAGE = [
    "5161dbd006cf4c43a7f7dd789ee1a3da",
    "6f522c67add14152926990afbe127384",
    "6c2d02cafb2e4b49aa3485a62262e54b"
]

def obter_coordenadas_com_fallback(endereco, api_keys):
    """
    Obtém as coordenadas de um endereço usando múltiplas chaves de API do OpenCage Geocoder.
    """
    for api_key in api_keys:
        url = f"https://api.opencagedata.com/geocode/v1/json?q={endereco}&key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                coordenadas = data["results"][0]["geometry"]
                return coordenadas["lat"], coordenadas["lng"]
        elif response.status_code == 402:  # Limite de requisições atingido
            continue
    return None, None

def preencher_regioes_pedidos(df, progress_callback=None):
    """
    Preenche a coluna 'Região' dos pedidos com base nas coordenadas (reverse geocoding).
    """
    if "Latitude" not in df.columns or "Longitude" not in df.columns:
        st.error("As colunas 'Latitude' e 'Longitude' são necessárias para preencher as regiões.")
        return df

    regioes = []
    total = len(df)
    for idx, row in df.iterrows():
        if pd.notnull(row["Latitude"]) and pd.notnull(row["Longitude"]):
            # Simulação de reverse geocoding (substitua por uma API real, se necessário)
            regioes.append(f"Região-{int(row['Latitude'])}-{int(row['Longitude'])}")
        else:
            regioes.append(None)
        if progress_callback:
            progress_callback(idx + 1, total)

    df["Região"] = regioes
    return df

def carregar_base_pedidos():
    """
    Carrega a base de dados local dos pedidos.
    """
    if os.path.exists(CAMINHO_BASE_PEDIDOS):
        return pd.read_csv(CAMINHO_BASE_PEDIDOS)
    else:
        return pd.DataFrame(columns=["ID Pedido", "Cliente", "Endereço", "Produto", "Quantidade", "Peso", "Status"])

def salvar_base_pedidos(df):
    """
    Salva a base de dados local dos pedidos.
    """
    os.makedirs(os.path.dirname(CAMINHO_BASE_PEDIDOS), exist_ok=True)
    df.to_csv(CAMINHO_BASE_PEDIDOS, index=False)

def carregar_cache_coordenadas():
    """
    Carrega o cache de coordenadas de um arquivo CSV.
    """
    if os.path.exists(CAMINHO_CACHE_COORDENADAS):
        return pd.read_csv(CAMINHO_CACHE_COORDENADAS).set_index("Endereço").to_dict("index")
    return {}

def salvar_cache_coordenadas(cache):
    """
    Salva o cache de coordenadas em um arquivo CSV.
    """
    os.makedirs(os.path.dirname(CAMINHO_CACHE_COORDENADAS), exist_ok=True)
    cache_df = pd.DataFrame.from_dict(cache, orient="index").reset_index()
    cache_df.columns = ["Endereço", "Latitude", "Longitude"]
    cache_df.to_csv(CAMINHO_CACHE_COORDENADAS, index=False)

def validar_cabecalho_pedidos(df):
    """
    Valida se a planilha de pedidos contém os cabeçalhos corretos.
    """
    cabecalhos_esperados = [
        "Nº Pedido", "Cód. Cliente", "Nome Cliente", "Grupo Cliente", 
        "Endereço de Entrega", "Bairro de Entrega", "Cidade de Entrega", 
        "Qtde. dos Itens", "Peso dos Itens"
    ]
    return all(col in df.columns for col in cabecalhos_esperados)

def definir_regiao(df):
    """
    Define a região com base na Cidade de Entrega.
    Se a Cidade de Entrega for 'São Paulo', considera o Bairro de Entrega como região.
    """
    if all(col in df.columns for col in ["Cidade de Entrega", "Bairro de Entrega"]):
        df["Regiao"] = df.apply(
            lambda row: row["Bairro de Entrega"] if row["Cidade de Entrega"] == "São Paulo" else row["Cidade de Entrega"],
            axis=1
        )
    else:
        raise ValueError("As colunas 'Cidade de Entrega' e 'Bairro de Entrega' são necessárias.")
    return df

def obter_coordenadas(endereco, cache):
    """
    Obtém as coordenadas de um endereço, usando o cache ou a API do OpenCage Geocoder.
    """
    if endereco in cache:
        return cache[endereco]["Latitude"], cache[endereco]["Longitude"]
    lat, lon = obter_coordenadas_com_fallback(endereco, API_KEYS_OPENCAGE)
    if lat is not None and lon is not None:
        cache[endereco] = {"Latitude": lat, "Longitude": lon}
        salvar_cache_coordenadas(cache)
    return lat, lon

def geocodificar_pedidos(df):
    """
    Adiciona colunas de latitude e longitude ao DataFrame de pedidos e salva na planilha.
    """
    if "Endereco Completo" not in df.columns:
        st.error("A coluna 'Endereco Completo' não foi encontrada na planilha de pedidos.")
        return df

    # Carregar o cache de coordenadas
    cache = carregar_cache_coordenadas()

    latitudes = []
    longitudes = []

    for _, row in df.iterrows():
        endereco = f"{row['Endereço de Entrega']}, {row['Bairro de Entrega']}, {row['Cidade de Entrega']}"
        lat, lon = obter_coordenadas(endereco, cache)
        latitudes.append(lat)
        longitudes.append(lon)

    df["Latitude"] = latitudes
    df["Longitude"] = longitudes

    # Salvar as coordenadas diretamente na planilha de pedidos
    salvar_base_pedidos(df)
    return df

def pagina_pedidos():
    st.title("📦 Gerenciamento de Pedidos")
    st.markdown("""
    ### Adicione, edite ou remova pedidos.
    """)

    # Carregar dados dos pedidos
    pedidos_path = "database/pedidos.csv"
    pedidos_df = pd.read_csv(pedidos_path)

    # Exibir tabela interativa
    st.dataframe(pedidos_df, use_container_width=True)

    # Formulário para adicionar novo pedido
    with st.form("adicionar_pedido"):
        st.subheader("Adicionar Pedido")
        id_pedido = st.text_input("ID do Pedido")
        endereco = st.text_input("Endereço")
        peso = st.number_input("Peso (kg)", min_value=0)
        submit = st.form_submit_button("Adicionar")

        if submit:
            novo_pedido = {
                "ID": id_pedido,
                "Endereço": endereco,
                "Peso": peso,
            }
            pedidos_df = pedidos_df.append(novo_pedido, ignore_index=True)
            pedidos_df.to_csv(pedidos_path, index=False)
            st.success("Pedido adicionado com sucesso!")

    # Botão para remover pedido
    st.subheader("Remover Pedido")
    id_remover = st.selectbox("Selecione o ID para remover", pedidos_df["ID"].tolist())
    if st.button("Remover"):
        pedidos_df = pedidos_df[pedidos_df["ID"] != id_remover]
        pedidos_df.to_csv(pedidos_path, index=False)
        st.success("Pedido removido com sucesso!")
