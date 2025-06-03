import streamlit as st
import pandas as pd
import PyPDF2
import re
import os

def extrair_tabela_pdf(pdf_path):
    reader = PyPDF2.PdfReader(pdf_path)
    texto = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    linhas = texto.splitlines()
    dados = []
    preview = []
    # Regexes super tolerantes
    chaves = {
        'placa': r'placa[^\w\d]*([A-Z]{3}-?\d{4})',
        'tipo de veiculo': r'tipo de ve[ií]culo[^\w\d]*([\w\s/]+)',
        'cap. veiculo (kg)': r'cap(acidade)?( do)? ve[ií]culo[^\w\d]*([\d\.]+)\s*kg',
        'peso': r'peso( da)? carga[^\w\d]*([\d\.]+)',
        's frete': r'frete[\w\s:.-]*([\d\.]+,[\d]{2})'
    }
    # Busca todos os campos em todas as linhas e armazena pares campo:valor
    campos_encontrados = {k: [] for k in chaves}
    for idx, linha in enumerate(linhas):
        for campo, padrao in chaves.items():
            m = re.search(padrao, linha, re.IGNORECASE)
            if m:
                valor = m.groups()[-1].strip()
                preview.append(f"Linha {idx+1} | {campo}: {valor}")
                if campo in ['s frete', 'cap. veiculo (kg)', 'peso']:
                    valor = valor.replace('.', '').replace(',', '.')
                campos_encontrados[campo].append(valor)
    # Monta registros combinando os campos encontrados por ordem de aparição
    n = max(len(v) for v in campos_encontrados.values())
    for i in range(n):
        registro = {campo: campos_encontrados[campo][i] if i < len(campos_encontrados[campo]) else '' for campo in chaves}
        # Só adiciona se pelo menos placa e frete existirem
        if registro['placa'] and registro['s frete']:
            dados.append(registro)
    df = pd.DataFrame(dados)
    return df, texto, preview

def show():
    st.title("Análise de Pagamento de CTRCs")
    st.write("Faça upload de uma planilha extraída do PDF de fechamento de fretes para análise detalhada ou envie um PDF.")

    file = st.file_uploader("Planilha de CTRCs (extraída do PDF) ou PDF", type=None, accept_multiple_files=False)

    df = None
    texto_pdf = None
    preview = None
    if file:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file, sep=None, engine='python')
        elif file.name.endswith(".xlsx"):
            df = pd.read_excel(file)
        elif file.name.endswith(".pdf"):
            temp_path = os.path.join('data', 'temp_ctrcs.pdf')
            with open(temp_path, 'wb') as f:
                f.write(file.read())
            df, texto_pdf, preview = extrair_tabela_pdf(temp_path)
            os.remove(temp_path)
        if df is not None and not df.empty:
            df.columns = [c.strip().lower() for c in df.columns]

            # Filtros básicos
            st.sidebar.header("Filtros")
            placas = sorted(df['placa'].dropna().unique())
            placa_sel = st.sidebar.multiselect('Filtrar por Placa', placas, default=placas)
            tipos = sorted(df['tipo de veiculo'].dropna().unique()) if 'tipo de veiculo' in df.columns else []
            tipo_sel = st.sidebar.multiselect('Filtrar por Tipo de Veículo', tipos, default=tipos)
            df_filt = df[df['placa'].isin(placa_sel)]
            if tipo_sel:
                df_filt = df_filt[df_filt['tipo de veiculo'].isin(tipo_sel)]

            st.subheader("Tabela de CTRCs")
            st.dataframe(df_filt)

            # Análise por veículo
            st.subheader("Custo total e percentual por veículo")
            if 's frete' in df_filt.columns:
                df_filt['s frete'] = pd.to_numeric(df_filt['s frete'], errors='coerce').fillna(0)
                resumo = df_filt.groupby(['placa', 'tipo de veiculo', 'cap. veiculo (kg)'], dropna=False)['s frete'].sum().reset_index()
                total = resumo['s frete'].sum()
                resumo['% do total'] = resumo['s frete'] / total * 100
                st.dataframe(resumo)
                st.markdown(f"**Total pago em fretes: R$ {total:,.2f}**")
                st.bar_chart(resumo.set_index('placa')['s frete'])

            # Eficiência de carga
            st.subheader("Eficiência de Carga por Veículo")
            if 'peso' in df_filt.columns and 'cap. veiculo (kg)' in df_filt.columns:
                df_filt['peso'] = pd.to_numeric(df_filt['peso'], errors='coerce').fillna(0)
                df_filt['cap. veiculo (kg)'] = pd.to_numeric(df_filt['cap. veiculo (kg)'], errors='coerce').fillna(0)
                df_filt['aproveitamento'] = (df_filt['peso'] / df_filt['cap. veiculo (kg)']).replace([float('inf'), -float('inf')], 0)
                aproveitamento = df_filt.groupby('placa')['aproveitamento'].mean().reset_index()
                st.dataframe(aproveitamento)
                st.bar_chart(aproveitamento.set_index('placa'))

            # Custo por tonelada transportada
            st.subheader("Custo por Tonelada Transportada")
            if 's frete' in df_filt.columns and 'peso' in df_filt.columns:
                custo_ton = df_filt.groupby('placa').apply(lambda x: x['s frete'].sum() / (x['peso'].sum()/1000) if x['peso'].sum() > 0 else 0).reset_index(name='R$/ton')
                st.dataframe(custo_ton)

            # Ranking de veículos mais caros
            st.subheader("Ranking de Veículos Mais Caros")
            if 's frete' in df_filt.columns:
                ranking = resumo.sort_values('s frete', ascending=False).head(10)
                st.dataframe(ranking)

            # Alertas
            st.subheader("Alertas e Insights")
            if 'aproveitamento' in df_filt.columns:
                baixo_aprov = aproveitamento[aproveitamento['aproveitamento'] < 0.5]
                if not baixo_aprov.empty:
                    st.warning(f"Veículos com baixo aproveitamento de carga (<50%): {', '.join(baixo_aprov['placa'])}")
            if 's frete' in df_filt.columns:
                media = resumo['s frete'].mean()
                acima_media = resumo[resumo['s frete'] > media]
                if not acima_media.empty:
                    st.info(f"Veículos com custo acima da média: {', '.join(acima_media['placa'])}")
        else:
            st.warning("Não foi possível extrair dados estruturados do PDF enviado. Veja abaixo o texto extraído para ajudar no ajuste do layout ou envie um exemplo para suporte.")
            if texto_pdf:
                with st.expander("Texto extraído do PDF (debug)"):
                    st.text(texto_pdf)
                if preview:
                    st.markdown("**Preview das capturas encontradas:**")
                    for p in preview:
                        st.text(p)
    else:
        st.info("Envie uma planilha extraída do PDF ou o próprio PDF para análise.")
