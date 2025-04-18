import streamlit as st

def pagina_roteirizador():
    st.title("Configurações do Roteirizador")
    st.markdown("""
    ### Configure os parâmetros para a roteirização:
    - Escolha o critério de otimização.
    - Defina restrições e preferências.
    """)

    # Configuração de critérios de otimização
    st.markdown("#### Critério de Otimização")
    criterio = st.selectbox("Escolha o critério:", ["Menor Distância", "Menor Tempo", "Menor Custo"])

    # Configuração de restrições
    st.markdown("#### Restrições")
    janela_tempo = st.checkbox("Considerar janelas de tempo")
    capacidade = st.checkbox("Respeitar capacidade dos veículos")

    # Configuração de preferências
    st.markdown("#### Preferências")
    ponto_partida = st.text_input("Ponto de partida (endereço ou coordenadas)")
    ponto_chegada = st.text_input("Ponto de chegada (opcional)")

    # Botão para salvar configurações
    if st.button("Salvar Configurações"):
        st.success("Configurações salvas com sucesso!")
