import streamlit as st
import pandas as pd

def show():
    st.title("Análise de Pedágios não Relacionados a Carregamentos")
    st.write("Faça upload das duas planilhas: Pedágios e Carregamentos.")

    pedagio_file = st.file_uploader("Planilha de Pedágios (Placa, Data de Utilizacao, Valor Cobrado)", type=["csv", "xlsx"])
    carga_file = st.file_uploader("Planilha de Carregamento (Placa, Data Carga)", type=["csv", "xlsx"])

    if pedagio_file and carga_file:
        # Leitura dos arquivos
        if pedagio_file.name.endswith(".csv"):
            df_pedagio = pd.read_csv(pedagio_file, sep=None, engine='python')
        else:
            df_pedagio = pd.read_excel(pedagio_file)
        if carga_file.name.endswith(".csv"):
            df_carga = pd.read_csv(carga_file, sep=None, engine='python')
        else:
            df_carga = pd.read_excel(carga_file)

        # Normalização dos nomes das colunas
        df_pedagio.columns = [c.strip().lower() for c in df_pedagio.columns]
        df_carga.columns = [c.strip().lower() for c in df_carga.columns]

        # Conversão das datas para datetime
        df_pedagio['data de utilizacao'] = pd.to_datetime(df_pedagio['data de utilizacao'], errors='coerce')
        df_carga['data carga'] = pd.to_datetime(df_carga['data carga'], errors='coerce')

        # Mesclar por placa e data
        merged = pd.merge(
            df_pedagio,
            df_carga,
            left_on=['placa', 'data de utilizacao'],
            right_on=['placa', 'data carga'],
            how='left',
            indicator=True
        )
        # Filtrar pedágios sem carregamento correspondente
        pedagios_sem_carga = merged[merged['_merge'] == 'left_only']

        st.subheader("Pedágios sem Carregamento no mesmo dia:")
        if not pedagios_sem_carga.empty:
            placas = sorted(pedagios_sem_carga['placa'].dropna().unique())
            placa_sel = st.multiselect('Filtrar por Placa', placas, default=placas)
            df_filtrado = pedagios_sem_carga[
                pedagios_sem_carga['placa'].isin(placa_sel)
            ]
            st.dataframe(df_filtrado[['placa', 'data de utilizacao', 'valor cobrado']])
            st.download_button(
                "Baixar resultado em CSV",
                df_filtrado[['placa', 'data de utilizacao', 'valor cobrado']].to_csv(index=False).encode('utf-8'),
                file_name="pedagios_sem_carregamento.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum pedágio sem carregamento encontrado.")
    else:
        st.info("Envie as duas planilhas para análise.")
