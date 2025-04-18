from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

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
