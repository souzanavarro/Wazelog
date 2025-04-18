import core.core_frota as frota
import core.core_pedidos as pedidos
import core.core_roteirizador as roteirizador
import core.core_ia as ia
import streamlit as st
import pandas as pd
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
    st.title("Roteirização")
    st.markdown("""
    ### Gere rotas otimizadas:
    - Combine os dados da frota e dos pedidos.
    - Configure os parâmetros de roteirização.
    - Visualize as rotas geradas.
    """)

    caminho_pedidos = st.text_input("Caminho para a planilha de pedidos", "pedidos.xlsx")
    caminho_frota = st.text_input("Caminho para a planilha de frota", "frota.xlsx")

    if st.button("Carregar dados e gerar rotas"):
        # Carregar dados
        dados_frota = carregar_dados_frota()
        dados_pedidos = carregar_dados_pedidos()

        # Verificar disponibilidade dos veículos
        frota_disponivel = verificar_disponibilidade_veiculos(dados_frota)

        # Geocodificar endereços (se necessário) e definir regiões
        try:
            dados_pedidos = geocodificar_enderecos(dados_pedidos, "Endereco Completo")
            dados_pedidos = definir_regiao(dados_pedidos, "Regiao")
            st.success("Endereços completos e regiões definidos com sucesso!")
        except ValueError as e:
            st.error(f"Erro ao processar os dados: {e}")

        # Clusterizar pedidos
        dados_pedidos = clusterizar_pedidos_kmeans(dados_pedidos, n_clusters=5)

        # Priorizar clusters
        dados_pedidos = priorizar_clusters(dados_pedidos, criterio="peso_total")

        # Distribuir carga por veículo
        alocacao = distribuir_carga_por_veiculo(dados_pedidos, frota_disponivel, criterio="peso_total")
        st.write("Distribuição de carga por veículo:")
        st.json(alocacao)

        # Exibir clusters no Streamlit
        st.write("Pedidos clusterizados:")
        st.dataframe(dados_pedidos)

        # Otimizar rotas para cada veículo
        dados_roteirizacao = {
            "distancias": [],  # Matriz de distâncias (preencher com dados reais)
            "veiculos": len(frota_disponivel),
            "deposito": 0,  # Índice do depósito
            "demandas": [],  # Demandas por ponto (preencher com dados reais)
            "capacidades": [veiculo["Capacidade (Kg)"] for veiculo in frota_disponivel],
            "janelas_tempo": []  # Janelas de tempo (preencher com dados reais)
        }
        rotas_otimizadas = otimizar_rota(dados_roteirizacao, parametros={})
        st.write("Rotas otimizadas:", rotas_otimizadas)

        # Gerar visualização no mapa
        mapa = gerar_mapa_rotas(rotas_otimizadas, dados_pedidos)
        st.markdown("### Visualização das Rotas")
        st.components.v1.html(mapa._repr_html_(), height=600)

        # Exportar rotas para Excel
        if st.button("Exportar Rotas para Excel"):
            exportar_rotas_excel(rotas_otimizadas, dados_pedidos)
            st.success("Rotas exportadas para Excel com sucesso!")

        # Salvar no histórico
        if st.button("Salvar no Histórico"):
            salvar_historico(rotas_otimizadas, dados_pedidos)
            st.success("Rotas salvas no histórico com sucesso!")

        # Continuar com a roteirização
        resultado = fluxo_completo(caminho_pedidos, caminho_frota)
        st.write("Rotas geradas:", resultado["rotas"])
        st.write("Métricas de performance:", resultado["performance"])

if __name__ == "__main__":
    resultado = unir_dados_e_roteirizar()
    print("Roteirização concluída:", resultado)
