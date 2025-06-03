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

        # Carrega a frota para mapear placas para transportador
        try:
            df_frota = pd.read_csv('data/Frota.csv')
            df_frota.columns = [c.strip().lower() for c in df_frota.columns]
        except Exception as e:
            st.warning(f"Erro ao carregar Frota.csv: {e}")
            df_frota = None

        # Junta transportador nas placas dos pedágios
        if df_frota is not None:
            df_pedagio = pd.merge(
                df_pedagio,
                df_frota[['placa', 'transportador']],
                on='placa',
                how='left'
            )
            df_pedagio['transportador'] = df_pedagio['transportador'].fillna('Analisar Transportador')
        else:
            df_pedagio['transportador'] = 'Analisar Transportador'

        # Mesclar por placa e data
        merged = pd.merge(
            df_pedagio,
            df_carga,
            left_on=['placa', 'data de utilizacao'],
            right_on=['placa', 'data carga'],
            how='left',
            indicator=True
        )
        pedagios_sem_carga = merged[merged['_merge'] == 'left_only']

        st.subheader("Pedágios sem Carregamento no mesmo dia:")
        if not pedagios_sem_carga.empty:
            transportadores = sorted(pedagios_sem_carga['transportador'].fillna('Desconhecido').unique())
            transportadores = ['Desconhecido'] + [t for t in transportadores if t != 'Desconhecido']
            transportador_sel = st.selectbox('Filtrar por Transportador', transportadores)
            if transportador_sel == 'Desconhecido':
                # Mostra todos os transportadores e soma total
                df_filtrado = pedagios_sem_carga.copy()
                # Conversão segura do valor cobrado
                df_filtrado['valor cobrado'] = (
                    df_filtrado['valor cobrado']
                    .astype(str)
                    .str.replace('R$', '', regex=False)
                    .str.replace('.', '', regex=False)
                    .str.replace(',', '.', regex=False)
                    .str.strip()
                )
                df_filtrado['valor cobrado'] = pd.to_numeric(df_filtrado['valor cobrado'], errors='coerce').fillna(0)
                soma_float = df_filtrado['valor cobrado'].sum()
                st.dataframe(df_filtrado[['placa', 'data de utilizacao', 'valor cobrado', 'transportador']])
                st.markdown(f"**Total de pedágios indevidos para TODOS os transportadores: R$ {soma_float:,.2f}**")
                st.download_button(
                    "Baixar resultado em CSV",
                    df_filtrado[['placa', 'data de utilizacao', 'valor cobrado', 'transportador']].to_csv(index=False).encode('utf-8'),
                    file_name="pedagios_sem_carregamento_todos.csv",
                    mime="text/csv"
                )
            else:
                df_filtrado = pedagios_sem_carga[
                    pedagios_sem_carga['transportador'] == transportador_sel
                ]
                df_filtrado['valor cobrado'] = (
                    df_filtrado['valor cobrado']
                    .astype(str)
                    .str.replace('R$', '', regex=False)
                    .str.replace('.', '', regex=False)
                    .str.replace(',', '.', regex=False)
                    .str.strip()
                )
                df_filtrado['valor cobrado'] = pd.to_numeric(df_filtrado['valor cobrado'], errors='coerce').fillna(0)
                soma_float = df_filtrado['valor cobrado'].sum()
                st.dataframe(df_filtrado[['placa', 'data de utilizacao', 'valor cobrado', 'transportador']])
                st.markdown(f"**Total de pedágios indevidos para {transportador_sel}: R$ {soma_float:,.2f}**")
                st.download_button(
                    "Baixar resultado em CSV",
                    df_filtrado[['placa', 'data de utilizacao', 'valor cobrado', 'transportador']].to_csv(index=False).encode('utf-8'),
                    file_name=f"pedagios_sem_carregamento_{transportador_sel}.csv",
                    mime="text/csv"
                )
        else:
            st.info("Nenhum pedágio sem carregamento encontrado.")
    else:
        st.info("Envie as duas planilhas para análise.")
