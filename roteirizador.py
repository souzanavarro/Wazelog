import streamlit as st

def pagina_roteirizador():
    st.title("⚙️ Configurações do Roteirizador")
    st.markdown("""
    ### Configure os parâmetros para a roteirização:
    - Escolha o critério de otimização.
    - Defina restrições e preferências.
    """)

    # Adicionar uma caixa de informações no topo
    st.info("⚡ Configure os parâmetros abaixo para otimizar suas rotas de entrega.")

    # Dividir a página em duas colunas para melhor organização
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🛠️ Critério de Otimização")
        criterio = st.selectbox("Escolha o critério:", ["Menor Distância", "Menor Tempo", "Menor Custo"])

        st.markdown("#### 🔒 Restrições")
        janela_tempo = st.checkbox("Considerar janelas de tempo")
        capacidade = st.checkbox("Respeitar capacidade dos veículos")

    with col2:
        st.markdown("#### 📍 Preferências")
        ponto_partida = st.text_input("Ponto de partida (endereço ou coordenadas)", placeholder="Ex: Rua A, 123, São Paulo")
        ponto_chegada = st.text_input("Ponto de chegada (opcional)", placeholder="Ex: Rua B, 456, São Paulo")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Salvar Configurações"):
            st.success("Configurações salvas com sucesso!")
