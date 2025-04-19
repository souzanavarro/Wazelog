import core.core_frota as frota
import core.core_pedidos as pedidos
import core.core_roteirizador as roteirizador
import core.core_ia as ia
import streamlit as st
import pandas as pd
import os
from core.core_frota import carregar_dados_frota
from core.core_pedidos import carregar_dados_pedidos
from core.core_roteirizador import resolver_vrp
from core.core_regras_negocio import aplicar_regras_negocio, carregar_regras_personalizadas
from core.core_mapas import calcular_distancia_osrm
from core.core_feedback import registrar_feedback, avaliar_performance, aprendizado_continuo
from core.core_fluxo import fluxo_completo
from core.core_clusterizacao import clusterizar_pedidos_kmeans, priorizar_clusters
from core.core_distribuicao import verificar_disponibilidade_veiculos, distribuir_carga_por_veiculo
from core.core_roteirizacao import otimizar_rota
from core.core_exportacao import gerar_mapa_rotas, exportar_rotas_excel, salvar_historico

# Caminhos para as planilhas no banco de dados
CAMINHO_BASE_PEDIDOS = "database/pedidos.csv"
CAMINHO_BASE_FROTA = "database/frota.csv"

def carregar_planilha(caminho, nome):
    """
    Carrega uma planilha do banco de dados.
    """
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    else:
        st.error(f"A planilha de {nome} não foi encontrada no caminho: {caminho}")
        return pd.DataFrame()

def geocodificar_enderecos(df, endereco_coluna):
    """
    Combina as colunas de endereço, bairro e cidade para criar um endereço completo.
    """
    if all(col in df.columns for col in ["Endereço de Entrega", "Bairro de Entrega", "Cidade de Entrega"]):
        df[endereco_coluna] = (
            df["Endereço de Entrega"].fillna("") + ", " +
            df["Bairro de Entrega"].fillna("") + ", " +
            df["Cidade de Entrega"].fillna("")
        )
    else:
        raise ValueError("As colunas 'Endereço de Entrega', 'Bairro de Entrega' e 'Cidade de Entrega' são necessárias.")
    return df

def definir_regiao(df, regiao_coluna):
    """
    Define a região com base na Cidade de Entrega.
    Se a Cidade de Entrega for 'São Paulo', considera o Bairro de Entrega como região.
    """
    if all(col in df.columns for col in ["Cidade de Entrega", "Bairro de Entrega"]):
        df[regiao_coluna] = df.apply(
            lambda row: row["Bairro de Entrega"] if row["Cidade de Entrega"] == "São Paulo" else row["Cidade de Entrega"],
            axis=1
        )
    else:
        raise ValueError("As colunas 'Cidade de Entrega' e 'Bairro de Entrega' são necessárias.")
    return df

def unir_dados_e_roteirizar():
    # Carregar dados da frota
    dados_frota = frota.carregar_dados_frota()
    
    # Carregar dados dos pedidos
    dados_pedidos = pedidos.carregar_dados_pedidos()
    
    # Aplicar parâmetros de roteirização
    parametros = roteirizador.obter_parametros()
    dados_roteirizados = roteirizador.aplicar_roteirizacao(dados_frota, dados_pedidos, parametros)
    
    # Encaminhar para IA para otimização
    resultado_final = ia.otimizar_roteirizacao(dados_roteirizados)
    
    return resultado_final

def pagina_roteirizacao():
    st.title("📍 Roteirização")
    st.markdown("""
    ### Configure e execute a roteirização:
    - Visualize os dados de pedidos e frota.
    - Execute a otimização de rotas.
    """)

    # Dividir a página em duas colunas para melhor organização
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("#### Dados de Pedidos")
        dados_pedidos = carregar_planilha(CAMINHO_BASE_PEDIDOS, "pedidos")
        if not dados_pedidos.empty:
            st.dataframe(dados_pedidos, use_container_width=True)

        st.markdown("#### Dados de Frota")
        dados_frota = carregar_planilha(CAMINHO_BASE_FROTA, "frota")
        if not dados_frota.empty:
            # Filtrar veículos disponíveis
            dados_frota_disponiveis = dados_frota[dados_frota["Disponível"] == "Sim"]
            st.dataframe(dados_frota_disponiveis, use_container_width=True)

    with col2:
        st.markdown("#### Ações")
        if st.button("🚀 Executar Roteirização"):
            if dados_pedidos.empty or dados_frota_disponiveis.empty:
                st.error("Certifique-se de que as planilhas de pedidos e frota estão carregadas corretamente e que há veículos disponíveis.")
            else:
                st.success("Roteirização executada com sucesso!")

    st.markdown("---")
    st.info("💡 **Dica:** Certifique-se de que os dados de pedidos e frota estão corretos antes de executar a roteirização.")

if __name__ == "__main__":
    resultado = unir_dados_e_roteirizar()
    print("Roteirização concluída:", resultado)
