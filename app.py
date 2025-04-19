# Configurar o modo "Wide" no Streamlit
import streamlit as st
st.set_page_config(layout="wide", page_title="Roteirizador Inteligente", page_icon="🗺️")

from frota import pagina_frota
from pedidos import pagina_pedidos
from roteirizacao import pagina_roteirizacao
from roteirizador import pagina_roteirizador

def main():
    st.sidebar.title("📋 Menu")
    st.sidebar.markdown("---")
    pagina = st.sidebar.radio("Navegue pelas páginas:", ["🏠 Início", "🚚 Frota", "📦 Pedidos", "📍 Roteirização", "⚙️ Roteirizador"])

    st.sidebar.markdown("---")
    st.sidebar.info("💡 **Dica:** Navegue pelas páginas para configurar e otimizar suas rotas.")

    if pagina == "🏠 Início":
        st.title("🗺️ Bem-vindo ao Roteirizador Inteligente")
        st.markdown("""
        ### O que você pode fazer aqui:
        - **Cadastrar frota:** Adicione e gerencie os veículos disponíveis.
        - **Subir pedidos:** Carregue os pedidos para roteirização.
        - **Configurar parâmetros:** Ajuste as configurações para otimizar as rotas.
        - **Visualizar resultados:** Veja as rotas geradas e otimizadas.
        """)

        # Dividir a página em duas colunas para melhor organização
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🚀 Como começar:")
            st.markdown("""
            Use o menu lateral para navegar entre as páginas e realizar as operações desejadas.
            """)

        with col2:
            st.markdown("### 🔄 Resumo Visual do Fluxo:")
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
    elif pagina == "🚚 Frota":
        pagina_frota()
    elif pagina == "📦 Pedidos":
        pagina_pedidos()
    elif pagina == "📍 Roteirização":
        pagina_roteirizacao()
    elif pagina == "⚙️ Roteirizador":
        pagina_roteirizador()

if __name__ == "__main__":
    main()
