import streamlit as st
import pandas as pd
import PyPDF2
import re
import os
import unicodedata

def normaliza(s):
    return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('ASCII')

def extrair_ctrcs_pdf(pdf_path):
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        texto = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        linhas = texto.splitlines()
        preview = []
        linhas_norm = [normaliza(l) for l in linhas]
        texto_unico = " ".join(linhas_norm)
        # Regex para cabeçalho de bloco
        padrao_topo = re.compile(r"Placa:\s*([A-Z0-9-]+).*?Tipo de ve[ií]culo\s*:?[\s]*([\w\s/]+).*?Cap[\.]?(acidade)?(\s*de)? Ve[ií]culo\s*:?[\s]*([\d\.]+)\s*KG", re.IGNORECASE)
        # Regex para encontrar linhas de CTRC (busca data e valores na linha)
        padrao_data = re.compile(r"(\d{2}/\d{2}/\d{4})")
        padrao_peso_carga = re.compile(r"Peso Carga:?\s*([\d\.]+)")
        padrao_frete_ap = re.compile(r"Valor da carga na AP\s*[:]??\s*([\d\.,]+)")
        padrao_carga = re.compile(r"Carga:?\s*([\d\.]+)")
        dados = []
        bloco = {'Placa': '', 'Tipo de Veiculo': '', 'Cap. Veiculo (KG)': ''}
        registros_bloco = []
        peso_carga_bloco = None
        frete_ap_bloco = None
        carga_bloco = None
        for idx, linha in enumerate(linhas_norm):
            m_topo = padrao_topo.search(linha)
            if m_topo:
                # Salva registros do bloco anterior, preenchendo Frete e Peso Carga
                if registros_bloco:
                    for r in registros_bloco:
                        r['Valor da carga na AP'] = frete_ap_bloco if frete_ap_bloco is not None else ''
                        r['Peso Carga'] = peso_carga_bloco if peso_carga_bloco is not None else ''
                        r['Carga'] = carga_bloco if carga_bloco is not None else ''
                        dados.append(r)
                    registros_bloco = []
                bloco['Placa'] = m_topo.group(1)
                bloco['Tipo de Veiculo'] = m_topo.group(2).strip()
                bloco['Cap. Veiculo (KG)'] = m_topo.group(5).replace('.', '')
                peso_carga_bloco = None
                frete_ap_bloco = None
                carga_bloco = None
                preview.append(f"Linha {idx+1} | NOVO BLOCO: Placa: {bloco['Placa']} | Tipo: {bloco['Tipo de Veiculo']} | Cap: {bloco['Cap. Veiculo (KG)']}")
            m_peso_carga = padrao_peso_carga.search(linha)
            if m_peso_carga:
                peso_carga_bloco = float(m_peso_carga.group(1).replace('.', ''))
                preview.append(f"Linha {idx+1} | Peso Carga detectado: {peso_carga_bloco}")
            m_frete_ap = padrao_frete_ap.search(linha)
            if m_frete_ap:
                frete_ap_bloco = float(m_frete_ap.group(1).replace('.', '').replace(',', '.'))
                preview.append(f"Linha {idx+1} | Frete AP detectado: {frete_ap_bloco}")
            m_carga = padrao_carga.search(linha)
            if m_carga:
                carga_bloco = m_carga.group(1)
                preview.append(f"Linha {idx+1} | Carga detectada: {carga_bloco}")
            if padrao_data.search(linha) and bloco['Placa']:
                valores = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", linha)
                numeros = re.findall(r"\d{3,}", linha)
                if len(numeros) >= 1:
                    peso_str = numeros[-1].replace('.', '')
                    peso = float(peso_str) if peso_str.isdigit() else 0
                else:
                    peso = 0
                registro = {
                    'Placa': bloco['Placa'],
                    'Tipo de Veiculo': bloco['Tipo de Veiculo'],
                    'Cap. Veiculo (KG)': bloco['Cap. Veiculo (KG)'],
                    'Carga': carga_bloco if carga_bloco is not None else '',
                    'Valor da carga na AP': '',  # será preenchido ao fechar o bloco
                    'Peso Carga': ''  # será preenchido ao fechar o bloco
                }
                preview.append(f"Linha {idx+1} | Peso Carga: {peso_carga_bloco} | Valor da carga na AP: {frete_ap_bloco}")
                registros_bloco.append(registro)
        # Ao final, salva o último bloco
        if registros_bloco:
            for r in registros_bloco:
                r['Valor da carga na AP'] = frete_ap_bloco if frete_ap_bloco is not None else ''
                r['Peso Carga'] = peso_carga_bloco if peso_carga_bloco is not None else ''
                r['Carga'] = carga_bloco if carga_bloco is not None else ''
                dados.append(r)
        if not dados:
            raise ValueError('Nenhum registro CTRC encontrado no PDF.')
        df = pd.DataFrame(dados)
        return df, preview, None
    except Exception as e:
        return None, [], str(e)

def extrair_ctrcs_csv(file):
    try:
        df = pd.read_csv(file, sep=None, engine='python')
        return df, None
    except Exception as e:
        return None, str(e)

def show():
    st.title('Conversor e Análise de CTRCs (PDF/CSV)')
    st.write('Faça upload de um PDF de fechamento de fretes ou de um arquivo CSV já convertido.')

    file = st.file_uploader('Envie o PDF ou CSV', type=['pdf', 'csv'])
    erro = None
    df = None
    preview = []

    if file:
        nome = file.name.lower()
        if nome.endswith('.pdf'):
            temp_path = os.path.join('data', 'temp_ctrcs.pdf')
            with open(temp_path, 'wb') as f:
                f.write(file.read())
            df, preview, erro = extrair_ctrcs_pdf(temp_path)
            os.remove(temp_path)
            if df is not None:
                # Oferece download do CSV convertido
                csv_convertido = os.path.join('data', 'CTRCs_CONVERTIDO.csv')
                df.to_csv(csv_convertido, index=False)
                with open(csv_convertido, 'rb') as f:
                    st.download_button('Baixar CSV convertido', f, file_name='CTRCs_CONVERTIDO.csv')
        elif nome.endswith('.csv'):
            df, erro = extrair_ctrcs_csv(file)
        else:
            erro = f'Formato de arquivo não suportado: {file.name}'

        if erro:
            st.error(f'Erro ao processar arquivo: {erro}')
        elif df is not None and not df.empty:
            st.success('Arquivo processado com sucesso!')
            # Exibe apenas as colunas desejadas
            colunas_exibir = [c for c in ['Placa', 'Tipo de Veiculo', 'Cap. Veiculo (KG)', 'Carga', 'Peso Carga', 'Valor da carga na AP'] if c in df.columns]
            st.dataframe(df[colunas_exibir])
            # Relatórios automáticos
            st.header('Relatórios e Análises')
            # Custo total
            if 'Valor da carga na AP' in df.columns:
                df['Valor da carga na AP'] = df['Valor da carga na AP'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                total_frete = pd.to_numeric(df['Valor da carga na AP'], errors='coerce').sum()
                st.metric('Total pago em fretes', f'R$ {total_frete:,.2f}')
            # Custo por Carga (agrupamento único)
            if 'Carga' in df.columns and 'Valor da carga na AP' in df.columns:
                por_carga = df.drop_duplicates('Carga')[['Carga', 'Valor da carga na AP']].copy()
                por_carga['Valor da carga na AP'] = por_carga['Valor da carga na AP'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                por_carga['Valor da carga na AP'] = pd.to_numeric(por_carga['Valor da carga na AP'], errors='coerce')
                def formatar_moeda(valor):
                    if pd.isna(valor):
                        return ''
                    return f"R$ {valor:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')
                por_carga['Valor da carga na AP'] = por_carga['Valor da carga na AP'].apply(formatar_moeda)
                por_carga = por_carga.sort_values('Valor da carga na AP', ascending=False)
                st.subheader('Valor por Carga (único por viagem/bloco)')
                st.dataframe(por_carga)
            # Eficiência de carga e agrupamento correto por bloco (Peso Carga)
            if 'Peso Carga' in df.columns and 'Cap. Veiculo (KG)' in df.columns and 'Carga' in df.columns:
                df['Peso Carga'] = pd.to_numeric(df['Peso Carga'], errors='coerce').fillna(0)
                df['Cap. Veiculo (KG)'] = pd.to_numeric(df['Cap. Veiculo (KG)'], errors='coerce').fillna(0)
                df['Valor da carga na AP'] = pd.to_numeric(df['Valor da carga na AP'], errors='coerce').fillna(0)
                clientes_paletizados = ['CARREFOUR', 'TRIMAIS', 'JBS', 'ANDORINHA', 'WALMART']
                agrupadores = ['Carga', 'Placa', 'Cap. Veiculo (KG)', 'Tipo de Veiculo', 'Peso Carga', 'Valor da carga na AP']
                if 'Regiao' in df.columns:
                    agrupadores.append('Regiao')
                if 'Destino' in df.columns:
                    agrupadores.append('Destino')
                if 'Data' in df.columns:
                    agrupadores.append('Data')
                agg_dict = {}
                for col in ['Tipo de Veiculo', 'Regiao', 'Destino', 'Data']:
                    if col in df.columns and col not in agrupadores:
                        agg_dict[col] = 'first'
                if agg_dict:
                    viagens = df.groupby(agrupadores).agg(agg_dict).reset_index()
                else:
                    viagens = df.groupby(agrupadores).first().reset_index()
                viagens['Aproveitamento'] = viagens['Peso Carga'] / viagens['Cap. Veiculo (KG)']
                if 'Destino' in viagens.columns:
                    viagens['Paletizado'] = viagens['Destino'].str.upper().apply(lambda x: any(c in x for c in clientes_paletizados))
                    viagens.loc[viagens['Paletizado'], 'Aproveitamento'] = 1.0
                viagens['Aproveitamento (%)'] = (viagens['Aproveitamento'] * 100).round(2)
                if 'Destino' in viagens.columns:
                    st.subheader('Aproveitamento de carga por viagem (bloco do PDF)')
                    st.dataframe(viagens[['Carga', 'Placa', 'Tipo de Veiculo', 'Cap. Veiculo (KG)', 'Peso Carga', 'Destino', 'Aproveitamento (%)', 'Valor da carga na AP', 'Paletizado']].style.apply(lambda row: ['background-color: #ffe599' if row['Paletizado'] else '' for _ in row], axis=1))
                else:
                    st.subheader('Aproveitamento de carga por viagem (bloco do PDF)')
                    st.dataframe(viagens[['Carga', 'Placa', 'Tipo de Veiculo', 'Cap. Veiculo (KG)', 'Peso Carga', 'Aproveitamento (%)', 'Valor da carga na AP']])
                viagens['R$/kg'] = viagens.apply(lambda x: x['Valor da carga na AP']/x['Peso Carga'] if x['Peso Carga'] > 0 else 0, axis=1)
                st.subheader('Custo por kilo transportado (por viagem/bloco)')
                st.dataframe(viagens[['Carga', 'Placa', 'Destino' if 'Destino' in viagens.columns else agrupadores[-1], 'R$/kg', 'Peso Carga', 'Valor da carga na AP']])
                st.markdown(f"**Total de kilos transportados (todas as viagens):** {viagens['Peso Carga'].sum():,.0f} kg")
                ranking = viagens.sort_values('Valor da carga na AP', ascending=False).head(10)
                st.subheader('Ranking de viagens mais caras (bloco do PDF)')
                st.dataframe(ranking[['Carga', 'Placa', 'Destino' if 'Destino' in viagens.columns else agrupadores[-1], 'Valor da carga na AP', 'Peso Carga']])
                st.subheader('Alertas e Insights')
                baixo_aprov = viagens[viagens['Aproveitamento'] < 0.5]
                if not baixo_aprov.empty:
                    tabela_baixo = baixo_aprov[['Carga', 'Placa', 'Destino' if 'Destino' in viagens.columns else agrupadores[-1], 'Aproveitamento', 'Paletizado' if 'Paletizado' in baixo_aprov.columns else None]].copy()
                    tabela_baixo['Aproveitamento (%)'] = (tabela_baixo['Aproveitamento'] * 100).round(2)
                    st.markdown('**Viagens com baixo aproveitamento de carga (<50%)**')
                    st.dataframe(tabela_baixo, use_container_width=True)
            # Ranking
            if 'Valor da carga na AP' in df.columns:
                ranking = por_veiculo.head(10)
                st.subheader('Ranking de veículos mais caros')
                st.dataframe(ranking)
            # Alertas
            st.subheader('Alertas e Insights')
            if 'Aproveitamento' in df.columns:
                if 'Destino' in df.columns:
                    baixo_aprov = aproveitamento[(aproveitamento['Aproveitamento'] < 0.5)]
                    if not baixo_aprov.empty:
                        tabela_baixo = baixo_aprov[['Placa', 'Destino', 'Aproveitamento', 'Paletizado']].copy()
                        tabela_baixo['Aproveitamento (%)'] = (tabela_baixo['Aproveitamento'] * 100).round(2)
                        tabela_baixo = tabela_baixo[['Placa', 'Destino', 'Aproveitamento (%)', 'Paletizado']]
                        st.markdown('**Veículos com baixo aproveitamento de carga (<50%)**')
                        st.dataframe(tabela_baixo.style.apply(lambda row: ['background-color: #ffe599' if row['Paletizado'] else '' for _ in row], axis=1), use_container_width=True)
                else:
                    baixo_aprov = aproveitamento[aproveitamento['Aproveitamento'] < 0.5]
                    if not baixo_aprov.empty:
                        tabela_baixo = baixo_aprov[['Placa', 'Aproveitamento']].copy()
                        tabela_baixo['Aproveitamento (%)'] = (tabela_baixo['Aproveitamento'] * 100).round(2)
                        tabela_baixo = tabela_baixo[['Placa', 'Aproveitamento (%)']]
                        st.markdown('**Veículos com baixo aproveitamento de carga (<50%)**')
                        st.dataframe(tabela_baixo, use_container_width=True)
            if 'Valor da carga na AP' in df.columns:
                media = por_veiculo['Valor da carga na AP'].mean()
                acima_media = por_veiculo[por_veiculo['Valor da carga na AP'] > media]
                if not acima_media.empty:
                    if 'Destino' in df.columns and 'Destino' in df:
                        tabela_custo = df[df['Placa'].isin(acima_media['Placa'])][['Placa', 'Destino', 'Valor da carga na AP']].copy()
                        tabela_custo['Paletizado'] = tabela_custo['Destino'].str.upper().apply(lambda x: any(c in x for c in clientes_paletizados))
                        tabela_custo['Valor da carga na AP'] = pd.to_numeric(tabela_custo['Valor da carga na AP'], errors='coerce').round(2)
                        st.markdown('**Veículos com custo acima da média**')
                        st.dataframe(tabela_custo.style.apply(lambda row: ['background-color: #ffe599' if row['Paletizado'] else '' for _ in row], axis=1), use_container_width=True)
                    else:
                        tabela_custo = acima_media[['Placa', 'Valor da carga na AP']].copy()
                        tabela_custo['Valor da carga na AP'] = pd.to_numeric(tabela_custo['Valor da carga na AP'], errors='coerce').round(2)
                        st.markdown('**Veículos com custo acima da média**')
                        st.dataframe(tabela_custo, use_container_width=True)
            # Preview do parser
            if preview:
                st.markdown('**Preview das capturas encontradas:**')
                st.code("\n".join(preview), language='text')
        else:
            st.warning('Nenhum dado extraído do arquivo enviado.')
    else:
        st.info('Envie um PDF ou CSV para iniciar a análise/conversão.')
