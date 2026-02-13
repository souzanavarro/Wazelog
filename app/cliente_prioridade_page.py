import streamlit as st
import pandas as pd
import io
import re

def normaliza_codigo(cod):
    return ''.join(re.findall(r'\d+', str(cod).strip()))

def normaliza_horario(h):
    # Normaliza variantes e espaços
    s = str(h).strip().upper()
    # normaliza acentos e termos mais comuns
    s = (s.replace("ATÉ", "ATE")
           .replace("ÀS", "AS")
           .replace("À", "A")
           .replace("Ã", "A").replace("Á", "A").replace("Â", "A").replace("À", "A")
           .replace("É", "E").replace("Ê", "E").replace("Í", "I")
           .replace("Ó", "O").replace("Ô", "O").replace("Õ", "O")
           .replace("Ú", "U").replace("Ç", "C"))
    # padroniza separadores e remove duplicidades de espaço
    s = s.replace("\u00A0", " ")  # NBSP
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normaliza_grupo(grupo):
    s = str(grupo).strip().upper()
    s = (s.replace("Ã", "A").replace("Á", "A").replace("Â", "A").replace("À", "A")
           .replace("É", "E").replace("Ê", "E").replace("Í", "I")
           .replace("Ó", "O").replace("Ô", "O").replace("Õ", "O")
           .replace("Ú", "U").replace("Ç", "C"))
    while "  " in s:
        s = s.replace("  ", " ")
    return s

def horario_por_grupo(grupo):
    g = normaliza_grupo(grupo)
    if "MARCHE" in g: return "ATE 15:00"
    if "CARREFOUR" in g: return "ATE 11:00"
    if "ASP" in g: return "ATE 12:00"
    if "GIGA" in g: return "DAS 09:00 ATE 11:00"
    if "TENDA ATACADO" in g or "TENDA" in g: return "ATE 11:00"
    if "COVABRA" in g: return "ATE 12:00"
    if "IRMAOS BOA" in g or "IRMAOS" in g or "BOA" in g: return "ATE 13:00"
    if "WAL-MART" in g or "WAL MART" in g or "WALMART" in g: return "ATE 11:00"
    if "BERGAMINI" in g: return "ATE 11:00"
    if "TRIMAIS" in g or "SABORES TRIMAIS" in g: return "ATE 11:00"
    return ""

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
    return out.strip()

# --------- Parsers robustos para o EMAIL ---------
_sep_regex = re.compile(r'[-–—;,\t|]')  # separadores comuns

def _split_codigo_hora(linha: str):
    """Aceita formatos: 
       123456 - ATE 11:00
       123456;ATE 11:00
       123456<TAB>ATE 11:00
       123456    ATE 11:00  (múltiplos espaços)
       123456 ATE 11:00     (se segunda parte 'parece horário')
    """
    ln = (linha or "").replace("\u00A0", " ").strip()
    ln = ln.replace("–", "-").replace("—", "-")

    # 1) Separadores explícitos: -, ; , , tab, |
    if _sep_regex.search(ln):
        parts = _sep_regex.split(ln, maxsplit=1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()

    # 2) Múltiplos espaços (padrão colagem do Excel)
    m = re.match(r'^\s*(\d{3,})\s{2,}(.+?)\s*$', ln)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # 3) Um espaço apenas, se a direita "parece horário"
    m = re.match(r'^\s*(\d{3,})\s+(.+?)\s*$', ln)
    if m:
        direita = m.group(2).strip()
        if re.search(r'(\d{1,2}[:h]\d{2}|ATE|ATÉ|DAS|AS)', direita, re.I):
            return m.group(1).strip(), direita

    # 4) fallback: só código
    return ln, ""

def importar_email_cru(df_email):
    # df_email pode vir com 1 coluna (A) ou 2 colunas (cod/horario)
    df = df_email.copy()
    if df.shape[1] == 1:
        df.columns = ["A"]
        fontes = df["A"].astype(str).tolist()
        cods, horas = [], []
        for txt in fontes:
            cod, hora = _split_codigo_hora(txt)
            cod_norm = normaliza_codigo(cod)
            if cod_norm:
                cods.append(cod_norm)
                horas.append(normaliza_horario(hora))
        return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

    # 2+ colunas: tenta mapear cabeçalhos
    cols_map = {}
    for c in df.columns:
        cname = str(c).strip().upper()
        if ("COD" in cname or "CÓD" in cname) and "CLIENTE" in cname:
            cols_map[c] = "CÓD. CLIENTE"
        elif "HOR" in cname:
            cols_map[c] = "HORÁRIO"
        elif cname in ("A", "COLUNA A"):
            cols_map[c] = "A"

    if cols_map:
        df = df.rename(columns=cols_map)

    # Se não tem as duas colunas, tenta reconstruir a partir de "A"
    if not {"CÓD. CLIENTE", "HORÁRIO"}.issubset(df.columns):
        if "A" in df.columns:
            fontes = df["A"].astype(str).tolist()
            cods, horas = [], []
            for txt in fontes:
                cod, hora = _split_codigo_hora(txt)
                cod_norm = normaliza_codigo(cod)
                if cod_norm:
                    cods.append(cod_norm)
                    horas.append(normaliza_horario(hora))
            return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

    # Se já tem as duas, só normaliza
    df["CÓD. CLIENTE"] = df["CÓD. CLIENTE"].astype(str).apply(normaliza_codigo)
    df["HORÁRIO"] = df["HORÁRIO"].astype(str).apply(normaliza_horario)
    df = df[df["CÓD. CLIENTE"] != ""]
    return df[["CÓD. CLIENTE", "HORÁRIO"]].reset_index(drop=True)

def importar_email_cru_from_text(texto):
    linhas = (texto or "").strip().splitlines()
    cods, horas = [], []
    for linha in linhas:
        if not linha.strip():
            continue
        cod, hora = _split_codigo_hora(linha)
        cod_norm = normaliza_codigo(cod)
        if cod_norm:
            cods.append(cod_norm)
            horas.append(normaliza_horario(hora))
    return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

def atualizar_horarios_prioridades(df_prior, df_email):
    # df_prior: DataFrame com colunas: Placa, Nº Ped., Grupo Cliente, Cód. Cliente, Cliente, Horário
    # df_email: DataFrame com colunas: CÓD. CLIENTE, HORÁRIO
    dict_email = {
        normaliza_codigo(row["CÓD. CLIENTE"]): normaliza_horario(row["HORÁRIO"])
        for _, row in df_email.iterrows()
        if normaliza_codigo(row["CÓD. CLIENTE"])
    }
    horarios = []
    origem = []
    for _, row in df_prior.iterrows():
        grupo = row.get("Grupo Cliente", "") or row.get("GRUPO CLIENTE", "") or ""
        cod = normaliza_codigo(row.get("Cód. Cliente", "") or row.get("COD CLIENTE", ""))
        hora_grupo = horario_por_grupo(grupo)
        if hora_grupo:
            horarios.append(hora_grupo)
            origem.append("Grupo Cliente")
        elif cod in dict_email and dict_email[cod].strip():
            horarios.append(dict_email[cod])
            origem.append("EMAIL")
        else:
            horarios.append("SEM HORARIO")
            origem.append("SEM HORARIO")
    df_prior = df_prior.copy()
    df_prior["Horário"] = horarios
    df_prior["Origem Horário"] = origem
    return df_prior

def gerar_bloco_por_placa(df_prior):
    # Agrupa por placa, monta linhas do bloco
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
            item = f"{cod} - {cliente} ENTREGAR {hora}"
            itens.append(item)
        linha = " | ".join(itens)
        blocos.append(f"{placa}:\n{linha}\n")
    return "\n".join(blocos)

def show():
    st.header("Cliente Prioridade", divider="rainbow")
    st.write("Automação de prioridades: importa e-mails, aplica regras de horário por grupo/cliente e gera bloco por placa.")

    st.subheader("1. Informe os dados do EMAIL")
    st.caption("Aceita formatos: 'COD - ATE 11:00', 'COD;ATE 11:00', 'COD\\tATE 11:00', 'COD    ATE 11:00' ou 'COD ATE 11:00'.")
    email_text = st.text_area(
        "Cole aqui o conteúdo da planilha EMAIL (coluna A: texto ou CÓD. CLIENTE/HORÁRIO, um por linha):",
        height=200,
        key="email_text"
    )
    df_email = None
    if email_text.strip():
        df_email = importar_email_cru_from_text(email_text)
        st.success("EMAIL processado da caixa de texto.")
        st.dataframe(df_email, use_container_width=True)
    else:
        st.info("Cole os dados do EMAIL acima.")

    st.subheader("2. Upload das Planilhas PRIORIDADES")
    prior_file_clients = st.file_uploader("Planilha Clientes Prioridades", type=["xlsx", "csv"], key="prior_file_clients")
    prior_file_redes = st.file_uploader("Planilha Redes Prioridades (opcional)", type=["xlsx", "csv"], key="prior_file_redes")
    df_prior = None
    df_prior_clients = None
    df_prior_redes = None
    if prior_file_clients:
        if prior_file_clients.name.endswith(".xlsx"):
            df_prior_clients = pd.read_excel(prior_file_clients)
        else:
            df_prior_clients = pd.read_csv(prior_file_clients)
        st.success("PRIORIDADES (Clientes) importada.")
        st.dataframe(df_prior_clients, use_container_width=True)
    if prior_file_redes:
        if prior_file_redes.name.endswith(".xlsx"):
            df_prior_redes = pd.read_excel(prior_file_redes)
        else:
            df_prior_redes = pd.read_csv(prior_file_redes)
        st.success("PRIORIDADES (Redes) importada.")
        st.dataframe(df_prior_redes, use_container_width=True)

    # Combina as duas planilhas (se existirem) e remove duplicados por Cód. Cliente + Placa
    if df_prior_clients is not None or df_prior_redes is not None:
        frames = []
        if df_prior_clients is not None:
            frames.append(df_prior_clients)
        if df_prior_redes is not None:
            frames.append(df_prior_redes)
        df_prior = pd.concat(frames, ignore_index=True, sort=False)

        # Normaliza nomes de colunas comuns (variações vindas das planilhas)
        cols_map = {}
        for c in df_prior.columns:
            cname = str(c).strip().upper()
            if ("COD" in cname or "CÓD" in cname) and "CLIENTE" in cname:
                cols_map[c] = "Cód. Cliente"
            elif "PLACA" in cname:
                cols_map[c] = "Placa"
            elif "GRUPO" in cname and "CLIENTE" in cname:
                cols_map[c] = "Grupo Cliente"
            elif cname in ("CLIENTE", "NOME CLIENTE", "NOME DO CLIENTE", "CLIENTE NOME"):
                cols_map[c] = "Cliente"
            elif (("Nº" in c) or ("NO" in cname) or ("NUM" in cname)) and ("PED" in cname):
                cols_map[c] = "Nº Ped."

        if cols_map:
            df_prior = df_prior.rename(columns=cols_map)

        # Garante colunas mínimas e normaliza valores
        if "Cód. Cliente" in df_prior.columns:
            df_prior["Cód. Cliente"] = df_prior["Cód. Cliente"].astype(str).apply(normaliza_codigo)
        if "Placa" in df_prior.columns:
            df_prior["Placa"] = df_prior["Placa"].astype(str).str.upper().str.strip()
        if "Cliente" in df_prior.columns:
            df_prior["Cliente"] = df_prior["Cliente"].astype(str).str.strip()

        # Remove duplicatas pelo par (Cód. Cliente, Placa)
        if "Cód. Cliente" in df_prior.columns and "Placa" in df_prior.columns:
            antes = len(df_prior)
            df_prior = df_prior.drop_duplicates(subset=["Cód. Cliente", "Placa"])
            removidos = antes - len(df_prior)
            if removidos > 0:
                st.success(f"Removidos {removidos} registros duplicados (mesmo Cód. Cliente + mesma Placa).")

        st.success("Planilhas combinadas.")
        st.dataframe(df_prior, use_container_width=True)

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

    st.divider()
    if df_prior_atual is not None:
        st.subheader("4. Gerar Bloco por Placa")
        if st.button("Gerar Bloco"):
            bloco = gerar_bloco_por_placa(df_prior_atual)
            st.text_area("Bloco Gerado", bloco, height=200)
            st.download_button("Baixar Bloco como TXT", bloco.encode("utf-8"), file_name="bloco_entregas.txt")
        else:
            bloco = None

    st.info("Dica: Você pode copiar o bloco gerado acima e colar onde desejar.")

# Para integração no app principal, basta importar e chamar show()
