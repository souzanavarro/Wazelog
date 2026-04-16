import streamlit as st
import pandas as pd
import re
from io import StringIO

# ============================================================
#  🔧 NORMALIZAÇÕES BÁSICAS
# ============================================================

def normaliza_codigo(cod: str) -> str:
    return ''.join(re.findall(r'\d+', str(cod).strip()))

def _sem_acentos_upper(s: str) -> str:
    s = str(s or "").upper().strip()
    tabela = {
        "Ã": "A", "Á": "A", "Â": "A", "À": "A",
        "É": "E", "Ê": "E",
        "Í": "I",
        "Ó": "O", "Ô": "O", "Õ": "O",
        "Ú": "U",
        "Ç": "C"
    }
    for k, v in tabela.items():
        s = s.replace(k, v)
    s = s.replace("\u00A0", " ")
    return re.sub(r"\s+", " ", s).strip()

def normaliza_grupo(g: str) -> str:
    return _sem_acentos_upper(g)

def normaliza_horario(h: str) -> str:
    return _sem_acentos_upper(h)

# ============================================================
#  ⏰ REGRAS DE HORÁRIO
# ============================================================

REGRAS_GRUPO = {
    "ASP": "ATE 12:00",
    "BERGAMINI": "ATE 11:00",
    "CARREFOUR": "ATE 11:00",
    "COOPERCICA": "ATE 10:00",
    "COVABRA": "ATE 12:00",
    "DIVINO FOGAO": "ATE 10:00",
    "GIGA": "DAS 09:00 AS 11:00",
    "INFANGER": "ATE 11:00",
    "IRMAOS BOA": "ATE 15:00",
    "IRMÃOS BOA": "ATE 15:00",
    "IRMAO BOA": "ATE 15:00",
    "MAMBO": "ATE 15:00",
    "NEGREIROS": "ATE 14:00",
    "REDE MARCHE": "ATE 11:00",
    "MARCHE": "ATE 11:00",
    "ROSSI": "ATE 16:00",
    "SENDAS": "ATE 11:00",
    "TENDA": "ATE 11:00",
    "TENDA ATACADO": "ATE 11:00",
    "TRIMAIS": "ATE 11:00",
    "WAL-MART": "ATE 11:00",
    "WAL MART": "ATE 11:00",
    "WALMART": "ATE 11:00",
}

def horario_por_grupo(grupo: str) -> str:
    g = normaliza_grupo(grupo)
    for chave, horario in REGRAS_GRUPO.items():
        if chave in g or g.startswith(chave):
            return horario
    return ""

# ============================================================
#  🧠 MAPA GRUPO → CÓDIGOS
# ============================================================

MAPA_GRUPO_CODIGOS = {
    "ASP": ["204885", "207498", "195274", "193263", "207499", "202007"],
    "BERGAMINI": ["934", "8991", "407"],
    "CARREFOUR": ["200185", "200545", "200566", "200203", "213506", "1029", "208079", "1475", "1474", "8666"],
    "COOPERCICA": ["204939", "14466", "1044", "1038", "8637", "196986", "204187", "1037", "185619"],
    "COVABRA": ["195797", "205692", "11618", "208510", "217278", "11625", "196723", "13168", "191577", "216679", "205138", "11619", "11623", "195790"],
    "DIVINO FOGAO": ["209730", "212972", "204734", "216256", "214961", "216157", "204736", "204310", "216496"],
    "GIGA": ["216261", "207320"],
    "INFANGER": ["197060", "177924"],
    "IRMAOS BOA": ["195254", "216356"],
    "MAMBO": ["209833", "209371", "200883", "210533", "13374", "207683"],
    "NEGREIROS": ["211053", "14268", "14263", "194781", "2753", "207890", "2751"],
    "REDE MARCHE": ["211634", "211584", "11829", "205012", "203762"],
    "TRIMAIS": ["11367", "217040", "214289", "214494"],
}

MAPA_CODIGO_GRUPO = {}
for grupo, codigos in MAPA_GRUPO_CODIGOS.items():
    for cod in codigos:
        MAPA_CODIGO_GRUPO[normaliza_codigo(cod)] = grupo

def grupo_por_codigo(cod: str) -> str:
    return MAPA_CODIGO_GRUPO.get(normaliza_codigo(cod), "")

# ============================================================
#  📥 EMAIL
# ============================================================

_TOKEN = r'(?P<h>\d{1,2})[:H]?(?P<m>\d{2})?'

def extrai_horario(texto: str) -> str:
    t = normaliza_horario(texto)
    m = re.search(_TOKEN, t)
    if m:
        return f"ATE {int(m.group('h')):02d}:{int(m.group('m') or 0):02d}"
    return ""

def importar_email_cru_from_text(texto: str) -> pd.DataFrame:
    cods, horas = [], []
    for ln in texto.splitlines():
        if not ln.strip():
            continue
        cod = normaliza_codigo(ln)
        hora = extrai_horario(ln)
        if cod:
            cods.append(cod)
            horas.append(hora)
    return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

# ============================================================
#  🔄 ATUALIZAÇÃO
# ============================================================

def construir_dict_email(df_email: pd.DataFrame) -> dict:
    return {
        normaliza_codigo(row["CÓD. CLIENTE"]): normaliza_horario(row["HORÁRIO"])
        for _, row in df_email.iterrows()
        if row["HORÁRIO"]
    }

def atualizar_horarios_prioridades(df_prior: pd.DataFrame, df_email: pd.DataFrame) -> pd.DataFrame:
    dict_email = construir_dict_email(df_email)
    horarios, origem = [], []

    for _, row in df_prior.iterrows():
        cod = normaliza_codigo(row.get("Cód. Cliente", ""))

        grupo_codigo = grupo_por_codigo(cod)
        grupo_planilha = row.get("Grupo Cliente", "")

        grupo = grupo_codigo if grupo_codigo else grupo_planilha
        gnorm = normaliza_grupo(grupo)

        if cod in dict_email:
            horarios.append(dict_email[cod])
            origem.append("EMAIL")
        else:
            hora = horario_por_grupo(gnorm)
            if hora:
                horarios.append(hora)
                origem.append("GRUPO")
            else:
                horarios.append("SEM HORARIO")
                origem.append("SEM HORARIO")

    df_prior["Horário"] = horarios
    df_prior["Origem Horário"] = origem
    return df_prior

# ============================================================
#  🖥 STREAMLIT
# ============================================================

def show():
    st.header("Prioridades", divider="rainbow")

    email_text = st.text_area("Cole EMAIL")

    if email_text:
        df_email = importar_email_cru_from_text(email_text)
        st.dataframe(df_email)

        file = st.file_uploader("Planilha Prioridades")

        if file:
            df_prior = pd.read_excel(file, dtype=str)
            df_prior = atualizar_horarios_prioridades(df_prior, df_email)
            st.dataframe(df_prior)

if __name__ == "__main__":
    show()
