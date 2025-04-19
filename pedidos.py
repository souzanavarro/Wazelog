import streamlit as st
import pandas as pd
import os

# Caminho para o arquivo local da base de dados de pedidos
CAMINHO_BASE_PEDIDOS = "database/pedidos.csv"

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

def geocodificar_enderecos(df):
    """
    Combina as colunas de endereço, bairro e cidade para criar um endereço completo.
    """
    if all(col in df.columns for col in ["Endereço de Entrega", "Bairro de Entrega", "Cidade de Entrega"]):
        df["Endereco Completo"] = (
            df["Endereço de Entrega"].fillna("") + ", " +
            df["Bairro de Entrega"].fillna("") + ", " +
            df["Cidade de Entrega"].fillna("")
        )
    else:
        raise ValueError("As colunas 'Endereço de Entrega', 'Bairro de Entrega' e 'Cidade de Entrega' são necessárias.")
    return df

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

def pagina_pedidos():
    st.title("📦 Cadastro de Pedidos")
    st.markdown("""
    ### Gerencie os pedidos disponíveis:
    - Faça upload de uma planilha de pedidos.
    - Visualize a lista de pedidos cadastrados.
    """)

    # Carregar base local
    df_pedidos = carregar_base_pedidos()

    # Dividir a página em duas colunas para melhor organização
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("#### Pedidos Cadastrados")
        if not df_pedidos.empty:
            st.dataframe(df_pedidos, use_container_width=True)
        else:
            st.info("Nenhum pedido cadastrado ainda.")

    with col2:
        st.markdown("#### Ações")
        if st.button("➕ Adicionar Pedido"):
            st.success("Ação de adicionar pedido em desenvolvimento.")
        if st.button("✏️ Editar Pedido"):
            st.success("Ação de editar pedido em desenvolvimento.")
        if st.button("🗑️ Remover Pedido"):
            st.warning("Ação de remover pedido em desenvolvimento.")

    st.markdown("---")
    st.info("💡 **Dica:** Certifique-se de que os pedidos estão corretos antes de iniciar a roteirização.")

    # Upload de planilha de pedidos
    st.markdown("#### Upload de Planilha de Pedidos")
    with st.form("form_upload_pedidos"):
        arquivo_pedidos = st.file_uploader("Faça upload da planilha de pedidos", type=["xlsx", "csv"])
        submit_upload = st.form_submit_button("Substituir Base de Dados")

        if submit_upload and arquivo_pedidos:
            try:
                if arquivo_pedidos.name.endswith(".xlsx"):
                    df_upload = pd.read_excel(arquivo_pedidos)
                else:
                    df_upload = pd.read_csv(arquivo_pedidos)
                
                # Validar cabeçalhos
                if not validar_cabecalho_pedidos(df_upload):
                    st.error("A planilha não contém os cabeçalhos esperados: Nº Pedido, Cód. Cliente, Nome Cliente, Grupo Cliente, Endereço de Entrega, Bairro de Entrega, Cidade de Entrega, Qtde. dos Itens, Peso dos Itens.")
                else:
                    # Adicionar colunas de Endereço Completo e Região
                    df_upload = geocodificar_enderecos(df_upload)
                    df_upload = definir_regiao(df_upload)

                    st.success("Planilha de pedidos carregada com sucesso!")
                    st.dataframe(df_upload)

                    # Substituir base local com os dados da nova planilha
                    salvar_base_pedidos(df_upload)
                    st.success("Dados da planilha substituíram a base local com sucesso!")
                    df_pedidos = df_upload  # Atualizar a variável para refletir os novos dados
            except Exception as e:
                st.error(f"Erro ao carregar a planilha: {e}")
