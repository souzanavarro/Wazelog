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

        # Normalização dos nomes das colunas para manter a primeira letra maiúscula
        df_pedagio.columns = [c.strip().capitalize() for c in df_pedagio.columns]
        df_carga.columns = [c.strip().capitalize() for c in df_carga.columns]

        # Ajuste para garantir que as colunas obrigatórias existam na planilha de pedágios
        colunas_esperadas = [
            'Placa', 'Data de utilizacao', 'Hora de untrada',
            'Nome do estabelecimento', 'Endereco do estabelecimento',
            'Valor cobrado', 'Informacao 1'
        ]
        for col in colunas_esperadas:
            if col not in df_pedagio.columns:
                st.error(f"Coluna obrigatória não encontrada na planilha de pedágios: {col}")
                return

        # Ajuste para garantir que as colunas obrigatórias existam na planilha de carregamento
        colunas_carga_esperadas = ['Placa', 'Data carga', 'Transportador']
        for col in colunas_carga_esperadas:
            if col not in df_carga.columns:
                st.error(f"Coluna obrigatória não encontrada na planilha de carregamento: {col}")
                return

        # Conversão das datas para datetime
        df_pedagio['Data de utilizacao'] = pd.to_datetime(df_pedagio['Data de utilizacao'], errors='coerce')
        df_carga['Data carga'] = pd.to_datetime(df_carga['Data carga'], errors='coerce')

        # Seleciona apenas as colunas necessárias da planilha de pedágios
        colunas_uteis = [
            'Placa', 'Data de utilizacao', 'Hora de untrada',
            'Nome do estabelecimento', 'Endereco do estabelecimento',
            'Valor cobrado', 'Informacao 1'
        ]
        df_pedagio = df_pedagio[[col for col in colunas_uteis if col in df_pedagio.columns]]

        # Ajuste para aceitar 'Placa Veiculo' como nome alternativo para 'Placa' na planilha de carregamento
        if 'Placa Veiculo' in df_carga.columns and 'Placa' not in df_carga.columns:
            df_carga = df_carga.rename(columns={'Placa Veiculo': 'Placa'})

        # Mesclar por placa e data
        merged = pd.merge(
            df_pedagio,
            df_carga,
            left_on=['Placa', 'Data de utilizacao'],
            right_on=['Placa', 'Data carga'],
            how='left',
            indicator=True,
            suffixes=('', '_carga')
        )
        pedagios_sem_carga = merged[merged['_merge'] == 'left_only'].copy()

        # Preencher transportador: busca na planilha de carregamento pelo último transportador da placa, se não achar busca na frota, senão 'Desconhecido'
        try:
            df_frota = pd.read_csv('data/Frota.csv')
            df_frota.columns = [c.strip().capitalize() for c in df_frota.columns]
        except Exception:
            df_frota = None

        def buscar_transportador(row):
            placa = row['Placa']
            data_pedagio = row['Data de utilizacao']
            # Busca o último transportador da placa na planilha de carga
            cargas_placa = df_carga[df_carga['Placa'] == placa]
            cargas_placa = cargas_placa[cargas_placa['Data carga'] <= data_pedagio]
            if not cargas_placa.empty:
                carga_mais_recente = cargas_placa.sort_values('Data carga', ascending=False).iloc[0]
                return carga_mais_recente['Transportador']
            # Busca na frota
            if df_frota is not None and placa in df_frota['Placa'].values:
                return df_frota[df_frota['Placa'] == placa]['Transportador'].iloc[0]
            return 'Desconhecido'

        pedagios_sem_carga['Transportador'] = pedagios_sem_carga.apply(buscar_transportador, axis=1)

        st.subheader("Pedágios sem Carregamento no mesmo dia:")
        if not pedagios_sem_carga.empty:
            transportadores = sorted(pedagios_sem_carga['Transportador'].unique())
            transportadores = ['Desconhecido'] + [t for t in transportadores if t != 'Desconhecido']
            transportador_sel = st.selectbox('Filtrar por Transportador', transportadores)
            if transportador_sel == 'Desconhecido':
                df_filtrado = pedagios_sem_carga.copy()
            else:
                df_filtrado = pedagios_sem_carga[
                    pedagios_sem_carga['Transportador'] == transportador_sel
                ]
            # Conversão segura do valor cobrado
            df_filtrado['Valor cobrado'] = (
                df_filtrado['Valor cobrado']
                .astype(str)
                .str.replace('R$', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            df_filtrado['Valor cobrado'] = pd.to_numeric(df_filtrado['Valor cobrado'], errors='coerce').fillna(0)
            soma_float = df_filtrado['Valor cobrado'].sum()
            # Padroniza os nomes das colunas para .title() antes de exibir/exportar
            df_filtrado.columns = [c.title() for c in df_filtrado.columns]
            colunas_exibir = [
                'Placa', 'Data De Utilizacao', 'Hora De Untrada',
                'Nome Do Estabelecimento', 'Endereco Do Estabelecimento',
                'Valor Cobrado', 'Informacao 1', 'Transportador'
            ]
            # Formata a coluna de data para exibir apenas a data no formato dd-mm-aaaa
            if 'Data De Utilizacao' in df_filtrado.columns:
                df_filtrado['Data De Utilizacao'] = pd.to_datetime(df_filtrado['Data De Utilizacao'], errors='coerce').dt.strftime('%d-%m-%Y')
            # Formata a coluna Valor Cobrado para exibir como R$
            if 'Valor Cobrado' in df_filtrado.columns:
                df_filtrado['Valor Cobrado'] = df_filtrado['Valor Cobrado'].apply(lambda x: f"R$ {x:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))
            # Ordena por Transportador, Placa e Data De Utilizacao
            df_filtrado = df_filtrado.sort_values(['Transportador', 'Placa', 'Data De Utilizacao'])

            # Gera relatório agrupado por transportadora, com total ao final de cada grupo
            relatorio = []
            for transportadora, grupo in df_filtrado.groupby('Transportador', sort=False):
                relatorio.append(grupo)
                # Converte 'Valor Cobrado' para float para somar corretamente
                valores_float = grupo['Valor Cobrado'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                valores_float = pd.to_numeric(valores_float, errors='coerce').fillna(0)
                total = valores_float.sum()
                linha_total = {col: '' for col in grupo.columns}
                linha_total['Transportador'] = f"Total {transportadora}"
                linha_total['Valor Cobrado'] = f"R$ {total:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ',')
                relatorio.append(pd.DataFrame([linha_total]))
            relatorio_df = pd.concat(relatorio, ignore_index=True)

            # Exportação e exibição
            st.dataframe(df_filtrado[colunas_exibir])

            # Tabela de totais por transportador
            totais_por_transportador = df_filtrado.copy()
            totais_por_transportador['Valor Cobrado'] = (
                totais_por_transportador['Valor Cobrado']
                .astype(str)
                .str.replace('R$', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            totais_por_transportador['Valor Cobrado'] = pd.to_numeric(totais_por_transportador['Valor Cobrado'], errors='coerce').fillna(0)
            totais = (
                totais_por_transportador.groupby('Transportador', as_index=False)['Valor Cobrado']
                .sum()
                .sort_values('Valor Cobrado', ascending=False)
            )
            totais['Valor Cobrado'] = totais['Valor Cobrado'].apply(lambda x: f"R$ {x:,.2f}".replace('.', 'X').replace(',', '.').replace('X', ','))
            st.markdown('**Total de pedágios indevidos por Transportador:**')
            st.dataframe(totais.rename(columns={'Valor Cobrado': 'Total Pedágios Indevidos'}))

            # Adiciona três linhas: em branco, total geral, em branco
            st.markdown('<br>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-weight:bold;">Total de pedágios indevidos para o transportador: R$ {soma_float:,.2f}</div>', unsafe_allow_html=True)
            st.markdown('<br>', unsafe_allow_html=True)

            if transportador_sel == 'Desconhecido':
                st.markdown(f"**Total de pedágios indevidos para TODOS os transportadores: R$ {soma_float:,.2f}**")
                # Monta CSV agrupado por transportador, com linhas em branco e total ao final de cada grupo
                import io
                csv_buffer = io.StringIO()
                for transportador, grupo in df_filtrado.groupby('Transportador', sort=False):
                    grupo[colunas_exibir].to_csv(csv_buffer, index=False, header=True)
                    csv_buffer.write('\n')
                    # Soma dos valores desse transportador
                    valores_float = grupo['Valor Cobrado'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                    valores_float = pd.to_numeric(valores_float, errors='coerce').fillna(0)
                    total = valores_float.sum()
                    csv_buffer.write(f'Total de pedágios indevidos para o transportador {transportador}:,R$ {total:,.2f}\n')
                    csv_buffer.write('\n')
                # Soma geral de todos os transportadores
                soma_geral = df_filtrado['Valor Cobrado'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                soma_geral = pd.to_numeric(soma_geral, errors='coerce').fillna(0).sum()
                # Referência ao mês do relatório
                try:
                    datas = pd.to_datetime(df_filtrado['Data De Utilizacao'], errors='coerce')
                    mes_ano = datas.dt.strftime('%m/%Y').dropna().unique()
                    referencia = ', '.join(sorted(set(mes_ano))) if len(mes_ano) > 0 else 'Indefinido'
                except Exception:
                    referencia = 'Indefinido'
                csv_buffer.write(f'Referência do relatório (mês/ano):,{referencia}\n')
                csv_buffer.write(f'Total de pedágios indevidos para TODOS os transportadores:,R$ {soma_geral:,.2f}\n')
                csv_buffer.write('Relatório gerado por Orlando Navarro\n')
                st.download_button(
                    "Baixar resultado em CSV",
                    csv_buffer.getvalue().encode('utf-8'),
                    file_name="pedagios_sem_carregamento_todos.csv",
                    mime="text/csv"
                )
            else:
                st.markdown(f"**Total de pedágios indevidos para {transportador_sel}: R$ {soma_float:,.2f}**")
                st.download_button(
                    "Baixar resultado em CSV",
                    df_filtrado[colunas_exibir].to_csv(index=False).encode('utf-8'),
                    file_name=f"pedagios_sem_carregamento_{transportador_sel}.csv",
                    mime="text/csv"
                )
        else:
            st.info("Nenhum pedágio sem carregamento encontrado.")
    else:
        st.info("Envie as duas planilhas para análise.")
