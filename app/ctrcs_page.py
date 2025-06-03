import streamlit as st
import pandas as pd

def show():
    st.title("Análise de Pagamento de CTRCs")
    st.write("Faça upload de uma planilha extraída do PDF de fechamento de fretes para análise detalhada.")

    file = st.file_uploader("Planilha de CTRCs (extraída do PDF)", type=["csv", "xlsx"])

    if file:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file, sep=None, engine='python')
        else:
            df = pd.read_excel(file)
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
        st.info("Envie uma planilha extraída do PDF para análise.")
