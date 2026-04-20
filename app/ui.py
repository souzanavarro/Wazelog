import streamlit as st


def apply_styles(theme_mode: str = '🌞 Claro'):
    """Aplica CSS centralizado para os temas Claro/Escuro.

    Chamado a partir de `app.py` para remover CSS inline repetido.
    """
    streamlit_red = "#FF4B4B"
    streamlit_red_dark = "#c62828"
    streamlit_accent_hover = "#D32F2F"

    if theme_mode == '🌞 Claro':
        st.markdown(f'''
        <style>
        body, .stApp {{
          font-family: 'Inter', 'Roboto', sans-serif;
          background: transparent !important;
          color: #1f1f1f !important;
        }}
        .stSidebar, section[data-testid="stSidebar"] {{
          background: #ffffff !important;
          color: #1f1f1f !important;
          border-radius: 16px; /* Consistente com cards */
          border-right: 1px solid #e0e0e0;
          box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .menu-title {{display: none !important;}}
        .menu-title {{
          font-size: 1.4rem;
          font-weight: 700;
          color: {streamlit_red};
          margin-bottom: 1.8rem;
          letter-spacing: 0.5px;
          text-align: left;
        }}
        .menu-btn {{
          display: flex;
          align-items: center;
          gap: 0.8rem;
          background: transparent;
          color: #333;
          border: none;
          border-radius: 12px;
          font-size: 1.05rem;
          font-weight: 500;
          padding: 0.8rem 1.1rem;
          margin-bottom: 0.4rem;
          transition: background 0.2s ease-in-out, color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
          cursor: pointer;
        }}
        .menu-btn.selected, .menu-btn:hover {{
          background: {streamlit_red}1A;
          color: {streamlit_red};
          font-weight: 600;
        }}
        .menu-divider {{
          height: 1.5px;
          background: #e0e0e0;
          margin: 1.5rem 0.5rem;
          border: none;
        }}
        .cardbox {{
          background: #ffffff;
          border-radius: 16px;
          box-shadow: 0 5px 15px rgba(0,0,0,0.07);
          padding: 1.5rem 1.8rem;
          margin: 1.5rem 0 2rem 0;
          color: #1f1f1f;
          transition: box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out;
          border: 1px solid #e9e9e9;
        }}
        .cardbox:hover {{
          box-shadow: 0 8px 25px rgba(0,0,0,0.1);
          transform: translateY(-3px);
        }}
        .kpi {{
          font-size: 2.3rem;
          font-weight: 700;
          color: {streamlit_red};
          margin-top: 0.5rem;
        }}
        .kpi-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 0.2rem;
        }}
        .stButton>button, .stDownloadButton>button {{
          border-radius: 12px;
          font-weight: 600;
          font-size: 1rem;
          min-height: 44px;
          height: 44px;
          padding: 0 1.4rem;
          background: #ffffff;
          color: #333333;
          border: 1px solid #d0d0d0;
          box-shadow: 0 2px 5px rgba(0,0,0,0.08);
          transition: background 0.2s, box-shadow 0.2s, transform 0.2s, border-color 0.2s;
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }}
        /* Inputs e tabelas simplificados - somente o essencial para reduzir duplicação */
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] > div {{
            background-color: #ffffff !important;
            color: #333333 !important;
            border: 1px solid #d0d0d0 !important;
            border-radius: 8px !important;
        }}
        .stMarkdown p {{
            margin-bottom: 0.8rem;
            line-height: 1.7;
        }}
        @media (max-width: 600px) {{
          .cardbox {{ padding: 1.2rem; margin: 1rem 0 1.5rem 0; }}
          .menu-title {{ font-size: 1.2rem; }}
          .kpi {{ font-size: 1.8rem; }}
        }}
        </style>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <style>
        body, .stApp {{
          font-family: 'Inter', 'Roboto', sans-serif;
          background: #181818 !important;
          color: #e0e0e0 !important;
        }}
        .stSidebar, section[data-testid="stSidebar"] {{
          background: #2a2a2a !important;
          color: #e0e0e0 !important;
          border-radius: 16px;
          border-right: 1px solid #3a3a3a;
          box-shadow: 0 2px 10px rgba(255,75,75,0.07);
        }}
        .menu-title {{display: none !important;}}
        .menu-title {{
          font-size: 1.4rem;
          font-weight: 700;
          color: {streamlit_red};
          margin-bottom: 1.8rem;
          letter-spacing: 0.5px;
          text-align: left;
        }}
        .menu-btn {{
          display: flex;
          align-items: center;
          gap: 0.8rem;
          background: transparent;
          color: #c5c5c5;
          border: none;
          border-radius: 12px;
          font-size: 1.05rem;
          font-weight: 500;
          padding: 0.8rem 1.1rem;
          margin-bottom: 0.4rem;
          transition: background 0.2s ease-in-out, color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
          cursor: pointer;
        }}
        .menu-btn.selected, .menu-btn:hover {{
          background: {streamlit_red}33;
          color: {streamlit_red};
          font-weight: 600;
        }}
        .menu-divider {{
          height: 1.5px;
          background: #444;
          margin: 1.5rem 0.5rem;
          border: none;
        }}
        .cardbox {{
          background: #2c2c2c;
          border-radius: 16px;
          box-shadow: 0 5px 15px rgba(0,0,0,0.25);
          padding: 1.5rem 1.8rem;
          margin: 1.5rem 0 2rem 0;
          color: #e0e0e0;
          transition: box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out;
          border: 1px solid #3f3f3f;
        }}
        .cardbox:hover {{
          box-shadow: 0 8px 25px rgba(0,0,0,0.35);
          transform: translateY(-3px);
        }}
        .kpi {{
          font-size: 2.3rem;
          font-weight: 700;
          color: {streamlit_red};
          margin-top: 0.5rem;
        }}
        .kpi-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: #e0e0e0;
            margin-bottom: 0.2rem;
        }}
        .stButton>button, .stDownloadButton>button {{
          border-radius: 12px;
          font-weight: 600;
          font-size: 1rem;
          min-height: 44px;
          height: 44px;
          padding: 0 1.4rem;
          background: #383838;
          color: #e0e0e0;
          border: 1px solid #505050;
          box-shadow: 0 2px 5px rgba(0,0,0,0.25);
          transition: background 0.2s, box-shadow 0.2s, transform 0.2s, border-color 0.2s;
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }}
        /* Inputs e tabelas simplificados - somente o essencial para reduzir duplicação */
        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-baseweb="select"] > div {{
            background-color: #383838 !important;
            color: #e0e0e0 !important;
            border: 1px solid #505050 !important;
            border-radius: 8px !important;
        }}
        .stMarkdown p {{
            margin-bottom: 0.8rem;
            line-height: 1.7;
        }}
        @media (max-width: 600px) {{
          .cardbox {{ padding: 1.2rem; margin: 1rem 0 1.5rem 0; }}
          .menu-title {{ font-size: 1.2rem; }}
          .kpi {{ font-size: 1.8rem; }}
        }}
        </style>
        ''', unsafe_allow_html=True)
