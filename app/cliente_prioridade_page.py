import streamlit as st
import pandas as pd
import io
import re

def normaliza_codigo(cod):
    return ''.join(re.findall(r'\d+', str(cod).strip()))

def normaliza_horario(h):
    s = str(h).strip().upper().replace("ATÉ", "ATE")
    while "  " in s:
        s = s.replace("  ", " ")
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
    if "MARCHE" in g: return "ATE 11:00"
    if "CARREFOUR" in g: return "ATE 11:00"
    if "ASP" in g: return "ATE 12:00"
    if "GIGA" in g: return "DAS 09:00 ATE 11:00"
    if "TENDA ATACADO" in g or "TENDA" in g: return "ATE 11:00"
    if "COVABRA" in g: return "ATE 12:00"
    if "IRMAOS BOA" in g or "IRMÃOS BOA" in g or "BOA" in g: return "ATE 15:00"
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

def importar_email_cru(df_email):
    # Espera coluna A com texto tipo "COD - HORARIO"
    df = df_email.copy()
    if df.shape[1] == 1:
        df.columns = ["A"]
    df["A"] = df["A"].astype(str).str.replace("–", "-").str.replace("—", "-")
    cods, horas = [], []
    for txt in df["A"]:
        txt = txt.strip()
        if not txt:
            cods.append("")
            horas.append("")
            continue
        p = txt.find("-")
        if p > 0:
            cod = txt[:p].strip()
            hora = txt[p+1:].strip()
        else:
            cod = txt
            hora = ""
        cods.append(normaliza_codigo(cod))
        horas.append(normaliza_horario(hora))
    return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

def importar_email_cru_from_text(texto):
    linhas = texto.strip().splitlines()
    cods, horas = [], []
    for linha in linhas:
        linha = linha.strip().replace("–", "-").replace("—", "-")
        if not linha:
            continue
        p = linha.find("-")
        if p > 0:
            cod = linha[:p].strip()
            hora = linha[p+1:].strip()
        else:
            cod = linha
            hora = ""
        cods.append(normaliza_codigo(cod))
        horas.append(normaliza_horario(hora))
    return pd.DataFrame({"CÓD. CLIENTE": cods, "HORÁRIO": horas})

def atualizar_horarios_prioridades(df_prior, df_email):
    # df_prior: DataFrame com colunas: Placa, Nº Ped., Grupo Cliente, Cód. Cliente, Cliente, Horário
    # df_email: DataFrame com colunas: CÓD. CLIENTE, HORÁRIO
    dict_email = {normaliza_codigo(row["CÓD. CLIENTE"]): normaliza_horario(row["HORÁRIO"])
                  for _, row in df_email.iterrows() if normaliza_codigo(row["CÓD. CLIENTE"]) and normaliza_horario(row["HORÁRIO"])}
    horarios = []
    origem = []
    for _, row in df_prior.iterrows():
        grupo = row.get("Grupo Cliente", "")
        cod = normaliza_codigo(row.get("Cód. Cliente", ""))
        hora_grupo = horario_por_grupo(grupo)
        if hora_grupo:
            horarios.append(hora_grupo)
            origem.append("Grupo Cliente")
        elif cod in dict_email:
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
            hora = row["Horário"]
            if not hora:
                hora = "SEM HORARIO"
            item = f"{cod} - {cliente} ENTREGAR {hora}"
            itens.append(item)
        linha = " | ".join(itens)
        blocos.append(f"{placa}:\n{linha}\n")
    return "\n".join(blocos)

def show():
    st.header("Cliente Prioridade", divider="rainbow")
    st.write("Automação de prioridades: importa e-mails, aplica regras de horário por grupo/cliente e gera bloco por placa.")

    st.subheader("1. Informe os dados do EMAIL")
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

    st.subheader("2. Upload da Planilha PRIORIDADES")
    prior_file = st.file_uploader("Planilha PRIORIDADES", type=["xlsx", "csv"], key="prior_file")
    df_prior = None
    if prior_file:
        if prior_file.name.endswith(".xlsx"):
            df_prior = pd.read_excel(prior_file)
        else:
            df_prior = pd.read_csv(prior_file)
        st.success("PRIORIDADES importada.")
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
