import streamlit as st
import pandas as pd
import re
from io import StringIO

# AgGrid para edição interativa (opcional)
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
    _HAS_AGGRID = True
except Exception:
    _HAS_AGGRID = False

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
#  🔗 MAPEAMENTO: REDES E SEUS CÓDIGOS
# ============================================================

REDES_CODIGOS = {
    "ASP": "193258,193263,195274,202007,204885,207498,207499,207500,207501,214169,214190,214191",
    "Bergamini": "407,934,8991",
    "Carrefour": "1014,1029,13733,13795,1474,1475,2973,3321,4440,8509,8666,9243,194203,200185,200203,200545,200563,200564,200566,208079,208091,208092,213506",
    "Coopercica": "1037,1038,1044,8637,14466,185619,196986,204187,204939",
    "Covabra": "2516,2534,11552,11554,11617,11618,11619,11623,11625,13168,191577,195788,195790,195791,195797,196723,205138,205692,208510,213991,215486,215487,216679,217278",
    "Divino Fogao": "204009,204182,204210,204235,204282,204283,204309,204310,204546,204734,204736,205161,205402,205573,209210,209730,211896,212972,213671,214961,215619,216157,216158,216256,216496,216981,217399,217542,217727",
    "GIGA": "207277,207318,207319,207320,207335,207336,207337,207338,207279,207280,207281,214011,216261",
    "Infanger": "177924,197060",
    "Irmaos Boa": "3731,3733,6836,8962,13006,187252,187254,187255,187257,191468,195224,195254,195312,196617,203947,203948,212074,214604,214605,214606,216116,216356,216904,217102,217139,217263",
    "Mambo": "3655,3656,3657,9082,12680,13374,192566,195840,200883,207683,209371,209833,210533,213192,216117",
    "Negreiros": "2751,2753,14263,14266,14267,14268,194781,197047,207890,211053",
    "Rede Muffato": "215676,215696,215697,215698",
    "Rede Marche": "11829,11830,11831,12791,12861,158121,158142,166781,178107,178124,197043,202031,203762,205012,211530,211581,211583,211584,211585,211595,211596,211597,211598,211599,211606,211607,211617,211632,211633,211634,211635,214865",
    "SENDAS": "194981,207236,212931",
    "Tenda": "196379,196397,196400,200316,200365",
    "Rossi": "209550,209551,209552,209553,209556,209558,209559,209560,209561,209562,209563,209564,209816,209817,214911,214941",
    "Wal-Mart": "8029,8031,8032,8033,8034,8038,8040,9612,10664,11565,11657,13451,13452,13453,13454,13482,13709,13710,13711,13712,13980,13981,13982,14060,14061,14144,14145,14258,14259,14318,14369,14423,14424,14425,14426,14427,14428,14429,14430,14453,159981,163522,166681,166701,167361,170081,170101,178128,179035,179036,179037,184264,186109,189525,190482,190489,190490,190503,190504,190760,191979,192529,192959,196050,196051,196096",
    "Trimais": "11367,202034,214289,214494,217040",
}

# Constrói dicionário inverso: código → grupo (para busca rápida)
_CODIGO_TO_GRUPO = {}
for rede, codigos_str in REDES_CODIGOS.items():
    for cod in codigos_str.split(","):
        _CODIGO_TO_GRUPO[cod.strip()] = rede

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
    "GIGA": "DAS 09:00 AS 11:00", 
    "INFANGER": "ATE 11:00",
    "IRMAOS BOA": "ATE 15:00",
    "IRMÃOS BOA": "ATE 15:00",
    "IRMAO BOA": "ATE 15:00",
    "MAMBO": "ATE 14:00",
    "NEGREIROS": "ATE 14:00",
    "REDE MARCHE": "ATE 14:00",
    "MARCHE": "ATE 14:00",
    "ROSSI": "ATE 16:00",
    "SENDAS": "ATE 11:00",
    "TENDA": "ATE 11:00",
    "TENDA ATACADO": "ATE 11:00",
    "TRIMAIS": "ATE 11:00",
    "WAL-MART": "ATE 11:00",
    "WAL MART": "ATE 11:00",
    "WALMART": "ATE 11:00",
    "REDE MUFFATO": "ATE 11:00",
}

# ============================================================
#  ⚠️ EXCEÇÕES DE HORÁRIO (mapeamento direto em Python)
#  Códigos que devem sempre receber horário mesmo com 'Grupo = Nenhum'
# ============================================================
HORARIOS_EXCECAO = {
    "12529": "ATE 08:00",
    "191873": "ATE 10:00",
    "217728": "ATE 12:00",
    "217443": "ATE 12:00",
    "216263": "ATE 12:00",
    "11648": "ATE 08:00",
    "211793": "ATE 12:00",
    "204182": "ATE 10:00",
    "198247": "ATE 07:00",
}

def grupo_por_codigo(cod: str) -> str:
    """Retorna o grupo cliente ao buscar pelo código."""
    cod_norm = normaliza_codigo(cod)
    return _CODIGO_TO_GRUPO.get(cod_norm, "")

def horario_por_grupo(grupo: str, cod_cliente: str = "") -> str:
    """Retorna o horário padrão pelo nome do grupo normalizado ou pelo código do cliente."""
    g = normaliza_grupo(grupo)
    for chave, horario in REGRAS_GRUPO.items():
        if chave in g or g.startswith(chave):
            return horario
    
    # Se não encontrou pelo grupo, tenta pelo código do cliente
    if cod_cliente:
        grupo_encontrado = grupo_por_codigo(cod_cliente)
        if grupo_encontrado:
            return horario_por_grupo(grupo_encontrado)
    
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
    try:
        h = int(hh)
    except Exception:
        return ""
    try:
        m = int(mm) if mm is not None and str(mm).strip() != "" else 0
    except Exception:
        return ""
    # Valida intervalo de horas e minutos
    if not (0 <= h <= 23 and 0 <= m <= 59):
        return ""
    return f"{h:02d}:{m:02d}"

def _fmt_compact_to_hm(d: str) -> str:
    if len(d) not in (3, 4):
        return ""
    hh = int(d[:-2].zfill(2))
    mm = int(d[-2:])
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return f"{hh:02d}:{mm:02d}"
    return ""

def extrai_horario(texto: str) -> str:
    """Extrai 'ATE HH:MM', 'AS HH:MM' ou 'DAS HH:MM AS HH:MM' de texto."""
    t = normaliza_horario(texto)

    if (m := _INTERVAL_RE.search(t)):
        h1 = _fmt_hm(m.group('h1'), m.group('m1'))
        h2 = _fmt_hm(m.group('h2'), m.group('m2'))
        if h1 and h2:
            return f"DAS {h1} AS {h2}"

    if (m := _ATE_RE.search(t)):
        h = _fmt_hm(m.group('h'), m.group('m'))
        if h:
            return f"ATE {h}"

    if (m := _AS_RE.search(t)):
        h = _fmt_hm(m.group('h'), m.group('m'))
        if h:
            return f"AS {h}"

    if (m := _TOKEN_RE.search(t)):
        h = _fmt_hm(m.group('h'), m.group('m'))
        if h:
            return f"ATE {h}"

    if (m := _COMPACT_RE.search(t)):
        h = _fmt_compact_to_hm(m.group('d'))
        if h:
            return f"ATE {h}"

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

def enriquecer_grupo_por_codigo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preenche a coluna 'Grupo Cliente' usando o mapeamento de código
    quando o grupo está vazio mas o código existe.
    """
    out = df.copy()
    if "Grupo Cliente" not in out.columns:
        out["Grupo Cliente"] = ""
    
    for idx, row in out.iterrows():
        grupo_atual = str(row.get("Grupo Cliente", "")).strip()
        
        # Se grupo está vazio, tenta encontrar pelo código
        if not grupo_atual or grupo_atual.lower() in ("", "none", "nan", "sem grupo", "nenhum"):
            cod = normaliza_codigo(row.get("Cód. Cliente", "") or row.get("COD CLIENTE", "") or row.get("CODIGO CLIENTE", ""))
            if cod:
                grupo_encontrado = grupo_por_codigo(cod)
                if grupo_encontrado:
                    out.at[idx, "Grupo Cliente"] = grupo_encontrado
    
    return out

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

def atualizar_horarios_prioridades(df_prior: pd.DataFrame, df_email: pd.DataFrame = None) -> pd.DataFrame:
    """
    PRIORIDADE INVERTIDA: EMAIL → Grupo → Código Cliente → SEM HORARIO
    df_prior deve conter: Placa, Nº Ped., Grupo Cliente, Cód. Cliente, Cliente
    df_email é opcional - se None, o sistema só usa Grupo e Código
    """
    dict_email = construir_dict_email(df_email) if df_email is not None and not df_email.empty else {}
    # Carrega exceções embutidas
    dict_excecoes = {normaliza_codigo(k): normaliza_horario(v) for k, v in HORARIOS_EXCECAO.items()}
    horarios, origem = [], []

    # Detecta se a coluna de horário já existe (variações de nome)
    horario_col = None
    if df_prior is not None:
        for c in df_prior.columns:
            if "HORARIO" in _sem_acentos_upper(c):
                horario_col = c
                break

    for _, row in df_prior.iterrows():
        grupo = row.get("Grupo Cliente", "") or row.get("GRUPO CLIENTE", "") or ""
        cod   = normaliza_codigo(row.get("Cód. Cliente", "") or row.get("COD CLIENTE", "") or row.get("CODIGO CLIENTE", ""))

        gnorm = normaliza_grupo(grupo)
        if gnorm in ("NENHUM", "NONE", "SEM GRUPO"):
            gnorm = ""

        # 0) Se a planilha já trouxe um horário válido por linha, preserva ele
        if horario_col:
            hora_planilha = normaliza_horario(row.get(horario_col, "") or "")
            if hora_planilha and hora_planilha.upper().strip() not in ("", "SEM HORARIO"):
                horarios.append(hora_planilha)
                origem.append("Planilha")
                continue

        # 0.5) Se existe exceção registrada para este código, aplica ela
        if cod and cod in dict_excecoes:
            horarios.append(dict_excecoes[cod])
            origem.append("Registro")
            continue

        # 1) Prioriza o horário vindo do EMAIL (se existir)
        if cod in dict_email and dict_email[cod].strip():
            horarios.append(dict_email[cod])
            origem.append("EMAIL")
            continue

        # 2) Tenta encontrar horário pelo grupo, e se não achar, tenta pelo código
        hora_grupo = horario_por_grupo(gnorm, cod)
        if hora_grupo:
            origem_label = "Grupo Cliente" if gnorm else "Código Cliente"
            horarios.append(hora_grupo)
            origem.append(origem_label)
        else:
            # Se não encontrou pelo nome do grupo, tenta diretamente pelo código do cliente
            if cod:
                grupo_via_codigo = grupo_por_codigo(cod)
                if grupo_via_codigo:
                    hora_via_codigo = horario_por_grupo(grupo_via_codigo)
                    if hora_via_codigo:
                        horarios.append(hora_via_codigo)
                        origem.append("Código Cliente")
                        continue

            horarios.append("SEM HORARIO")
            origem.append("SEM HORARIO")

    out = df_prior.copy()
    out["Horário"] = horarios
    out["Origem Horário"] = origem
    return out

# ============================================================
#  🔍 DETECÇÃO DE NOVAS REDES
# ============================================================

def detectar_redes_novas(df_prior: pd.DataFrame) -> dict:
    """
    Detecta códigos novos para redes existentes ou redes completamente novas.
    Para redes conhecidas: códigos presentes na planilha mas não no mapeamento.
    Para redes novas: todos os códigos não mapeados.
    Retorna dict: {rede: "cod_novo1,cod_novo2,..."}
    """
    redes_conhecidas_norm = {normaliza_grupo(rede): rede for rede in REDES_CODIGOS.keys()}
    codigos_por_rede_norm = {normaliza_grupo(rede): set(codigos_str.split(",")) for rede, codigos_str in REDES_CODIGOS.items()}
    codigos_conhecidos = set(_CODIGO_TO_GRUPO.keys())
    redes_atualizacoes = {}
    
    if df_prior is None or df_prior.empty:
        return redes_atualizacoes
    
    # Agrupa por Grupo Cliente e coleta códigos
    for grupo_cliente in df_prior["Grupo Cliente"].unique():
        if not grupo_cliente or str(grupo_cliente).lower() in ("", "none", "nan"):
            continue
        
        grupo_str = str(grupo_cliente).strip()
        grupo_norm = normaliza_grupo(grupo_str)
        
        # Coleta códigos desta rede na planilha
        codigos_planilha = set(df_prior[df_prior["Grupo Cliente"] == grupo_cliente]["Cód. Cliente"].unique())
        codigos_planilha.discard("")  # Remove vazios
        
        if grupo_norm in redes_conhecidas_norm:
            # Rede conhecida: encontra códigos novos (na planilha mas não no mapeamento)
            codigos_conhecidos_rede = codigos_por_rede_norm[grupo_norm]
            codigos_novos = codigos_planilha - codigos_conhecidos_rede
            if codigos_novos:
                codigos_sorted = sorted(codigos_novos, key=lambda x: int(x) if x.isdigit() else 0)
                redes_atualizacoes[grupo_str] = ",".join(codigos_sorted)
        else:
            # Rede nova: todos os códigos não mapeados em nenhuma rede
            codigos_novos = codigos_planilha - codigos_conhecidos
            if codigos_novos:
                codigos_sorted = sorted(codigos_novos, key=lambda x: int(x) if x.isdigit() else 0)
                redes_atualizacoes[grupo_str] = ",".join(codigos_sorted)
    
    return redes_atualizacoes

# ============================================================
#  🧾 GERAÇÃO DO BLOCO FINAL POR PLACA
#     Regra: se houver clientes "repetidos" de mesma base (ex.: MIX VALI ...),
#     omitir o CÓDIGO e exibir apenas 1 ocorrência (NOME + HORÁRIO) por base.
#     Ordena por horário: mais cedo → mais tarde
# ============================================================

def _extrair_hora_para_ordenacao(horario_str: str) -> tuple:
    """
    Extrai a hora inicial do horário para ordenação.
    Ex: "ATE 11:00" → (11, 0)
        "DAS 09:00 AS 11:00" → (9, 0)
        "SEM HORARIO" → (24, 0)  # vai por último
    """
    h_upper = str(horario_str).upper().strip()
    
    if "SEM HORARIO" in h_upper or not h_upper:
        return (24, 0)  # Coloca no final
    
    # Extrai horário com regex
    m = re.search(r'(\d{1,2}):(\d{2})', h_upper)
    if m:
        h, m_val = int(m.group(1)), int(m.group(2))
        return (h, m_val)
    
    return (24, 0)

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
        # - valor: (string formatada, hora_para_ordenacao)
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
                item_str = f"{nome_curto} ENTREGAR {hora}"
                hora_order = _extrair_hora_para_ordenacao(hora)
                itens_fmt.append((item_str, hora_order))

        # 2) Itens de bases não repetidas: mantém com código
        bases_repetidas = {b for b, gbase in base_groups.items() if b and len(gbase) >= 2}
        unicos = grupo[~grupo["_BaseKey"].isin(bases_repetidas)]
        for _, row in unicos.iterrows():
            cod = row["Cód. Cliente"]
            nome = row["_ClienteExib"]
            hora = row["Horário"] if row["Horário"] else "SEM HORARIO"
            item_str = f"{cod} - {nome} ENTREGAR {hora}"
            hora_order = _extrair_hora_para_ordenacao(hora)
            itens_fmt.append((item_str, hora_order))

        # Remove duplicatas exatas por segurança mantendo a ordem
        vistos = set()
        itens_unicos = []
        for it, hora_ord in itens_fmt:
            if it not in vistos:
                itens_unicos.append((it, hora_ord))
                vistos.add(it)

        # Ordena por horário (mais cedo primeiro)
        itens_unicos.sort(key=lambda x: x[1])

        # Extrai apenas a string após ordenação
        itens_ordenados = [it for it, _ in itens_unicos]

        blocos.append(f"{placa}:\n{' | '.join(itens_ordenados)}\n")

    return "\n".join(blocos)

# ============================================================
#  🖥 INTERFACE STREAMLIT
# ============================================================

def show():
    # ======== Estilos específicos da página (Material / One UI feel) ========
    st.markdown("""
    <style>
    .cp-hero{display:flex;align-items:center;gap:1rem;margin-bottom:0.6rem}
    .cp-hero-icon{font-size:2.8rem;padding:0;margin:0;border-radius:0;background:none;color:#FFB800}
    .cp-hero-title{font-size:1.6rem;font-weight:700}
    .cp-sub{color:#666;margin-top:-6px}
    .cp-card{background:var(--bg-card,#ffffff);border-radius:12px;padding:1rem;margin-bottom:1rem;box-shadow:0 6px 18px rgba(32,33,36,0.06)}
    .cp-grid{display:flex;gap:1rem}
    .cp-metric{background:linear-gradient(180deg,#fff,#fafafa);padding:0.7rem;border-radius:10px;text-align:center}
    .cp-btn{background:#1976d2;color:white;border-radius:10px;padding:8px 14px;border:none}
    .cp-accent{color:#1976d2;font-weight:600}
    </style>
    """, unsafe_allow_html=True)

    # Hero
    col0, col1 = st.columns([0.12, 1])
    with col0:
        st.markdown("<div class='cp-hero-icon'>⭐</div>", unsafe_allow_html=True)
    with col1:
        st.markdown("<div class='cp-hero-title'>Prioridades — Cliente & Horários</div>", unsafe_allow_html=True)
        st.markdown("<div class='cp-sub'>Importe o EMAIL e planilhas, aplique regras e gere o bloco por placa.</div>", unsafe_allow_html=True)

    st.markdown("<div class='cp-card'>", unsafe_allow_html=True)

    # Preparar variáveis que serão usadas nas abas
    df_email = None
    df_prior = None
    df_prior_atual = st.session_state.get("df_prior_atual", None)

    tabs = st.tabs(["📧 Email", "📋 Prioridades", "⏱ Atualizar Horários", "🧾 Bloco"])

    # ---------- Aba Email ----------
    with tabs[0]:
        st.subheader("Cole a coluna do EMAIL")
        email_text = st.text_area("Cole aqui (uma linha por código):", height=180, key="email_text")
        if email_text and email_text.strip():
            df_email = importar_email_cru_from_text(email_text)
            st.success("EMAIL processado com sucesso ✨")
            c1, c2, c3 = st.columns([1,1,2])
            c1.markdown(f"<div class='cp-metric'><div class='cp-accent'>Códigos</div><div style='font-size:18px;font-weight:700'>{len(df_email)}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='cp-metric'><div class='cp-accent'>Com horário</div><div style='font-size:18px;font-weight:700'>{int((df_email['HORÁRIO'].str.strip() != '').sum())}</div></div>", unsafe_allow_html=True)
            c3.dataframe(df_email, use_container_width=True)
        else:
            st.info("Cole os dados do EMAIL acima. Exemplos: '123456 - ATE 11:00' ou '123456\t11:00'.")

    # ---------- Aba Prioridades (upload) ----------
    with tabs[1]:
        st.subheader("Upload das Planilhas PRIORIDADES")
        prior_file_clients = st.file_uploader("Planilha Clientes Prioridades", type=["xlsx", "csv"], key="prior_file_clients")
        prior_file_redes = st.file_uploader("Planilha Redes Prioridades (opcional)", type=["xlsx", "csv"], key="prior_file_redes")

        frames = []
        if prior_file_clients:
            df1 = pd.read_excel(prior_file_clients, dtype=str) if prior_file_clients.name.lower().endswith(".xlsx") else pd.read_csv(prior_file_clients, dtype=str)
            df1 = limpar_linhas_resumo(df1)
            frames.append(df1)
            st.success("Clientes importados ✔️")
            st.dataframe(df1, use_container_width=True)

        if prior_file_redes:
            df2 = pd.read_excel(prior_file_redes, dtype=str) if prior_file_redes.name.lower().endswith(".xlsx") else pd.read_csv(prior_file_redes, dtype=str)
            df2 = limpar_linhas_resumo(df2)
            frames.append(df2)
            st.success("Redes importadas ✔️")
            st.dataframe(df2, use_container_width=True)

        if frames:
            df_prior = pd.concat(frames, ignore_index=True, sort=False)
            df_prior = limpar_linhas_resumo(df_prior)
            # normalizações já existentes
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
            if cols_map:
                df_prior = df_prior.rename(columns=cols_map)
            if "Cód. Cliente" in df_prior.columns:
                df_prior["Cód. Cliente"] = df_prior["Cód. Cliente"].astype(str).apply(normaliza_codigo)
            if "Placa" in df_prior.columns:
                df_prior["Placa"] = df_prior["Placa"].astype(str).str.upper().str.strip()
            df_prior = enriquecer_grupo_por_codigo(df_prior)
            st.success("Planilhas combinadas e normalizadas 🚀")
            # Mostra tabela editável com AgGrid quando disponível
            if _HAS_AGGRID:
                gb = GridOptionsBuilder.from_dataframe(df_prior)
                gb.configure_default_column(editable=True, resizable=True)
                gb.configure_grid_options(domLayout='autoHeight')
                grid_options = gb.build()
                grid_response = AgGrid(
                    df_prior,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.MODEL_CHANGED,
                    fit_columns_on_grid_load=True,
                    enable_enterprise_modules=False,
                )
                try:
                    df_prior = pd.DataFrame(grid_response['data'])
                    # Salva versão editada em sessão para uso posterior
                    st.session_state['df_prior_cached'] = df_prior
                    st.success('Tabela editável salva na sessão.')
                except Exception:
                    st.warning('Não foi possível capturar alterações da tabela.')
            else:
                st.dataframe(df_prior, use_container_width=True)

            redes_atualizacoes = detectar_redes_novas(df_prior)
            if redes_atualizacoes:
                with st.expander("🔍 Códigos novos detectados", expanded=False):
                    st.warning(f"Encontrados códigos novos para {len(redes_atualizacoes)} rede(s)")
                    for rede_nome, codigos in redes_atualizacoes.items():
                        st.code(f'"{rede_nome}": "{codigos}",', language="python")

        else:
            st.info("Faça upload das planilhas para combiná-las e ver diagnósticos.")

    # ---------- Aba Atualizar Horários ----------
    with tabs[2]:
        st.subheader("Atualizar Horários na Prioridade")
        st.caption("Use o EMAIL (se houver) para priorizar horários — caso contrário, serão aplicadas regras padrão de Grupo/Código.")
        if st.button("Atualizar Horários"):
            # recomputa df_prior a partir do uploader state
            prior_state = st.session_state.get('prior_file_clients', None)
            # Usa a lógica já implementada: tentamos recombinar se houver upload
            if 'prior_file_clients' in st.session_state and st.session_state['prior_file_clients'] is not None:
                # Re-executar leitura simples: rely on widget values above to set df_prior
                st.info("Processando... aguarde")
            df_email_local = None
            if st.session_state.get('email_text'):
                df_email_local = importar_email_cru_from_text(st.session_state.get('email_text'))
            # Tentativa simples: se já existia df_prior em sessão, usa ele
            df_prior_session = None
            # Recria df_prior se possível (confiando no fluxo da aba 'Prioridades')
            try:
                # if user uploaded, the dataframe will be visible in the previous tab; try to read from uploaded file again
                pass
            except Exception:
                pass

            # Use session stored previous result if present
            df_prior_session = st.session_state.get('df_prior_cached', None)
            if df_prior_session is None:
                st.info("Nenhuma planilha processada encontrada. Faça upload nas Prioridades.")
            else:
                df_prior_atual = atualizar_horarios_prioridades(df_prior_session, df_email_local)
                st.session_state['df_prior_atual'] = df_prior_atual
                st.success("Horários atualizados ✅")
                st.dataframe(df_prior_atual, use_container_width=True)

    # ---------- Aba Bloco / Export ----------
    with tabs[3]:
        st.subheader("Gerar Bloco por Placa")
        st.caption("Gere o bloco final por placa para copiar/baixar.")
        df_prior_atual = st.session_state.get('df_prior_atual', None)
        if df_prior_atual is None:
            st.info("Atualize os horários primeiro na aba 'Atualizar Horários'.")
        else:
            if st.button("Gerar Bloco"):
                bloco = gerar_bloco_por_placa(df_prior_atual)
                st.text_area("Bloco Gerado", bloco, height=260)
                st.download_button("Baixar Bloco como TXT", bloco.encode("utf-8"), file_name="bloco_entregas.txt")

    st.markdown("</div>", unsafe_allow_html=True)

# Para integrar no app principal, basta: from seu_modulo import show; show()
if __name__ == "__main__":
    show()
