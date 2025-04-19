import streamlit as st
import pandas as pd
import os

# Caminho para o arquivo local da base de dados
CAMINHO_BASE_FROTA = "database/frota.csv"

def carregar_base_local():
    """
    Carrega a base de dados local da frota.
    """
    if os.path.exists(CAMINHO_BASE_FROTA):
        return pd.read_csv(CAMINHO_BASE_FROTA)
    else:
        return pd.DataFrame(columns=["Placa", "Transportador", "Descrição Veículo", "Capac. Kg", 
                                      "Disponível"])

def salvar_base_local(df):
    """
    Salva a base de dados local da frota.
    """
    os.makedirs(os.path.dirname(CAMINHO_BASE_FROTA), exist_ok=True)
    df.to_csv(CAMINHO_BASE_FROTA, index=False)

def pagina_frota():
    st.title("🚚 Gerenciamento de Frota")
    st.markdown("""
    ### Adicione, edite ou remova veículos da frota.
    """)

    # Carregar dados da frota
    frota_path = "database/frota.csv"
    frota_df = pd.read_csv(frota_path)

    # Exibir tabela interativa
    st.dataframe(frota_df, use_container_width=True)

    # Formulário para adicionar novo veículo
    with st.form("adicionar_veiculo"):
        st.subheader("Adicionar Veículo")
        placa = st.text_input("Placa")
        transportador = st.text_input("Transportador")
        capacidade = st.number_input("Capacidade (kg)", min_value=0)
        disponivel = st.selectbox("Disponível", ["Sim", "Não"])
        submit = st.form_submit_button("Adicionar")

        if submit:
            novo_veiculo = {
                "Placa": placa,
                "Transportador": transportador,
                "Capacidade": capacidade,
                "Disponível": disponivel,
            }
            frota_df = frota_df.append(novo_veiculo, ignore_index=True)
            frota_df.to_csv(frota_path, index=False)
            st.success("Veículo adicionado com sucesso!")

    # Botão para remover veículo
    st.subheader("Remover Veículo")
    placa_remover = st.selectbox("Selecione a placa para remover", frota_df["Placa"].tolist())
    if st.button("Remover"):
        frota_df = frota_df[frota_df["Placa"] != placa_remover]
        frota_df.to_csv(frota_path, index=False)
        st.success("Veículo removido com sucesso!")
