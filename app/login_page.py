import streamlit as st

# Lista de usuários e senhas (pode ser expandida futuramente)
USUARIOS = {
    "Orlando": "Picole2024@"
}

def show():
    st.title("Login - Wazelog")
    st.write("Acesse o sistema com seu usuário e senha.")

    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        if usuario in USUARIOS and senha == USUARIOS[usuario]:
            st.session_state['autenticado'] = True
            st.session_state['usuario'] = usuario
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

    # Botão de logout se já estiver autenticado
    if st.session_state.get('autenticado', False):
        if st.button('Logout'):
            st.session_state['autenticado'] = False
            st.session_state['usuario'] = None
            st.success("Logout realizado com sucesso!")
            st.rerun()

# Função utilitária para checar login antes de acessar as páginas

def checar_login():
    if not st.session_state.get('autenticado', False):
        st.warning("Faça login para acessar o sistema.")
        st.stop()