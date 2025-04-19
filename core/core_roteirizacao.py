from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import networkx as nx
import random

def otimizar_rota(dados, parametros):
    """
    Otimiza a rota de entrega para um conjunto de veículos usando Google OR-Tools.
    
    :param dados: Dicionário com distâncias, demandas e capacidades.
    :param parametros: Dicionário com parâmetros de roteirização.
    :return: Lista de rotas otimizadas por veículo.
    """
    # Criar o gerenciador de dados
    manager = pywrapcp.RoutingIndexManager(len(dados['distancias']), dados['veiculos'], dados['deposito'])
    routing = pywrapcp.RoutingModel(manager)

    # Função de custo (distância)
    def distancia_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return dados['distancias'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distancia_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Restrições de capacidade (se aplicável)
    if 'demandas' in dados:
        def demanda_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return dados['demandas'][from_node]

        demanda_callback_index = routing.RegisterUnaryTransitCallback(demanda_callback)
        routing.AddDimensionWithVehicleCapacity(
            demanda_callback_index,
            0,  # Sem capacidade extra
            dados['capacidades'],  # Capacidades dos veículos
            True,  # Início cumulativo
            'Capacity'
        )

    # Restrições de janelas de tempo (se aplicável)
    if 'janelas_tempo' in dados:
        def tempo_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dados['tempos'][from_node][to_node]

        tempo_callback_index = routing.RegisterTransitCallback(tempo_callback)
        routing.AddDimension(
            tempo_callback_index,
            30,  # Tempo de espera permitido
            1440,  # Tempo máximo (em minutos)
            False,  # Não acumular no início
            'Time'
        )
        time_dimension = routing.GetDimensionOrDie('Time')
        for location_idx, (start, end) in enumerate(dados['janelas_tempo']):
            if start is not None and end is not None:
                index = manager.NodeToIndex(location_idx)
                time_dimension.CumulVar(index).SetRange(start, end)

    # Configurar parâmetros de busca
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 30

    # Resolver o problema
    solution = routing.SolveWithParameters(search_parameters)

    # Processar a solução
    if solution:
        return extrair_rotas(manager, routing, solution)
    else:
        return None

def extrair_rotas(manager, routing, solution):
    """
    Extrai as rotas otimizadas da solução.
    """
    rotas = []
    for veiculo_id in range(routing.vehicles()):
        index = routing.Start(veiculo_id)
        rota = []
        while not routing.IsEnd(index):
            rota.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        rotas.append(rota)
    return rotas

def otimizar_rota_com_ia(dados, parametros, modelo_ia=None):
    """
    Otimiza a rota de entrega utilizando IA para considerar dados históricos e regras de negócio.

    :param dados: Dicionário com distâncias, demandas e capacidades.
    :param parametros: Dicionário com parâmetros de roteirização.
    :param modelo_ia: Modelo de IA treinado para prever tempos de entrega ou priorizar rotas.
    :return: Lista de rotas otimizadas por veículo.
    """
    if modelo_ia:
        # Ajustar dados com base em previsões do modelo de IA
        dados = modelo_ia.ajustar_dados(dados)

    # Chamar a função de otimização padrão
    return otimizar_rota(dados, parametros)

def aplicar_regras_negocio(dados, regras):
    """
    Aplica regras de negócio para ajustar as rotas antes da otimização.

    :param dados: Dicionário com dados de pedidos e veículos.
    :param regras: Lista de regras de negócio a serem aplicadas.
    :return: Dados ajustados com base nas regras de negócio.
    """
    for regra in regras:
        dados = regra.aplicar(dados)
    return dados

def integrar_dados_historicos(dados, historico):
    """
    Integra dados históricos para melhorar a precisão da roteirização.

    :param dados: Dicionário com dados de pedidos e veículos.
    :param historico: Dados históricos de entregas anteriores.
    :return: Dados ajustados com base no histórico.
    """
    for pedido in dados['pedidos']:
        if pedido['id'] in historico:
            pedido['tempo_estimado'] = historico[pedido['id']]['tempo_medio']
    return dados

def criar_grafo_tsp(pontos, matriz_distancias):
    # Função para criar um grafo para o problema do TSP
    G = nx.Graph()
    for i, ponto in enumerate(pontos):
        G.add_node(i, pos=ponto)
    for i in range(len(pontos)):
        for j in range(i + 1, len(pontos)):
            G.add_edge(i, j, weight=matriz_distancias[i][j])
    return G

def resolver_tsp_genetico(matriz_distancias, num_geracoes=100, tamanho_populacao=50):
    # Função para resolver o problema do TSP usando algoritmo genético
    def fitness(caminho):
        return sum(matriz_distancias[caminho[i]][caminho[i + 1]] for i in range(len(caminho) - 1)) + matriz_distancias[caminho[-1]][caminho[0]]

    def crossover(pai1, pai2):
        corte = random.randint(1, len(pai1) - 2)
        filho = pai1[:corte] + [gene for gene in pai2 if gene not in pai1[:corte]]
        return filho

    def mutacao(caminho):
        i, j = random.sample(range(len(caminho)), 2)
        caminho[i], caminho[j] = caminho[j], caminho[i]

    populacao = [random.sample(range(len(matriz_distancias)), len(matriz_distancias)) for _ in range(tamanho_populacao)]
    for _ in range(num_geracoes):
        populacao.sort(key=fitness)
        nova_populacao = populacao[:10]
        while len(nova_populacao) < tamanho_populacao:
            pai1, pai2 = random.sample(populacao[:20], 2)
            filho = crossover(pai1, pai2)
            if random.random() < 0.1:
                mutacao(filho)
            nova_populacao.append(filho)
        populacao = nova_populacao

    return min(populacao, key=fitness)

def tsp_nearest_neighbor(matriz_distancias):
    # Função para resolver o problema do TSP usando o algoritmo do vizinho mais próximo
    n = len(matriz_distancias)
    visitados = [False] * n
    caminho = [0]
    visitados[0] = True

    for _ in range(n - 1):
        ultimo = caminho[-1]
        proximo = min((dist, j) for j, dist in enumerate(matriz_distancias[ultimo]) if not visitados[j])[1]
        caminho.append(proximo)
        visitados[proximo] = True

    return caminho + [0]
