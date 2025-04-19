import streamlit as st
import pandas as pd
import os
import json
from streamlit_folium import folium_static
import folium
import random
from core.core_clusterizacao import clusterizar_pedidos_kmeans, clusterizar_pedidos_dbscan, priorizar_clusters
from core.core_exportacao import exportar_rotas_json, exportar_rotas_excel
from core.core_feedback import registrar_feedback, carregar_feedback

def carregar_configuracoes():
    """
    Carrega as configurações salvas do roteirizador.
    """
    caminho_config = "database/configuracoes_roteirizador.json"
    if os.path.exists(caminho_config):
        with open(caminho_config, "r") as f:
            return json.load(f)
    return {}

def salvar_configuracoes(config):
    """
    Salva as configurações do roteirizador em um arquivo JSON.
    """
    caminho_config = "database/configuracoes_roteirizador.json"
    os.makedirs(os.path.dirname(caminho_config), exist_ok=True)
    with open(caminho_config, "w") as f:
        json.dump(config, f, indent=4)

def carregar_dados_pedidos():
    """
    Carrega os dados de pedidos do banco de dados.
    """
    caminho_pedidos = "database/pedidos.csv"
    if os.path.exists(caminho_pedidos):
        return pd.read_csv(caminho_pedidos)
    else:
        st.error("Nenhum pedido encontrado. Certifique-se de que os pedidos foram cadastrados.")
        return pd.DataFrame()

def carregar_dados_frota():
    """
    Carrega os dados da frota do banco de dados.
    """
    caminho_frota = "database/frota.csv"
    if os.path.exists(caminho_frota):
        return pd.read_csv(caminho_frota)
    else:
        st.error("Nenhuma frota encontrada. Certifique-se de que a frota foi cadastrada.")
        return pd.DataFrame()

def separar_por_regiao(pedidos, metodo="kmeans", n_clusters=5, eps=0.5, min_samples=5, criterio_prioridade="volume_total"):
    """
    Realiza a separação de pedidos por região usando clusterização.

    :param pedidos: DataFrame com colunas 'Latitude' e 'Longitude'.
    :param metodo: Método de clusterização ('kmeans', 'dbscan' ou 'regiao_predefinida').
    :param n_clusters: Número de clusters (apenas para KMeans).
    :param eps: Distância máxima entre pontos (apenas para DBSCAN).
    :param min_samples: Número mínimo de pontos para formar um cluster (apenas para DBSCAN).
    :param criterio_prioridade: Critério para priorizar clusters ('volume_total' ou 'urgencia').
    :return: DataFrame com clusters atribuídos e priorizados.
    """
    if metodo == "kmeans":
        pedidos = clusterizar_pedidos_kmeans(pedidos, n_clusters=n_clusters)
    elif metodo == "dbscan":
        pedidos = clusterizar_pedidos_dbscan(pedidos, eps=eps, min_samples=min_samples)
    elif metodo == "regiao_predefinida":
        if "Regiao" not in pedidos.columns:
            raise ValueError("A coluna 'Regiao' é necessária para o método 'regiao_predefinida'.")
    else:
        raise ValueError("Método de clusterização não suportado.")

    # Priorizar clusters
    pedidos = priorizar_clusters(pedidos, criterio=criterio_prioridade)
    return pedidos

def preparar_dados_para_roteirizacao(pedidos, frota, config):
    """
    Prepara os dados de pedidos e frota para a roteirização.
    """
    # Filtrar veículos disponíveis
    frota_disponivel = frota[frota["Disponível"].str.lower() == "sim"]

    # Verificar se há veículos disponíveis
    if frota_disponivel.empty:
        st.error("Nenhum veículo disponível na frota.")
        return None, None

    # Verificar se há pedidos com coordenadas válidas
    pedidos_validos = pedidos.dropna(subset=["Latitude", "Longitude"])
    if pedidos_validos.empty:
        st.error("Nenhum pedido com coordenadas válidas encontrado.")
        return None, None

    # Aplicar restrições e preferências
    if config.get("capacidade"):
        pedidos_validos = pedidos_validos[pedidos_validos["Peso dos Itens"] <= frota_disponivel["Capac. Kg"].max()]

    # Separar pedidos por região/clusterização
    metodo_clusterizacao = config.get("metodo_clusterizacao", "kmeans")
    n_clusters = config.get("n_clusters", 5)
    eps = config.get("eps", 0.5)
    min_samples = config.get("min_samples", 5)
    criterio_prioridade = config.get("criterio_prioridade", "volume_total")

    pedidos_validos = separar_por_regiao(
        pedidos_validos,
        metodo=metodo_clusterizacao,
        n_clusters=n_clusters,
        eps=eps,
        min_samples=min_samples,
        criterio_prioridade=criterio_prioridade
    )

    return pedidos_validos, frota_disponivel

def visualizar_rotas_no_mapa(rotas, pedidos, ponto_partida):
    """
    Visualiza as rotas no mapa usando Folium.
    """
    st.markdown("### 🌍 Visualização das Rotas no Mapa")
    mapa = folium.Map(location=[ponto_partida["Latitude"], ponto_partida["Longitude"]], zoom_start=12)

    # Adicionar ponto de partida
    folium.Marker(
        location=[ponto_partida["Latitude"], ponto_partida["Longitude"]],
        popup="Ponto de Partida",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(mapa)

    # Adicionar rotas
    for i, rota in enumerate(rotas):
        rota_coords = [[ponto_partida["Latitude"], ponto_partida["Longitude"]]] + [
            [pedidos.iloc[node - 1]["Latitude"], pedidos.iloc[node - 1]["Longitude"]] for node in rota[1:-1]
        ] + [[ponto_partida["Latitude"], ponto_partida["Longitude"]]]

        folium.PolyLine(rota_coords, color="blue", weight=2.5, opacity=0.8, tooltip=f"Rota Veículo {i + 1}").add_to(mapa)

        for coord in rota_coords[1:-1]:
            folium.Marker(location=coord, icon=folium.Icon(color="red", icon="truck")).add_to(mapa)

    folium_static(mapa)

def visualizar_clusters_e_rotas(pedidos, clusters, rotas, ponto_partida):
    """
    Visualiza os clusters e rotas no mapa usando Folium.

    :param pedidos: DataFrame com informações dos pedidos.
    :param clusters: Lista de clusters atribuídos aos pedidos.
    :param rotas: Lista de rotas planejadas.
    :param ponto_partida: Dicionário com as coordenadas do ponto de partida.
    """
    st.markdown("### 🌍 Visualização de Clusters e Rotas no Mapa")

    # Criar o mapa centrado no ponto de partida
    mapa = folium.Map(location=[ponto_partida["Latitude"], ponto_partida["Longitude"]], zoom_start=12)

    # Adicionar ponto de partida
    folium.Marker(
        location=[ponto_partida["Latitude"], ponto_partida["Longitude"]],
        popup="Ponto de Partida",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(mapa)

    # Adicionar clusters ao mapa
    cores = ["red", "blue", "purple", "orange", "darkred", "lightred", "beige", "darkblue", "darkgreen", "cadetblue"]
    for cluster_id in clusters["cluster"].unique():
        pedidos_cluster = pedidos[pedidos["cluster"] == cluster_id]
        cor = cores[cluster_id % len(cores)]
        for _, pedido in pedidos_cluster.iterrows():
            folium.CircleMarker(
                location=[pedido["Latitude"], pedido["Longitude"]],
                radius=5,
                color=cor,
                fill=True,
                fill_color=cor,
                fill_opacity=0.7,
                popup=f"Pedido ID: {pedido['ID']}\nCluster: {cluster_id}"
            ).add_to(mapa)

    # Adicionar rotas ao mapa
    for i, rota in enumerate(rotas):
        rota_coords = [[ponto_partida["Latitude"], ponto_partida["Longitude"]]] + [
            [pedidos.iloc[node - 1]["Latitude"], pedidos.iloc[node - 1]["Longitude"]] for node in rota[1:-1]
        ] + [[ponto_partida["Latitude"], ponto_partida["Longitude"]]]

        folium.PolyLine(rota_coords, color="blue", weight=2.5, opacity=0.8, tooltip=f"Rota Veículo {i + 1}").add_to(mapa)

    # Renderizar o mapa no Streamlit
    folium_static(mapa)

def calcular_custos_rotas(rotas, matriz_distancia):
    """
    Calcula o custo total das rotas com base na matriz de distância.
    """
    st.markdown("### 💰 Cálculo de Custos das Rotas")
    custo_total = 0
    for i, rota in enumerate(rotas):
        custo_rota = sum(matriz_distancia[rota[j]][rota[j + 1]] for j in range(len(rota) - 1))
        custo_total += custo_rota
        st.write(f"Custo da Rota Veículo {i + 1}: {custo_rota:.2f} unidades")
    st.write(f"**Custo Total:** {custo_total:.2f} unidades")
    return custo_total

def calcular_metricas_desempenho(rotas, pedidos):
    """
    Calcula métricas de desempenho, como número de pedidos atendidos e distância média por veículo.
    """
    st.markdown("### 📊 Métricas de Desempenho")
    total_pedidos = sum(len(rota) - 2 for rota in rotas)  # Exclui ponto de partida e chegada
    distancia_media = sum(len(rota) - 1 for rota in rotas) / len(rotas)  # Número de arestas por rota
    st.write(f"**Total de Pedidos Atendidos:** {total_pedidos}")
    st.write(f"**Distância Média por Veículo:** {distancia_media:.2f} unidades")

def calcular_tempo_estimado_entrega(rotas, dados_pedidos):
    """
    Calcula o tempo estimado de entrega para cada rota com base em dados históricos e distâncias.

    :param rotas: Lista de rotas otimizadas.
    :param dados_pedidos: DataFrame com informações dos pedidos, incluindo tempos históricos.
    :return: Dicionário com tempos estimados por rota.
    """
    tempos_estimados = {}
    for i, rota in enumerate(rotas):
        tempo_total = 0
        for j in range(len(rota) - 1):
            origem = rota[j]
            destino = rota[j + 1]
            tempo_historico = dados_pedidos.loc[(dados_pedidos['origem'] == origem) & (dados_pedidos['destino'] == destino), 'tempo_historico']
            if not tempo_historico.empty:
                tempo_total += tempo_historico.iloc[0]
            else:
                # Estimativa padrão caso não haja histórico
                tempo_total += 10  # Exemplo: 10 minutos por entrega
        tempos_estimados[f"Rota {i + 1}"] = tempo_total
    return tempos_estimados

def gerar_relatorio_roteirizacao(rotas, custos, tempos_estimados):
    """
    Gera um relatório detalhado da roteirização, incluindo custos, tempos e métricas de desempenho.

    :param rotas: Lista de rotas otimizadas.
    :param custos: Dicionário com custos por rota.
    :param tempos_estimados: Dicionário com tempos estimados por rota.
    :return: String formatada com o relatório.
    """
    relatorio = "Relatório de Roteirização\n"
    relatorio += "=" * 30 + "\n"
    for i, rota in enumerate(rotas):
        relatorio += f"Rota {i + 1}:\n"
        relatorio += f"  Paradas: {', '.join(map(str, rota))}\n"
        relatorio += f"  Custo: {custos.get(f'Rota {i + 1}', 'N/A')}\n"
        relatorio += f"  Tempo Estimado: {tempos_estimados.get(f'Rota {i + 1}', 'N/A')} minutos\n"
        relatorio += "-" * 30 + "\n"
    return relatorio

def salvar_relatorio_em_arquivo(relatorio, caminho="relatorios/relatorio_roteirizacao.txt"):
    """
    Salva o relatório de roteirização em um arquivo de texto.

    :param relatorio: String com o conteúdo do relatório.
    :param caminho: Caminho do arquivo onde o relatório será salvo.
    """
    import os
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w") as arquivo:
        arquivo.write(relatorio)

def validar_dados_entrada(pedidos, frota):
    """
    Valida os dados de entrada para garantir que estão completos e consistentes.

    :param pedidos: DataFrame com dados dos pedidos.
    :param frota: DataFrame com dados da frota.
    :return: Boolean indicando se os dados são válidos.
    """
    if pedidos.empty:
        raise ValueError("A lista de pedidos está vazia.")
    if frota.empty:
        raise ValueError("A frota está vazia.")
    if not all(col in pedidos.columns for col in ["Latitude", "Longitude", "Peso"]):
        raise ValueError("Os dados dos pedidos estão incompletos.")
    if not all(col in frota.columns for col in ["Capac. Kg", "Disponível"]):
        raise ValueError("Os dados da frota estão incompletos.")
    return True

def calcular_emissoes_carbono(rotas, dados_pedidos, fator_emissao=0.21):
    """
    Calcula as emissões de carbono para cada rota com base na distância total percorrida.

    :param rotas: Lista de rotas otimizadas.
    :param dados_pedidos: DataFrame com informações dos pedidos, incluindo distâncias.
    :param fator_emissao: Fator de emissão em kg CO2 por km.
    :return: Dicionário com emissões de carbono por rota.
    """
    emissoes = {}
    for i, rota in enumerate(rotas):
        distancia_total = 0
        for j in range(len(rota) - 1):
            origem = rota[j]
            destino = rota[j + 1]
            distancia = dados_pedidos.loc[(dados_pedidos['origem'] == origem) & (dados_pedidos['destino'] == destino), 'distancia']
            if not distancia.empty:
                distancia_total += distancia.iloc[0]
        emissoes[f"Rota {i + 1}"] = distancia_total * fator_emissao
    return emissoes

def resolver_customizado_genetico(pedidos, ponto_partida, num_veiculos, num_geracoes=100, populacao_inicial=50):
    """
    Resolve um problema customizado de roteirização usando algoritmos genéticos.
    """
    coordenadas = [(ponto_partida["Latitude"], ponto_partida["Longitude"])] + list(zip(pedidos["Latitude"], pedidos["Longitude"]))
    num_pontos = len(coordenadas)

    # Função de distância euclidiana
    def distancia_euclidiana(i, j):
        return ((coordenadas[i][0] - coordenadas[j][0])**2 + (coordenadas[i][1] - coordenadas[j][1])**0.5)

    # Matriz de distância
    matriz_distancia = [[distancia_euclidiana(i, j) for j in range(num_pontos)] for i in range(num_pontos)]

    # Função de fitness
    def fitness(rota):
        return sum(matriz_distancia[rota[i]][rota[i + 1]] for i in range(len(rota) - 1))

    # Gerar população inicial
    populacao = [random.sample(range(1, num_pontos), num_pontos - 1) for _ in range(populacao_inicial)]

    for _ in range(num_geracoes):
        # Avaliar fitness
        populacao = sorted(populacao, key=lambda rota: fitness([0] + rota + [0]))

        # Seleção
        nova_populacao = populacao[:10]  # Top 10

        # Crossover
        while len(nova_populacao) < populacao_inicial:
            pai1, pai2 = random.sample(populacao[:20], 2)
            corte = random.randint(1, len(pai1) - 1)
            filho = pai1[:corte] + [gene for gene in pai2 if gene not in pai1[:corte]]
            nova_populacao.append(filho)

        # Mutação
        for rota in nova_populacao[10:]:
            if random.random() < 0.1:  # 10% de chance de mutação
                i, j = random.sample(range(len(rota)), 2)
                rota[i], rota[j] = rota[j], rota[i]

        populacao = nova_populacao

    melhor_rota = populacao[0]
    return [0] + melhor_rota + [0], matriz_distancia

def pagina_roteirizador():
    st.title("⚙️ Configurações do Roteirizador")
    st.markdown("""
    ### Configure os parâmetros para a roteirização:
    - Escolha o critério de otimização.
    - Defina restrições e preferências.
    """)

    # Adicionar uma caixa de informações no topo
    st.info("⚡ Configure os parâmetros abaixo para otimizar suas rotas de entrega.")

    # Carregar configurações salvas
    config_salvas = carregar_configuracoes()

    # Dividir a página em duas colunas para melhor organização
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🛠️ Critério de Otimização")
        criterio = st.selectbox(
            "Escolha o critério:",
            ["Menor Distância", "Menor Tempo", "Menor Custo"],
            index=["Menor Distância", "Menor Tempo", "Menor Custo"].index(config_salvas.get("criterio", "Menor Distância"))
        )

        st.markdown("#### 🔒 Restrições")
        janela_tempo = st.checkbox("Considerar janelas de tempo", value=config_salvas.get("janela_tempo", False))
        capacidade = st.checkbox("Respeitar capacidade dos veículos", value=config_salvas.get("capacidade", False))

    with col2:
        st.markdown("#### 📍 Preferências")
        ponto_partida = st.text_input(
            "Ponto de partida (endereço ou coordenadas)",
            value=config_salvas.get("ponto_partida", ""),
            placeholder="Ex: Rua A, 123, São Paulo"
        )
        ponto_chegada = st.text_input(
            "Ponto de chegada (opcional)",
            value=ponto_partida if ponto_partida else config_salvas.get("ponto_chegada", ""),
            placeholder="Ex: Rua B, 456, São Paulo",
            disabled=True  # Desabilitar o campo para evitar edição manual
        )

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        salvar = st.button("💾 Salvar Configurações")
        preparar = st.button("🚀 Preparar Dados para Roteirização")

        if salvar:
            config = {
                "criterio": criterio,
                "janela_tempo": janela_tempo,
                "capacidade": capacidade,
                "ponto_partida": ponto_partida,
                "ponto_chegada": ponto_partida  # Ponto de chegada é igual ao ponto de partida
            }
            salvar_configuracoes(config)
            st.success("Configurações salvas com sucesso! Arquivo criado em `database/configuracoes_roteirizador.json`.")

        if preparar:
            pedidos = carregar_dados_pedidos()
            frota = carregar_dados_frota()
            config = carregar_configuracoes()

            if not pedidos.empty and not frota.empty:
                pedidos_validos, frota_disponivel = preparar_dados_para_roteirizacao(pedidos, frota, config)
                if pedidos_validos is not None and frota_disponivel is not None:
                    st.success("Dados preparados com sucesso!")
                    st.markdown("#### Pedidos Válidos")
                    st.dataframe(pedidos_validos)
                    st.markdown("#### Frota Disponível")
                    st.dataframe(frota_disponivel)

def pagina_exportacao(rotas, dados_pedidos):
    """
    Página para exportar rotas otimizadas em diferentes formatos.

    :param rotas: Lista de rotas otimizadas.
    :param dados_pedidos: DataFrame com informações dos pedidos.
    """
    st.title("📤 Exportação de Rotas")
    st.markdown("Escolha o formato para exportar as rotas otimizadas:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Exportar para JSON"):
            exportar_rotas_json(rotas, dados_pedidos, caminho="rotas_exportadas.json")
            st.success("Rotas exportadas para JSON com sucesso!")

    with col2:
        if st.button("Exportar para Excel"):
            exportar_rotas_excel(rotas, dados_pedidos, caminho="rotas_exportadas.xlsx")
            st.success("Rotas exportadas para Excel com sucesso!")

def pagina_feedback(rotas_executadas):
    """
    Página para registrar e visualizar feedbacks sobre as rotas executadas.

    :param rotas_executadas: Lista de rotas realmente executadas.
    """
    st.title("📝 Feedback das Rotas")
    st.markdown("Forneça feedback sobre as rotas executadas para melhorar futuras roteirizações.")

    feedbacks = []

    for i, rota in enumerate(rotas_executadas):
        st.markdown(f"### Rota {i + 1}")
        atraso = st.number_input(f"Atraso (minutos) - Rota {i + 1}", min_value=0, step=1, key=f"atraso_{i}")
        desvio = st.number_input(f"Desvios (número de paradas alteradas) - Rota {i + 1}", min_value=0, step=1, key=f"desvio_{i}")
        comentario = st.text_area(f"Comentários adicionais - Rota {i + 1}", key=f"comentario_{i}")

        feedbacks.append({
            "atraso": atraso,
            "desvio": desvio,
            "comentario": comentario
        })

    if st.button("Salvar Feedback"):
        registrar_feedback(rotas_executadas, feedbacks)
        st.success("Feedback salvo com sucesso!")

    st.markdown("---")
    st.markdown("### Feedbacks Registrados")
    feedback_registrado = carregar_feedback()
    if feedback_registrado:
        st.json(feedback_registrado)
    else:
        st.info("Nenhum feedback registrado até o momento.")
