import streamlit as st
import pandas as pd
import plotly.express as px

# Configurar o modo "Wide" no Streamlit
st.set_page_config(layout="wide", page_title="Inteligência Artificial", page_icon="🤖")

def pagina_ia():
    st.title("🤖 Inteligência Artificial")
    st.markdown("""
    ### Treine modelos e visualize previsões de atrasos.
    """)

    # Dados fictícios para demonstração
    historico = pd.DataFrame({
        "Distância": [10, 20, 30, 40],
        "Tempo Estimado": [15, 25, 35, 45],
        "Atraso": [5, 10, 15, 20],
    })

    # Gráfico de dispersão
    fig = px.scatter(historico, x="Distância", y="Atraso", size="Tempo Estimado", color="Atraso",
                     template="plotly_white", title="Relação entre Distância e Atraso")
    st.plotly_chart(fig, use_container_width=True)

    # Botão para treinar modelo
    if st.button("Treinar Modelo"):
        st.success("Modelo treinado com sucesso!")
