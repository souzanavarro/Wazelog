from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def resolver_vrp(dados, parametros):
    """
    Resolve o problema de roteirização de veículos (VRP) usando Google OR-Tools.
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

    # Configurar parâmetros de busca
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Resolver o problema
    solution = routing.SolveWithParameters(search_parameters)

    # Processar a solução
    if solution:
        return extrair_solucao(manager, routing, solution)
    else:
        return None

def extrair_solucao(manager, routing, solution):
    """
    Extrai a solução do modelo de roteirização.
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