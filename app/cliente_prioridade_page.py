import streamlit as st
import pandas as pd
import re
from io import StringIO

# ============================================================
#  🔧 NORMALIZAÇÕES BÁSICAS
# ============================================================

def normaliza_codigo(cod: str) -> str:
    """Extrai apenas os dígitos do código."""
    return ''.join(re.findall(r'\d+', str(cod).strip()))

def _sem_acentos_upper(s: str) -> str:
    """Remove acentos, normaliza espaços e converte para UPPER."""
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
#  ⏰ REGRAS DE HORÁRIO POR GRUPO
# ============================================================

REGRAS_GRUPO = {
    "ASP": "ATE 12:00",
    "BERGAMINI": "ATE 11:00",
    "CARREFOUR": "ATE 11:00",
    "COOPERCICA": "ATE 10:00",
    "COVABRA": "ATE 12:00",
    "DIVINO FOGAO": "ATE 10:00",
    "GIGA": "DAS 07:00 AS 11:00",
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
    """Retorna o horário padrão pelo nome do grupo normalizado."""
    g = normaliza_grupo(grupo)
    for chave, horario in REGRAS_GRUPO.items():
        if chave in g or g.startswith(chave):
            return horario
    return ""

# ============================================================
#  🏬 REDUÇÃO DE PREFIXOS DO NOME DO CLIENTE
# ============================================================

PREFIX_MAP = {
    "SUPERMERCADOS": "SUP.",
    "SUPERMERCADO": "SUP.",
    "HIPERMERCADOS": "HIP.",
    "HIPERMERCADO": "HIP.",
    "ATACAREJOS": "ATAC.",
    "ATACAREJO": "ATAC.",
    "MINIMERCADOS": "MINIM.",
    "MINIMERCADO": "MINIM.",
    "ATACADISTAS": "ATAC.",
    "ATACADISTA": "ATAC."
}

def _reduzir_prefixo(nome: str, prefixo: str, abreviado: str) -> str:
    """
    Reduz prefixos de varejo preservando o restante do nome conforme digitado.
    Aceita 'com' e 'sem' espaço logo após o prefixo.
    """
    s = str(nome or "").strip()
    su = _sem_acentos_upper(s)

    # Com espaço
    if su.startswith(prefixo + " "):
        return f"{abreviado} {s[len(prefixo)+1:].lstrip()}"

    # Sem espaço
    if su.startswith(prefixo):
        resto = s[len(prefixo):].lstrip(" -_.")
        return f"{abreviado} {resto}"

    return s

def reduzir_prefixos_retail(nome: str) -> str:
    s = str(nome or "")
    for prefixo, abrev in PREFIX_MAP.items():
        s = _reduzir_prefixo(s, prefixo, abrev)
    return s

def limitar_cliente15(s: str) -> str:
    """Limita o nome a 15 letras, preservando espaços simples."""
    s = str(s).upper().strip()
    out, letras, last_space = "", 0, False
    for ch in s:
        if ch.isalpha():
            out += ch
            letras += 1
            last_space = False
            if letras >= 15:
                break
        elif ch == " " and out and not last_space:
            out += " "
            last_space = True
    return out.strip()

def preparar_nome_cliente(nome: str) -> str:
    """Aplica reduções de varejo e limite de 15 letras para exibição."""
    return limitar_cliente15(reduzir_prefixos_retail(nome))

# ============================================================
#  🔑 CHAVE BASE DO CLIENTE (para detectar repetidos de mesma "rede")
# ============================================================

def chave_base_cliente(nome: str) -> str:
    """
    Gera chave base pela combinação dos 2 primeiros tokens (sem acento/upper).
    Ex.: "MIX VALI COMERCIO", "MIX VALI COM DE PRO" => "MIX VALI"
    """
    su = _sem_acentos_upper(nome)
    tokens = re.findall(r"[A-Z0-9]+", su)
    if not tokens:
        return ""
    return " ".join(tokens[:2])

# ============================================================
#  ⏱ EXTRAÇÃO ROBUSTA DE HORÁRIO DE TEXTO
# ============================================================

_TOKEN = r'(?P<h>\d{1,2})[:H]?(?P<m>\d{2})?'

_INTERVAL_RE = re.compile(
    rf'\bDAS\b\s*(?P<h1>\d{{1,2}})[:H]?(?P<m1>\d{{2}})?\s*(?:AS|ATE)\s*(?P<h2>\d{{1,2}})[:H]?(?P<m2>\d{{2}})?'
)
_ATE_RE   = re.compile(rf'\bATE\b\s*{_TOKEN}')
_AS_RE    = re.compile(rf'\bAS\b\s*{_TOKEN}')
_TOKEN_RE = re.compile(_TOKEN)
_COMPACT_RE = re.compile(r'\b(?P<d>\d{3,4})\b')

def _fmt_hm(hh, mm) -> str:
    return f"{int(hh):02d}:{int(mm) if mm else 0:02d}"

def _fmt_compact_to_hm(d: str) -> str:
    return f"{d[:-2].zfill(2)}:{d[-2:]}" if len(d) in (3, 4) else ""

def extrai_horario(texto: str) -> str:
    """Extrai 'ATE HH:MM', 'AS HH:MM' ou 'DAS HH:MM AS HH:MM' de texto."""
    t = normaliza_horario(texto)

    if (m := _INTERVAL_RE.search(t)):
        h1 = _fmt_hm(m.group('h1'), m.group('m1'))
        h2 = _fmt_hm(m.group('h2'), m.group('m2'))
        return f"DAS {h1} AS {h2}"

    if (m := _ATE_RE.search(t)):
        return f"ATE {_fmt_hm(m.group('h'), m.group('m'))}"

    if (m := _AS_RE.search(t)):
        return f"AS {_fmt_hm(m.group('h'), m.group('m'))}"

    if (m := _TOKEN_RE.search(t)):
        return f"ATE {_fmt_hm(m.group('h'), m.group('m'))}"

    if (m := _COMPACT_RE.search(t)):
        return f"ATE {_fmt_compact_to_hm(m.group('d'))}"

    return ""

# ============================================================
#  📥 PARSERS DO EMAIL
# ============================================================

_SEP_REGEX = re.compile(r'[-–—;,\t|]')

def _split_codigo_hora(linha: str):
    """
    Aceita:
      123456 - ATE 11:00 ; 123456;ATE 11:00 ; 123456<TAB>ATE 11:00
      123456    ATE 11:00 ; 123456 - CLIENTE XYZ - ATE 11:00
      123456 - ... DAS 07:00 AS 11:00 ; 123456 11:00
    Retorna (codigo, resto) — o horário é extraído depois via extrai_horario().
    """
    ln = str(linha or "").replace("\u00A0", " ").strip()
    ln = ln.replace("–", "-").replace("—", "-")

    # Código no início da linha
    m = re.match(r'^\s*(\d{3,})\b(.*)$', ln)
    if m:
        codigo = m.group(1).strip()
        resto = m.group(2).lstrip(" -")
        return codigo, resto

    # Fallback por separador
    if _SEP_REGEX.search(ln):
        parts = _SEP_REGEX.split(ln, maxsplit=1)
        return parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""

    # Último recurso
    return ln, ""

def importar_email_cru_from_text(texto: str) -> pd.DataFrame:
    """Constrói DataFrame com colunas: CÓD. CLIENTE, HORÁRIO a partir de texto livre."""
    cods, horas = [], []
    for ln in (texto or "").splitlines():
        if not ln.strip():
            continue
        cod, resto = _split_codigo_hora(ln)
        cod_norm = normaliza_codigo(cod)
        if cod_norm:
            hora = extrai_horario(resto) or extrai_horario(ln)
            cods.append(cod_norm)
            horas.append(normaliza_horario(hora))
    return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

# ============================================================
#  🧹 LIMPEZA DE LINHAS NAS PLANILHAS PRIORIDADES
# ============================================================

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
        vals = [str(v).strip() for v in row if str(v).strip().lower() not in ("", "none", "nan")]
        if not vals:
            return True
        if len(vals) == 1 and re.fullmatch(r'\d{1,10}', vals[0]):
            return True
        if any(_sem_acentos_upper(v).startswith(("TOTAL", "SOMA")) for v in vals):
            return True
        return False

    mask = df.apply(is_resumo, axis=1)
    return df.loc[~mask].reset_index(drop=True)

# ============================================================
#  🔄 APLICAÇÃO DE HORÁRIOS
# ============================================================

def construir_dict_email(df_email: pd.DataFrame) -> dict:
    """Dict {cod_cliente: horario} apenas para horários válidos."""
    return {
        normaliza_codigo(row["CÓD. CLIENTE"]): normaliza_horario(row["HORÁRIO"])
        for _, row in df_email.iterrows()
        if normaliza_codigo(row["CÓD. CLIENTE"]) and str(row["HORÁRIO"]).strip() not in ("", "SEM HORARIO")
    }

def atualizar_horarios_prioridades(df_prior: pd.DataFrame, df_email: pd.DataFrame) -> pd.DataFrame:
    """
    PRIORIDADE INVERTIDA: EMAIL → Grupo → SEM HORARIO
    df_prior deve conter: Placa, Nº Ped., Grupo Cliente, Cód. Cliente, Cliente
    """
    dict_email = construir_dict_email(df_email)
    horarios, origem = [], []

    for _, row in df_prior.iterrows():
        grupo = row.get("Grupo Cliente", "") or row.get("GRUPO CLIENTE", "") or ""
        cod   = normaliza_codigo(row.get("Cód. Cliente", "") or row.get("COD CLIENTE", "") or row.get("CODIGO CLIENTE", ""))

        gnorm = normaliza_grupo(grupo)
        if gnorm in ("NENHUM", "NONE", "SEM GRUPO"):
            gnorm = ""

        if cod in dict_email and dict_email[cod].strip():
            horarios.append(dict_email[cod])
            origem.append("EMAIL")
        else:
            hora_grupo = horario_por_grupo(gnorm)
            if hora_grupo:
                horarios.append(hora_grupo)
                origem.append("Grupo Cliente")
            else:
                horarios.append("SEM HORARIO")
                origem.append("SEM HORARIO")

    out = df_prior.copy()
    out["Horário"] = horarios
    out["Origem Horário"] = origem
    return out

# ============================================================
#  🧾 GERAÇÃO DO BLOCO FINAL POR PLACA
#     Regra: se houver clientes "repetidos" de mesma base (ex.: MIX VALI ...),
#     omitir o CÓDIGO e exibir apenas 1 ocorrência (NOME + HORÁRIO) por base.
# ============================================================

def gerar_bloco_por_placa(df_prior: pd.DataFrame) -> str:
    df = df_prior.copy()

    # Campos normalizados
    df["Placa"] = df["Placa"].astype(str).str.upper().str.strip()
    df["Cód. Cliente"] = df["Cód. Cliente"].astype(str).apply(normaliza_codigo)
    df["Cliente"] = df["Cliente"].astype(str).str.strip()
    df["Horário"] = df["Horário"].astype(str).str.upper().str.strip()

    # Nome para exibição (abrevia prefixos e limita a 15 letras)
    df["_ClienteExib"] = df["Cliente"].apply(preparar_nome_cliente)
    # Chave base para detectar "mesmos clientes" de uma mesma rede
    df["_BaseKey"] = df["Cliente"].apply(chave_base_cliente)

    blocos = []

    for placa, grupo in df.groupby("Placa", sort=False):
        # Mapa final de itens da placa:
        # - chave: identificador único do que deve aparecer
        # - valor: string formatada para o bloco
        itens_fmt = []

        # 1) Colapsa por base (uma ocorrência por base)
        base_groups = dict(tuple(grupo.groupby("_BaseKey", sort=False)))

        for base, gbase in base_groups.items():
            if base and len(gbase) >= 2:
                # Bases repetidas: omite código e mantém só 1 item
                # Escolhe o nome exibido mais curto para ficar limpo
                row_escolhida = gbase.iloc[0]
                nome_curto = min(gbase["_ClienteExib"], key=len)
                # Mantém o horário do primeiro registro dessa base
                hora = row_escolhida["Horário"] if row_escolhida["Horário"] else "SEM HORARIO"
                itens_fmt.append(f"{nome_curto} ENTREGAR {hora}")

        # 2) Itens de bases não repetidas: mantém com código
        bases_repetidas = {b for b, gbase in base_groups.items() if b and len(gbase) >= 2}
        unicos = grupo[~grupo["_BaseKey"].isin(bases_repetidas)]
        for _, row in unicos.iterrows():
            cod = row["Cód. Cliente"]
            nome = row["_ClienteExib"]
            hora = row["Horário"] if row["Horário"] else "SEM HORARIO"
            itens_fmt.append(f"{cod} - {nome} ENTREGAR {hora}")

        # Remove duplicatas exatas por segurança mantendo a ordem
        vistos = set()
        itens_ordenados = []
        for it in itens_fmt:
            if it not in vistos:
                itens_ordenados.append(it)
                vistos.add(it)

        blocos.append(f"{placa}:\n{' | '.join(itens_ordenados)}\n")

    return "\n".join(blocos)

# ============================================================
#  🖥 INTERFACE STREAMLIT
# ============================================================

def show():
    st.header("Prioridades", divider="rainbow")
    st.write("Importe o EMAIL e as planilhas de PRIORIDADES, aplique regras de horário e gere o bloco por placa. O app também indica faltas (códigos presentes no EMAIL que não aparecem nas planilhas).")

    # ---------- 1) EMAIL ----------
    st.subheader("1. Informe os dados do EMAIL")
    st.caption("Aceita: 'COD - ATE 11:00', 'COD;ATE 11:00', 'COD\\tATE 11:00', 'COD    ATE 11:00', 'COD 11:00', 'COD - CLIENTE - ATE 11:00', 'COD - ... DAS 07:00 AS 11:00'.")
    email_text = st.text_area(
        "Cole aqui a coluna do EMAIL (texto livre com CÓD. e HORÁRIO, um por linha):",
        height=200, key="email_text"
    )

    df_email = None
    if email_text.strip():
        df_email = importar_email_cru_from_text(email_text)
        st.success("EMAIL processado.")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Códigos no EMAIL", len(df_email))
        with col2:
            st.metric("Com horário válido", int((df_email["HORÁRIO"].str.strip() != "").sum()))
        st.dataframe(df_email, use_container_width=True)
    else:
        st.info("Cole os dados do EMAIL acima.")

    # ---------- 2) PRIORIDADES ----------
    st.subheader("2. Upload das Planilhas PRIORIDADES")
    prior_file_clients = st.file_uploader("Planilha Clientes Prioridades", type=["xlsx", "csv"], key="prior_file_clients")
    prior_file_redes   = st.file_uploader("Planilha Redes Prioridades (opcional)", type=["xlsx", "csv"], key="prior_file_redes")

    df_prior = None
    frames = []

    if prior_file_clients:
        df1 = pd.read_excel(prior_file_clients, dtype=str) if prior_file_clients.name.lower().endswith(".xlsx") else pd.read_csv(prior_file_clients, dtype=str)
        df1 = limpar_linhas_resumo(df1)
        frames.append(df1)
        st.success("PRIORIDADES (Clientes) importada.")
        st.dataframe(df1, use_container_width=True)

    if prior_file_redes:
        df2 = pd.read_excel(prior_file_redes, dtype=str) if prior_file_redes.name.lower().endswith(".xlsx") else pd.read_csv(prior_file_redes, dtype=str)
        df2 = limpar_linhas_resumo(df2)
        frames.append(df2)
        st.success("PRIORIDADES (Redes) importada.")
        st.dataframe(df2, use_container_width=True)

    # Combina
    if frames:
        df_prior = pd.concat(frames, ignore_index=True, sort=False)
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

        # Normaliza campos principais existentes
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

    # ---------- 2.1) DIAGNÓSTICO: FALTAS DE PRIORIDADE
    if df_email is not None and df_prior is not None and "Cód. Cliente" in df_prior.columns:
        dict_email = construir_dict_email(df_email)
        cods_prior = set(df_prior["Cód. Cliente"].astype(str).apply(normaliza_codigo))
        cods_email = set(dict_email.keys())

        faltando_na_prioridade = sorted(cods_email - cods_prior)
        matches = len(cods_prior & cods_email)

        with st.expander("Diagnóstico de Matches e Faltas (EMAIL ↔ PRIORIDADES)", expanded=True):
            st.write(f"Códigos distintos em PRIORIDADES: **{len(cods_prior)}**")
            st.write(f"Códigos com horário no EMAIL: **{len(cods_email)}**")
            st.write(f"Matches (interseção): **{matches}**")

            if faltando_na_prioridade:
                st.warning(f"Faltam **{len(faltando_na_prioridade)}** prioridades: códigos presentes no EMAIL que não aparecem nas planilhas PRIORIDADES.")
                faltas_df = pd.DataFrame({
                    "CÓD. CLIENTE": faltando_na_prioridade,
                    "HORÁRIO (EMAIL)": [dict_email[c] for c in faltando_na_prioridade]
                })
                st.dataframe(faltas_df, use_container_width=True)
                # Download CSV das faltas
                csv_buf = StringIO()
                faltas_df.to_csv(csv_buf, index=False, encoding="utf-8")
                st.download_button(
                    "Baixar faltas (CSV)",
                    data=csv_buf.getvalue(),
                    file_name="faltas_prioridades_email.csv",
                    mime="text/csv"
                )
            else:
                st.success("Não há faltas: todos os códigos do EMAIL constam nas planilhas PRIORIDADES.")

    # ---------- 3) Atualizar Horários ----------
    st.divider()
    if df_email is not None and df_prior is not None:
        st.subheader("3. Atualizar Horários na Prioridade")
        if st.button("Atualizar Horários"):
            df_prior_atual = atualizar_horarios_prioridades(df_prior, df_email)
            st.session_state["df_prior_atual"] = df_prior_atual
            st.dataframe(df_prior_atual, use_container_width=True)
        else:
            df_prior_atual = st.session_state.get("df_prior_atual", None)
            if df_prior_atual is not None:
                st.dataframe(df_prior_atual, use_container_width=True)
    else:
        df_prior_atual = None

    # ---------- 4) Gerar Bloco ----------
    st.divider()
    if df_prior_atual is not None:
        st.subheader("4. Gerar Bloco por Placa")
        st.caption("Se houver clientes repetidos da mesma base (ex.: 'MIX VALI ...'), o bloco terá apenas 1 ocorrência por base (sem código).")
        if st.button("Gerar Bloco"):
            bloco = gerar_bloco_por_placa(df_prior_atual)
            st.text_area("Bloco Gerado", bloco, height=260)
            st.download_button("Baixar Bloco como TXT", bloco.encode("utf-8"), file_name="bloco_entregas.txt")

    st.info("Dica: Você pode copiar o bloco gerado acima e colar onde desejar.")

# Para integrar no app principal, basta: from seu_modulo import show; show()
if __name__ == "__main__":
    show()
