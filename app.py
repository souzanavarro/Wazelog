import streamlit as st
from streamlit_option_menu import option_menu

def main():
    st.set_page_config(
        page_title="Roteirizador Inteligente",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Sidebar com menu de navegação
    with st.sidebar:
        st.image("https://via.placeholder.com/150", use_container_width=True)
        st.title("Menu de Navegação")
        pagina = option_menu(
            menu_title=None,
            options=["Início", "Frota", "Pedidos", "Roteirização", "Configurações"],
            icons=["house", "truck", "box", "map", "gear"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
        )

    # Configuração de tema
    tema = st.sidebar.radio("Escolha o tema:", ["Light", "Dark"])
    if tema == "Dark":
        st.markdown(
            """<style>body { background-color: #121212; color: #ffffff; }</style>""",
            unsafe_allow_html=True,
        )

    # Renderizar páginas
    if pagina == "Início":
        st.title("🌍 Bem-vindo ao Roteirizador Inteligente")
        st.markdown("""
        ### O que você pode fazer aqui:
        - Gerenciar sua frota.
        - Adicionar e editar pedidos.
        - Configurar e executar roteirizações.
        """)
    elif pagina == "Frota":
        from frota import pagina_frota
        pagina_frota()
    elif pagina == "Pedidos":
        from pedidos import pagina_pedidos
        pagina_pedidos()
    elif pagina == "Roteirização":
        from roteirizacao import pagina_roteirizacao
        pagina_roteirizacao()
    elif pagina == "Configurações":
        from roteirizador import pagina_roteirizador
        pagina_roteirizador()

if __name__ == "__main__":
    main()
