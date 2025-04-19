import streamlit as st
import pandas as pd
import os
from core.core_frota import cadastrar_veiculo

# Caminho para o arquivo local da base de dados
CAMINHO_BASE_FROTA = "database/frota.csv"
CAMINHO_LOCAL_PARTIDA = "database/local_partida.csv"

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

def carregar_local_partida():
    """
    Carrega o local de partida (endereço e coordenadas).
    """
    if os.path.exists(CAMINHO_LOCAL_PARTIDA):
        return pd.read_csv(CAMINHO_LOCAL_PARTIDA).iloc[0].to_dict()
    else:
        return {"Endereco": "", "Latitude": 0.0, "Longitude": 0.0}

def salvar_local_partida(local_partida):
    """
    Salva o local de partida (endereço e coordenadas).
    """
    os.makedirs(os.path.dirname(CAMINHO_LOCAL_PARTIDA), exist_ok=True)
    pd.DataFrame([local_partida]).to_csv(CAMINHO_LOCAL_PARTIDA, index=False)

def validar_cabecalho_frota(df):
    """
    Valida se a planilha da frota contém os cabeçalhos corretos.
    """
    cabecalhos_esperados = ["Placa", "Transportador", "Descrição Veículo", "Capac. Cx", "Capac. Kg", "Disponível"]
    return all(col in df.columns for col in cabecalhos_esperados)

def pagina_frota():
    st.title("🚚 Cadastro de Frota")
    st.markdown("""
    ### Gerencie os veículos disponíveis:
    - Adicione novos veículos.
    - Atualize informações da frota.
    - Visualize a lista de veículos cadastrados.
    """)

    # Configurar local de partida
    st.markdown("#### Configurar Local de Partida")
    local_partida = carregar_local_partida()
    with st.form("form_local_partida"):
        endereco = st.text_input("Endereço do Local de Partida", value=local_partida["Endereco"])
        latitude = st.number_input("Latitude", value=local_partida["Latitude"], format="%.6f")
        longitude = st.number_input("Longitude", value=local_partida["Longitude"], format="%.6f")
        submit_local_partida = st.form_submit_button("Salvar Local de Partida")

        if submit_local_partida:
            local_partida = {"Endereco": endereco, "Latitude": latitude, "Longitude": longitude}
            salvar_local_partida(local_partida)
            st.success("Local de partida salvo com sucesso!")

    # Carregar base local
    df_frota = carregar_base_local()

    # Remover veículos com placas específicas
    placas_para_remover = ["FLB1111", "FLB2222", "FLB3333", "FLB4444", "FLB5555", 
                           "FLB6666", "FLB7777", "FLB8888", "FLB9999", "CYN1819", "HFU1B60"]
    if not df_frota.empty:
        df_frota = df_frota[~df_frota["Placa"].isin(placas_para_remover)]
        salvar_base_local(df_frota)
        st.success("Veículos com as placas especificadas foram removidos com sucesso!")

    # Upload de planilha da frota
    st.markdown("#### Upload de Planilha da Frota")
    with st.form("form_upload_frota"):
        arquivo_frota = st.file_uploader("Faça upload da planilha da frota", type=["xlsx", "csv"])
        submit_upload = st.form_submit_button("Substituir Base de Dados")

        if submit_upload and arquivo_frota:
            try:
                if arquivo_frota.name.endswith(".xlsx"):
                    df_upload = pd.read_excel(arquivo_frota)
                else:
                    df_upload = pd.read_csv(arquivo_frota)
                
                # Validar cabeçalhos
                if not validar_cabecalho_frota(df_upload):
                    st.error("A planilha não contém os cabeçalhos esperados: Placa, Transportador, Descrição Veículo, Capac. Cx, Capac. Kg, Disponível.")
                else:
                    st.success("Planilha da frota carregada com sucesso!")
                    st.dataframe(df_upload)

                    # Substituir base local com os dados da nova planilha
                    salvar_base_local(df_upload)
                    st.success("Dados da planilha substituíram a base local com sucesso!")
                    df_frota = df_upload  # Atualizar a variável para refletir os novos dados
            except Exception as e:
                st.error(f"Erro ao carregar a planilha: {e}")

    # Dividir a página em duas colunas para melhor organização
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("#### Frota Cadastrada")
        if not df_frota.empty:
            st.dataframe(df_frota, use_container_width=True)
        else:
            st.info("Nenhum veículo cadastrado ainda.")

    with col2:
        st.markdown("#### Ações")
        if st.button("➕ Adicionar Veículo"):
            st.success("Ação de adicionar veículo em desenvolvimento.")
        if st.button("✏️ Editar Veículo"):
            st.success("Ação de editar veículo em desenvolvimento.")
        if st.button("🗑️ Remover Veículo"):
            st.warning("Ação de remover veículo em desenvolvimento.")

    st.markdown("---")
    st.info("💡 **Dica:** Certifique-se de que os dados da frota estão atualizados antes de realizar a roteirização.")

    # Exibir cadastros existentes
    if not df_frota.empty:
        # Formulário para editar um veículo
        st.markdown("#### Editar Veículo")
        placas = df_frota["Placa"].tolist()
        placa_selecionada = st.selectbox("Selecione a placa do veículo para editar", placas)
        if placa_selecionada:
            veiculo_selecionado = df_frota[df_frota["Placa"] == placa_selecionada].iloc[0]
            with st.form("form_editar_veiculo"):
                transportador = st.text_input("Transportador", veiculo_selecionado["Transportador"])
                descricao = st.text_input("Descrição do veículo", veiculo_selecionado["Descrição Veículo"])
                capacidade_kg = st.number_input("Capacidade (Kg)", min_value=0, value=int(veiculo_selecionado["Capac. Kg"]))
                disponivel = st.selectbox("Disponível", ["Sim", "Não"], index=0 if veiculo_selecionado["Disponível"] == "Sim" else 1)
                submit_editar = st.form_submit_button("Salvar Alterações")

                if submit_editar:
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, ["Transportador", "Descrição Veículo", "Capac. Kg", "Disponível"]] = [
                        transportador, descricao, capacidade_kg, disponivel
                    ]
                    salvar_base_local(df_frota)
                    st.success("Alterações salvas com sucesso!")

    # Formulário para cadastro manual
    st.markdown("#### Cadastro Manual de Veículos")
    with st.form("form_frota"):
        placa = st.text_input("Placa do veículo")
        transportador = st.text_input("Transportador")
        descricao = st.text_input("Descrição do veículo")
        capacidade_kg = st.number_input("Capacidade (Kg)", min_value=0)
        disponivel = st.selectbox("Disponível (ex: Sim/Não)", ["Sim", "Não"])
        submit = st.form_submit_button("Salvar")

        if submit:
            veiculo = {
                "Placa": placa,
                "Transportador": transportador,
                "Descrição Veículo": descricao,
                "Capac. Kg": capacidade_kg,
                "Disponível": disponivel
            }
            df_frota = pd.concat([df_frota, pd.DataFrame([veiculo])], ignore_index=True).drop_duplicates(subset=["Placa"])
            salvar_base_local(df_frota)
            st.success(f"Veículo {veiculo['Placa']} cadastrado com sucesso!")
