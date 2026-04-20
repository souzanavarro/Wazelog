import sys
import os
import streamlit as st
import pandas as pd
import requests
sys.dont_write_bytecode = True

st.set_page_config(page_title="Wazelog", layout="wide")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import init_db
init_db()

from dashboard_page import show as show_dashboard
from frota_page import show as show_frota
from pedidos_page import show as show_pedidos
from roteirizacao_page import show as show_roteirizacao
from mapas_page import show as show_mapas
from cnpj_page import show as show_cnpj
from pedagios_page import show as show_pedagios
# Login removido: não mais importamos/checamos autenticação
from ctrcs_page import show as show_ctrcs
from cliente_prioridade_page import show as show_cliente_prioridade
from ui import apply_styles

# --- Toggle de tema ---
# Remover título e centralizar layout do menu
with st.sidebar:
    st.markdown("""
        <style>
        .stSidebar, section[data-testid="stSidebar"] {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .menu-title {display: none !important;}
        </style>
    """, unsafe_allow_html=True)
    theme_mode = st.radio('Selecionar tema', options=['🌞 Claro', '🌙 Escuro'], horizontal=True, key='theme_mode', label_visibility="collapsed")

# --- Centraliza CSS via `app.ui.apply_styles` ---
apply_styles(theme_mode)

# --- Menu lateral minimalista com ícones ---
main_submenus = [
    ("Dashboard", "🏠"),
    ("Frota", "🚚"),
    ("Pedidos", "📦"),
    ("Roteirização", "🗺️"),
    ("Mapas", "🗾"),
]

other_items = [
    ("Busca CNPJ", "🔎"),
    ("Pedágios", "💸"),
    ("CTRCs", "📑"),
    ("Clientes Prioridades", "⭐"),
]

with st.sidebar:
    pagina = st.session_state.get('pagina_selecionada', 'Dashboard')
    with st.expander('Roteirização', expanded=True):
        for nome, icone in main_submenus:
            btn = st.button(f"{icone}  {nome}", key=f"menu_{nome}", use_container_width=True)
            if btn:
                st.session_state['pagina_selecionada'] = nome
                st.rerun()
    st.markdown("<hr class='menu-divider'>", unsafe_allow_html=True)
    for nome, icone in other_items:
        btn = st.button(f"{icone}  {nome}", key=f"menu_{nome}", use_container_width=True)
        if btn:
            st.session_state['pagina_selecionada'] = nome
            st.rerun()
    st.markdown("<hr class='menu-divider'>", unsafe_allow_html=True)

# --- Renderização das páginas (login removido; acesso direto) ---
pagina = st.session_state.get('pagina_selecionada', 'Dashboard')
if pagina == "Dashboard":
    show_dashboard()
elif pagina == "Frota":
    show_frota()
elif pagina == "Pedidos":
    show_pedidos()
elif pagina == "Roteirização":
    show_roteirizacao()
elif pagina == "Mapas":
    show_mapas()
elif pagina == "Busca CNPJ":
    show_cnpj()
elif pagina == "Pedágios":
    show_pedagios()
elif pagina == "CTRCs":
    show_ctrcs()
elif pagina == "Clientes Prioridades":
    show_cliente_prioridade()
else:
    show_dashboard()
