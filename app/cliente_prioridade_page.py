import streamlit as st
import pandas as pd
import re

# =========================
# Normalizações básicas
# =========================
def normaliza_codigo(cod):
    """Mantém apenas dígitos do código."""
    return ''.join(re.findall(r'\d+', str(cod).strip()))

def _sem_acentos_upper(s: str) -> str:
    s = str(s or "").upper().strip()
    s = (s.replace("Ã", "A").replace("Á", "A").replace("Â", "A").replace("À", "A")
           .replace("É", "E").replace("Ê", "E")
           .replace("Í", "I")
           .replace("Ó", "O").replace("Ô", "O").replace("Õ", "O")
           .replace("Ú", "U")
           .replace("Ç", "C"))
    s = s.replace("\u00A0", " ")  # NBSP
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normaliza_horario(h):
    return _sem_acentos_upper(h)

def normaliza_grupo(grupo):
    return _sem_acentos_upper(grupo)

# =========================
# Regras de horário por Grupo Cliente
# =========================
def horario_por_grupo(grupo):
    g = normaliza_grupo(grupo)
    if "MARCHE" in g: return "ATE 15:00"
    if "CARREFOUR" in g: return "ATE 11:00"
    if "ASP" in g: return "ATE 12:00"
    if "GIGA" in g: return "DAS 09:00 ATE 11:00"
    if "TENDA ATACADO" in g or "TENDA" in g: return "ATE 11:00"
    if "COVABRA" in g: return "ATE 12:00"
    if "IRMAOS BOA" in g or "IRMÃOS BOA" in g or "IRMOS BOA" in g or "BOA" in g: return "ATE 13:00"
    if "WAL-MART" in g or "WAL MART" in g or "WALMART" in g: return "ATE 11:00"
    if "BERGAMINI" in g: return "ATE 11:00"
    if "TRIMAIS" in g or "SABORES TRIMAIS" in g: return "ATE 11:00"
    # Demais grupos sem regra → volta vazio para cair no EMAIL
    return ""

# =========================
# Limita nome do cliente a 15 letras (mantém espaços)
# =========================
def limitar_cliente15(s):
    s = str(s).upper().strip()
    out = ""
    letras = 0
    ultima_espaco = False
    for ch in s:
        if ch.isalpha():
            out += ch
            letras += 1
            ultima_espaco = False
            if letras >= 15:
                break
        elif ch == " ":
            if out and not ultima_espaco:
                out += " "
                ultima_espaco = True
        # ignora dígitos/pontuação
    return out.strip()

# =========================
# Extração robusta de horário de qualquer texto
# =========================
_TIME_TOKEN = r'(?P<h>\d{1,2})[:H]?(?P<m>\d{2})?'  # 9:00, 09:00, 9h00, 900 (m opcional)
_INTERVAL_RE = re.compile(
    rf'\bDAS\b\s*(?P<h1>\d{{1,2}})[:H]?(?P<m1>\d{{2}})?\s*(?:\bAS\b|\bATE\b)\s*(?P<h2>\d{{1,2}})[:H]?(?P<m2>\d{{2}})?\b'
)
_ATE_RE = re.compile(rf'\bATE\b\s*{_TIME_TOKEN}')
_AS_RE  = re.compile(rf'\bAS\b\s*{_TIME_TOKEN}')
_TOKEN_RE   = re.compile(_TIME_TOKEN)
_COMPACT_RE = re.compile(r'\b(?P<d>\d{3,4})\b')

def _fmt_hm(hh: str, mm: str | None) -> str:
    H = int(hh)
    M = int(mm) if (mm and mm.isdigit()) else (0 if mm is None else 0)
    return f"{H:02d}:{M:02d}"

def _fmt_compact_to_hm(d: str) -> str:
    d = d.strip()
    if len(d) == 3:   # 900 -> 09:00
        return f"0{d[0]}:{d[1:]}"
    if len(d) == 4:   # 1530 -> 15:30
        return f"{d[:2]}:{d[2:]}"
    return ""

def extrai_horario(texto: str) -> str:
    t = normaliza_horario(texto)

    # 1) Intervalo "DAS ... ATE/AS ..."
    m = _INTERVAL_RE.search(t)
    if m:
        h1 = _fmt_hm(m.group('h1'), m.group('m1'))
        h2 = _fmt_hm(m.group('h2'), m.group('m2'))
        return f"DAS {h1} ATE {h2}"

    # 2) "ATE HH[:MM]"
    m = _ATE_RE.search(t)
    if m:
        h = _fmt_hm(m.group('h'), m.group('m'))
        return f"ATE {h}"

    # 3) "AS HH[:MM]"
    m = _AS_RE.search(t)
    if m:
        h = _fmt_hm(m.group('h'), m.group('m'))
        return f"AS {h}"

    # 4) HH[:MM] / HhMM → assume "ATE"
    m = _TOKEN_RE.search(t)
    if m:
        h = _fmt_hm(m.group('h'), m.group('m'))
        return f"ATE {h}"

    # 5) Compacto 900 / 1530
    m = _COMPACT_RE.search(t)
    if m:
        h = _fmt_compact_to_hm(m.group('d'))
        if h:
            return f"ATE {h}"

    return ""

# =========================
# Parsers do EMAIL (Campo 1)
# =========================
_SEP_REGEX = re.compile(r'[-–—;,\t|]')  # separadores comuns

def _split_codigo_hora(linha: str):
    """
    Aceita:
      123456 - ATE 11:00
      123456;ATE 11:00
      123456<TAB>ATE 11:00
      123456    ATE 11:00
      123456 - CLIENTE XYZ - ATE 11:00
      123456 - CLIENTE XYZ DAS 09:00 ATE 11:00
      123456 11:00
    Retorna (codigo, resto) — o horário é extraído depois via extrai_horario().
    """
    ln = str(linha or "").replace("\u00A0", " ").strip()
    ln = ln.replace("–", "-").replace("—", "-")

    # Código no início da linha
    m_cod = re.match(r'^\s*(\d{3,})\b(.*)$', ln)
    if m_cod:
        codigo = m_cod.group(1).strip()
        resto = m_cod.group(2).strip()
        if resto and _SEP_REGEX.match(resto[:1]):
            resto = resto[1:].strip()
        return codigo, resto

    # Fallback por separador
    if _SEP_REGEX.search(ln):
        parts = _SEP_REGEX.split(ln, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

    # Último recurso
    return ln, ""

def importar_email_cru(df_email: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói DataFrame com colunas: CÓD. CLIENTE, HORÁRIO
    A partir de:
      - 1 coluna "A" com linhas de texto variadas
      - 2+ colunas onde tenta mapear CÓD. CLIENTE e HORÁRIO
    """
    df = df_email.copy()

    # Caso 1: apenas 1 coluna
    if df.shape[1] == 1:
        df.columns = ["A"]
        cods, horas = [], []
        for txt in df["A"].astype(str):
            cod, resto = _split_codigo_hora(txt)
            cod_norm = normaliza_codigo(cod)
            if cod_norm:
                horario = extrai_horario(resto) or extrai_horario(txt)
                cods.append(cod_norm)
                horas.append(normaliza_horario(horario))
        return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

    # Caso 2: 2+ colunas — tenta mapear cabeçalhos
    cols_map = {}
    for c in df.columns:
        cname = _sem_acentos_upper(c)
        if ("COD" in cname) and "CLIENTE" in cname:
            cols_map[c] = "CÓD. CLIENTE"
        elif "HOR" in cname or "ENTREGAR" in cname:
            cols_map[c] = "HORÁRIO"
        elif c in ("A", "Coluna A", "COLUNA A"):
            cols_map[c] = "A"

    if cols_map:
        df = df.rename(columns=cols_map)

    # Se não tem as duas colunas, reconstrói a partir de "A"
    if not {"CÓD. CLIENTE", "HORÁRIO"}.issubset(df.columns):
        if "A" in df.columns:
            cods, horas = [], []
            for txt in df["A"].astype(str):
                cod, resto = _split_codigo_hora(txt)
                cod_norm = normaliza_codigo(cod)
                if cod_norm:
                    horario = extrai_horario(resto) or extrai_horario(txt)
                    cods.append(cod_norm)
                    horas.append(normaliza_horario(horario))
            return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

    # Já tem as duas: normaliza e extrai se vier sujo
    df["CÓD. CLIENTE"] = df["CÓD. CLIENTE"].astype(str).apply(normaliza_codigo)
    df["HORÁRIO"] = df["HORÁRIO"].astype(str).apply(lambda x: normaliza_horario(extrai_horario(x) or x))
    df = df[df["CÓD. CLIENTE"] != ""]
    return df[["CÓD. CLIENTE", "HORÁRIO"]].reset_index(drop=True)

def importar_email_cru_from_text(texto: str) -> pd.DataFrame:
    linhas = (texto or "").splitlines()
    cods, horas = [], []
    for ln in linhas:
        if not ln.strip():
            continue
        cod, resto = _split_codigo_hora(ln)
        cod_norm = normaliza_codigo(cod)
        if cod_norm:
            horario = extrai_horario(resto) or extrai_horario(ln)
            cods.append(cod_norm)
            horas.append(normaliza_horario(horario))
    return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

# =========================
# Limpeza de linhas-resumo nas PRIORIDADES
# =========================
def _row_values_clean(row) -> list[str]:
    vals = []
    for v in row:
        s = str(v).strip()
        if s and s.lower() not in ("nan", "none"):
            vals.append(s)
    return vals

def limpar_linhas_resumo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove:
      - linhas totalmente vazias;
      - linhas com apenas 1 célula preenchida contendo somente dígitos (ex.: '24');
      - linhas com célula que comece com 'TOTAL' ou 'SOMA'.
    """
    if df is None or df.empty:
        return df

    def is_resumo(row) -> bool:
        vals = _row_values_clean(row)
        if len(vals) == 0:
            return True
        if len(vals) == 1 and re.fullmatch(r'\d{1,10}', vals[0]):
            return True
        # qualquer célula que indique totalização
        if any(_sem_acentos_upper(v).startswith(("TOTAL", "SOMA")) for v in vals):
            return True
        return False

    mask = df.apply(is_resumo, axis=1)
    return df.loc[~mask].reset_index(drop=True)

# =========================
# Aplicação de horários no PRIORIDADES
# =========================
def construir_dict_email(df_email: pd.DataFrame) -> dict:
    return {
        normaliza_codigo(row["CÓD. CLIENTE"]): normaliza_horario(row["HORÁRIO"])
        for _, row in df_email.iterrows()
        if normaliza_codigo(row["CÓD. CLIENTE"]) and str(row["HORÁRIO"]).strip() not in ("", "SEM HORARIO")
    }

def atualizar_horarios_prioridades(df_prior: pd.DataFrame, df_email: pd.DataFrame) -> pd.DataFrame:
    """
    df_prior deve conter: Placa, Nº Ped., Grupo Cliente, Cód. Cliente, Cliente
    """
    dict_email = construir_dict_email(df_email)

    horarios = []
    origem = []
    for _, row in df_prior.iterrows():
        grupo = row.get("Grupo Cliente", "") or row.get("GRUPO CLIENTE", "") or ""
        cod   = normaliza_codigo(row.get("Cód. Cliente", "") or row.get("COD CLIENTE", "") or row.get("CODIGO CLIENTE", ""))

        gnorm = normaliza_grupo(grupo)
        if gnorm in ("NENHUM", "NONE", "SEM GRUPO"):
            gnorm = ""

        # Prioridade: Grupo > EMAIL > SEM HORARIO
        hora_grupo = horario_por_grupo(gnorm)
        if hora_grupo:
            horarios.append(hora_grupo)
            origem.append("Grupo Cliente")
        elif cod in dict_email and dict_email[cod].strip():
            horarios.append(dict_email[cod])
            origem.append("EMAIL")
        else:
            horarios.append("SEM HORARIO")
            origem.append("SEM HORARIO")

    out = df_prior.copy()
    out["Horário"] = horarios
    out["Origem Horário"] = origem
    return out

# =========================
# Bloco final por placa
# =========================
def gerar_bloco_por_placa(df_prior: pd.DataFrame) -> str:
    df = df_prior.copy()
    df["Placa"] = df["Placa"].astype(str).str.upper().str.strip()
    df["Cód. Cliente"] = df["Cód. Cliente"].astype(str).apply(normaliza_codigo)
    df["Cliente"] = df["Cliente"].astype(str).str.upper().str.strip().apply(limitar_cliente15)
    df["Horário"] = df["Horário"].astype(str).str.upper().str.strip()

    blocos = []
    for placa, grupo in df.groupby("Placa"):
        itens = []
        for _, row in grupo.iterrows():
            cod = row["Cód. Cliente"]
            cliente = row["Cliente"]
            hora = row["Horário"] if row["Horário"] else "SEM HORARIO"
            itens.append(f"{cod} - {cliente} ENTREGAR {hora}")
        blocos.append(f"{placa}:\n{' | '.join(itens)}\n")
    return "\n".join(blocos)

# =========================
# UI Streamlit
# =========================
def show():
    st.header("Cliente Prioridade", divider="rainbow")
    st.write("Automação de prioridades: importa e-mails, aplica regras de horário por grupo/cliente e gera bloco por placa.")

    # -------- 1) EMAIL --------
    st.subheader("1. Informe os dados do EMAIL")
    st.caption("Aceita: 'COD - ATE 11:00', 'COD;ATE 11:00', 'COD\\tATE 11:00', 'COD    ATE 11:00', 'COD 11:00', 'COD - CLIENTE - ATE 11:00', 'COD - ... DAS 09:00 ATE 11:00'.")
    email_text = st.text_area(
        "Cole aqui o conteúdo da planilha EMAIL (coluna A: texto ou CÓD. CLIENTE/HORÁRIO, um por linha):",
        height=200, key="email_text"
    )

    df_email = None
    if email_text.strip():
        df_email = importar_email_cru_from_text(email_text)
        st.success("EMAIL processado da caixa de texto.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Códigos no EMAIL", len(df_email))
        with col2:
            st.metric("Com horário válido", int((df_email["HORÁRIO"].str.strip() != "").sum()))
        st.dataframe(df_email, use_container_width=True)
    else:
        st.info("Cole os dados do EMAIL acima.")

    # -------- 2) PRIORIDADES --------
    st.subheader("2. Upload das Planilhas PRIORIDADES")
    prior_file_clients = st.file_uploader("Planilha Clientes Prioridades", type=["xlsx", "csv"], key="prior_file_clients")
    prior_file_redes   = st.file_uploader("Planilha Redes Prioridades (opcional)", type=["xlsx", "csv"], key="prior_file_redes")

    df_prior = None
    df_prior_clients = None
    df_prior_redes = None

    if prior_file_clients:
        if prior_file_clients.name.lower().endswith(".xlsx"):
            df_prior_clients = pd.read_excel(prior_file_clients, dtype=str)
        else:
            df_prior_clients = pd.read_csv(prior_file_clients, dtype=str)
        # limpa linhas de resumo (ex.: a linha "24" do rodapé)
        df_prior_clients = limpar_linhas_resumo(df_prior_clients)
        st.success("PRIORIDADES (Clientes) importada.")
        st.dataframe(df_prior_clients, use_container_width=True)

    if prior_file_redes:
        if prior_file_redes.name.lower().endswith(".xlsx"):
            df_prior_redes = pd.read_excel(prior_file_redes, dtype=str)
        else:
            df_prior_redes = pd.read_csv(prior_file_redes, dtype=str)
        df_prior_redes = limpar_linhas_resumo(df_prior_redes)
        st.success("PRIORIDADES (Redes) importada.")
        st.dataframe(df_prior_redes, use_container_width=True)

    # Combina
    if df_prior_clients is not None or df_prior_redes is not None:
        frames = []
        if df_prior_clients is not None: frames.append(df_prior_clients)
        if df_prior_redes   is not None: frames.append(df_prior_redes)
        df_prior = pd.concat(frames, ignore_index=True, sort=False)

        # Limpa novamente pós-concat (garante remoção de qualquer rodapé residual)
        df_prior = limpar_linhas_resumo(df_prior)

        # Mapeia cabeçalhos comuns
        cols_map = {}
        for c in df_prior.columns:
            cname = _sem_acentos_upper(c)
            if ("COD" in cname) and "CLIENTE" in cname:
                cols_map[c] = "Cód. Cliente"
            elif "PLACA" in cname:
                cols_map[c] = "Placa"
            elif "GRUPO" in cname and "CLIENTE" in cname:
                cols_map[c] = "Grupo Cliente"
            elif cname in ("CLIENTE", "NOME CLIENTE", "NOME DO CLIENTE", "CLIENTE NOME"):
                cols_map[c] = "Cliente"
            elif ("PED" in cname) and any(tag in cname for tag in ["N", "NO", "NUM", "NUMERO", "Nº"]):
                cols_map[c] = "Nº Ped."

        if cols_map:
            df_prior = df_prior.rename(columns=cols_map)

        # Normaliza campos principais
        if "Cód. Cliente" in df_prior.columns:
            df_prior["Cód. Cliente"] = df_prior["Cód. Cliente"].astype(str).apply(normaliza_codigo)
        if "Placa" in df_prior.columns:
            df_prior["Placa"] = df_prior["Placa"].astype(str).str.upper().str.strip()
        if "Cliente" in df_prior.columns:
            df_prior["Cliente"] = df_prior["Cliente"].astype(str).str.strip()

        # Remove duplicados por (Cód. Cliente, Placa)
        if "Cód. Cliente" in df_prior.columns and "Placa" in df_prior.columns:
            antes = len(df_prior)
            df_prior = df_prior.drop_duplicates(subset=["Cód. Cliente", "Placa"])
            removidos = antes - len(df_prior)
            if removidos > 0:
                st.success(f"Removidos {removidos} registros duplicados (mesmo Cód. Cliente + mesma Placa).")

        st.success("Planilhas combinadas.")
        st.dataframe(df_prior, use_container_width=True)

    # Diagnóstico de match EMAIL x PRIORIDADES
    if df_email is not None and df_prior is not None and "Cód. Cliente" in df_prior.columns:
        dict_email = construir_dict_email(df_email)
        cods_prior = set(df_prior["Cód. Cliente"].astype(str).apply(normaliza_codigo))
        cods_email = set(dict_email.keys())
        matches = len(cods_prior & cods_email)
        with st.expander("Diagnóstico de matches EMAIL ↔ PRIORIDADES"):
            st.write(f"Códigos distintos em PRIORIDADES: **{len(cods_prior)}**")
            st.write(f"Códigos com horário no EMAIL: **{len(cods_email)}**")
            st.write(f"Matches (interseção): **{matches}**")
            if matches:
                exemplos = list(cods_prior & cods_email)[:15]
                st.write("Exemplos de códigos casados:", exemplos)

    # -------- 3) Atualizar Horários --------
    st.divider()
    if df_email is not None and df_prior is not None:
        st.subheader("3. Atualizar Horários na Prioridade")
        if st.button("Atualizar Horários"):
            df_prior_atual = atualizar_horarios_prioridades(df_prior, df_email)
            st.dataframe(df_prior_atual, use_container_width=True)
            st.session_state["df_prior_atual"] = df_prior_atual
        else:
            df_prior_atual = st.session_state.get("df_prior_atual", None)
            if df_prior_atual is not None:
                st.dataframe(df_prior_atual, use_container_width=True)
    else:
        df_prior_atual = None

    # -------- 4) Gerar Bloco --------
    st.divider()
    if df_prior_atual is not None:
        st.subheader("4. Gerar Bloco por Placa")
        if st.button("Gerar Bloco"):
            bloco = gerar_bloco_por_placa(df_prior_atual)
            st.text_area("Bloco Gerado", bloco, height=220)
            st.download_button("Baixar Bloco como TXT", bloco.encode("utf-8"), file_name="bloco_entregas.txt")
        else:
            _ = None

    st.info("Dica: Você pode copiar o bloco gerado acima e colar onde desejar.")

# Para integrar no app principal, basta: from seu_modulo import show; show()
``
