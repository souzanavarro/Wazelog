# Configurar o modo "Wide" no Streamlit
import streamlit as st
st.set_page_config(layout="wide")

from frota import pagina_frota
from pedidos import pagina_pedidos
from roteirizacao import pagina_roteirizacao

def main():
    st.sidebar.title("Menu")
    pagina = st.sidebar.radio("Navegue pelas páginas:", ["Início", "Frota", "Pedidos", "Roteirização"])

    if pagina == "Início":
        st.title("Bem-vindo ao Roteirizador Inteligente")
        st.markdown("""
        ### O que você pode fazer aqui:
        - **Cadastrar frota:** Adicione e gerencie os veículos disponíveis.
        - **Subir pedidos:** Carregue os pedidos para roteirização.
        - **Configurar parâmetros:** Ajuste as configurações para otimizar as rotas.
        - **Visualizar resultados:** Veja as rotas geradas e otimizadas.

        ### Como começar:
        Use o menu lateral para navegar entre as páginas e realizar as operações desejadas.
        """)

        st.markdown("### Resumo Visual do Fluxo:")
        st.markdown("""
        ```
        Importar Pedidos
             ↓
        Geocodificar Endereços
             ↓
        Separar por Região (Clustering)
             ↓
        Distribuir Carga por Veículo
             ↓
        Otimizar Rota Interna
             ↓
        Gerar Mapa e Exportar
             ↓
        Salvar no Histórico para IA
        ```
        """)
    elif pagina == "Frota":
        pagina_frota()
    elif pagina == "Pedidos":
        pagina_pedidos()
    elif pagina == "Roteirização":
        pagina_roteirizacao()

if __name__ == "__main__":
    main()
