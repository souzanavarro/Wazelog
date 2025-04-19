import streamlit as st
import pandas as pd
import os
import json

def carregar_configuracoes():
    """
    Carrega as configurações salvas do roteirizador.
    """
    caminho_config = "database/configuracoes_roteirizador.json"
    if os.path.exists(caminho_config):
        with open(caminho_config, "r") as f:
            return json.load(f)
    return {}

def salvar_configuracoes(config):
    """
    Salva as configurações do roteirizador em um arquivo JSON.
    """
    caminho_config = "database/configuracoes_roteirizador.json"
    os.makedirs(os.path.dirname(caminho_config), exist_ok=True)
    with open(caminho_config, "w") as f:
        json.dump(config, f, indent=4)

def carregar_dados_pedidos():
    """
    Carrega os dados de pedidos do banco de dados.
    """
    caminho_pedidos = "database/pedidos.csv"
    if os.path.exists(caminho_pedidos):
        return pd.read_csv(caminho_pedidos)
    else:
        st.error("Nenhum pedido encontrado. Certifique-se de que os pedidos foram cadastrados.")
        return pd.DataFrame()

def carregar_dados_frota():
    """
    Carrega os dados da frota do banco de dados.
    """
    caminho_frota = "database/frota.csv"
    if os.path.exists(caminho_frota):
        return pd.read_csv(caminho_frota)
    else:
        st.error("Nenhuma frota encontrada. Certifique-se de que a frota foi cadastrada.")
        return pd.DataFrame()

def preparar_dados_para_roteirizacao(pedidos, frota, config):
    """
    Prepara os dados de pedidos e frota para a roteirização.
    """
    # Filtrar veículos disponíveis
    frota_disponivel = frota[frota["Disponível"].str.lower() == "sim"]

    # Verificar se há veículos disponíveis
    if frota_disponivel.empty:
        st.error("Nenhum veículo disponível na frota.")
        return None, None

    # Verificar se há pedidos com coordenadas válidas
    pedidos_validos = pedidos.dropna(subset=["Latitude", "Longitude"])
    if pedidos_validos.empty:
        st.error("Nenhum pedido com coordenadas válidas encontrado.")
        return None, None

    # Aplicar restrições e preferências
    if config.get("capacidade"):
        pedidos_validos = pedidos_validos[pedidos_validos["Peso dos Itens"] <= frota_disponivel["Capacidade (Kg)"].max()]

    return pedidos_validos, frota_disponivel

def pagina_roteirizador():
    st.title("⚙️ Configurações do Roteirizador")
    st.markdown("""
    ### Configure os parâmetros para a roteirização:
    - Escolha o critério de otimização.
    - Defina restrições e preferências.
    """)

    # Adicionar uma caixa de informações no topo
    st.info("⚡ Configure os parâmetros abaixo para otimizar suas rotas de entrega.")

    # Carregar configurações salvas
    config_salvas = carregar_configuracoes()

    # Dividir a página em duas colunas para melhor organização
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🛠️ Critério de Otimização")
        criterio = st.selectbox(
            "Escolha o critério:",
            ["Menor Distância", "Menor Tempo", "Menor Custo"],
            index=["Menor Distância", "Menor Tempo", "Menor Custo"].index(config_salvas.get("criterio", "Menor Distância"))
        )

        st.markdown("#### 🔒 Restrições")
        janela_tempo = st.checkbox("Considerar janelas de tempo", value=config_salvas.get("janela_tempo", False))
        capacidade = st.checkbox("Respeitar capacidade dos veículos", value=config_salvas.get("capacidade", False))

    with col2:
        st.markdown("#### 📍 Preferências")
        ponto_partida = st.text_input(
            "Ponto de partida (endereço ou coordenadas)",
            value=config_salvas.get("ponto_partida", ""),
            placeholder="Ex: Rua A, 123, São Paulo"
        )
        ponto_chegada = st.text_input(
            "Ponto de chegada (opcional)",
            value=config_salvas.get("ponto_chegada", ""),
            placeholder="Ex: Rua B, 456, São Paulo"
        )

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        salvar = st.button("💾 Salvar Configurações")
        preparar = st.button("🚀 Preparar Dados para Roteirização")

        if salvar:
            config = {
                "criterio": criterio,
                "janela_tempo": janela_tempo,
                "capacidade": capacidade,
                "ponto_partida": ponto_partida,
                "ponto_chegada": ponto_chegada
            }
            salvar_configuracoes(config)
            st.success("Configurações salvas com sucesso! Arquivo criado em `database/configuracoes_roteirizador.json`.")

        if preparar:
            pedidos = carregar_dados_pedidos()
            frota = carregar_dados_frota()
            config = carregar_configuracoes()

            if not pedidos.empty and not frota.empty:
                pedidos_validos, frota_disponivel = preparar_dados_para_roteirizacao(pedidos, frota, config)
                if pedidos_validos is not None and frota_disponivel is not None:
                    st.success("Dados preparados com sucesso!")
                    st.markdown("#### Pedidos Válidos")
                    st.dataframe(pedidos_validos)
                    st.markdown("#### Frota Disponível")
                    st.dataframe(frota_disponivel)
