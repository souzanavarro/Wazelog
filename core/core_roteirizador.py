import os
import json
from datetime import datetime
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

class RoteirizadorAvancado:
    def __init__(self, matriz_distancias, demandas, capacidade_veiculos, locais_iniciais):
        self.matriz_distancias = matriz_distancias
        self.demandas = demandas
        self.capacidade_veiculos = capacidade_veiculos
        self.locais_iniciais = locais_iniciais

    def criar_dados_modelo(self):
        dados = {
            'distance_matrix': self.matriz_distancias,
            'demands': self.demandas,
            'vehicle_capacities': self.capacidade_veiculos,
            'num_vehicles': len(self.capacidade_veiculos),
            'starts': self.locais_iniciais,
            'ends': self.locais_iniciais,
        }
        return dados

    def resolver(self):
        dados = self.criar_dados_modelo()

        # Criar o gerenciador de índices
        gerenciador = pywrapcp.RoutingIndexManager(
            len(dados['distance_matrix']),
            dados['num_vehicles'],
            dados['starts'],
            dados['ends']
        )

        # Criar o modelo de roteirização
        roteirizador = pywrapcp.RoutingModel(gerenciador)

        # Função de custo (distância)
        def funcao_custo(from_index, to_index):
            from_node = gerenciador.IndexToNode(from_index)
            to_node = gerenciador.IndexToNode(to_index)
            return dados['distance_matrix'][from_node][to_node]

        transit_callback_index = roteirizador.RegisterTransitCallback(funcao_custo)
        roteirizador.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Restrições de capacidade
        def demanda_callback(from_index):
            from_node = gerenciador.IndexToNode(from_index)
            return dados['demands'][from_node]

        demanda_callback_index = roteirizador.RegisterUnaryTransitCallback(demanda_callback)
        roteirizador.AddDimensionWithVehicleCapacity(
            demanda_callback_index,
            0,  # sem capacidade extra
            dados['vehicle_capacities'],
            True,  # capacidade inicial deve ser respeitada
            'Capacity'
        )

        # Configurar parâmetros de busca
        parametros_busca = pywrapcp.DefaultRoutingSearchParameters()
        parametros_busca.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

        # Resolver o problema
        solucao = roteirizador.SolveWithParameters(parametros_busca)

        if solucao:
            return self.extrair_solucao(gerenciador, roteirizador, solucao)
        else:
            return None

    def extrair_solucao(self, gerenciador, roteirizador, solucao):
        rotas = []
        for veiculo_id in range(roteirizador.vehicles()):
            indice = roteirizador.Start(veiculo_id)
            rota = []
            while not roteirizador.IsEnd(indice):
                node_index = gerenciador.IndexToNode(indice)
                rota.append(node_index)
                indice = solucao.Value(roteirizador.NextVar(indice))
            rotas.append(rota)
        return rotas

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

def salvar_historico_roteirizacao(rotas, custos, tempos_estimados, caminho="database/historico_roteirizacao.json"):
    """
    Salva o histórico de uma roteirização em um arquivo JSON.

    :param rotas: Lista de rotas otimizadas.
    :param custos: Dicionário com custos por rota.
    :param tempos_estimados: Dicionário com tempos estimados por rota.
    :param caminho: Caminho do arquivo onde o histórico será salvo.
    """
    historico = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rotas": rotas,
        "custos": custos,
        "tempos_estimados": tempos_estimados
    }

    if os.path.exists(caminho):
        with open(caminho, "r") as arquivo:
            dados_existentes = json.load(arquivo)
    else:
        dados_existentes = []

    dados_existentes.append(historico)

    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w") as arquivo:
        json.dump(dados_existentes, arquivo, indent=4)

def carregar_historico_roteirizacao(caminho="database/historico_roteirizacao.json"):
    """
    Carrega o histórico de roteirizações de um arquivo JSON.

    :param caminho: Caminho do arquivo onde o histórico está salvo.
    :return: Lista de históricos de roteirização.
    """
    if os.path.exists(caminho):
        with open(caminho, "r") as arquivo:
            return json.load(arquivo)
    return []

def otimizar_multi_objetivo(dados, pesos):
    """
    Otimiza as rotas considerando múltiplos objetivos (custo, tempo, emissões).

    :param dados: Dicionário com informações de distâncias, tempos e emissões.
    :param pesos: Dicionário com pesos para cada objetivo (ex: {"custo": 0.5, "tempo": 0.3, "emissoes": 0.2}).
    :return: Lista de rotas otimizadas.
    """
    # Normalizar os dados para cada objetivo
    max_custo = max(dados["custos"])
    max_tempo = max(dados["tempos"])
    max_emissoes = max(dados["emissoes"])

    custos_normalizados = [c / max_custo for c in dados["custos"]]
    tempos_normalizados = [t / max_tempo for t in dados["tempos"]]
    emissoes_normalizadas = [e / max_emissoes for e in dados["emissoes"]]

    # Calcular a pontuação ponderada para cada rota
    pontuacoes = []
    for i in range(len(dados["custos"])):
        pontuacao = (
            pesos["custo"] * custos_normalizados[i] +
            pesos["tempo"] * tempos_normalizados[i] +
            pesos["emissoes"] * emissoes_normalizadas[i]
        )
        pontuacoes.append((i, pontuacao))

    # Ordenar as rotas pela pontuação (menor é melhor)
    rotas_ordenadas = sorted(pontuacoes, key=lambda x: x[1])

    # Retornar as rotas otimizadas na ordem
    return [dados["rotas"][i[0]] for i in rotas_ordenadas]

def fluxo_principal_roteirizador(dados, pesos_multi_objetivo):
    """
    Integra a otimização multi-objetivo ao fluxo principal do roteirizador.

    :param dados: Dicionário com informações de distâncias, tempos e emissões.
    :param pesos_multi_objetivo: Dicionário com pesos para cada objetivo (ex: {"custo": 0.5, "tempo": 0.3, "emissoes": 0.2}).
    :return: Lista de rotas otimizadas.
    """
    # Otimizar rotas considerando múltiplos objetivos
    rotas_otimizadas = otimizar_multi_objetivo(dados, pesos_multi_objetivo)

    # Calcular custos, tempos e emissões para as rotas otimizadas
    custos = [dados["custos"][i] for i in range(len(rotas_otimizadas))]
    tempos = [dados["tempos"][i] for i in range(len(rotas_otimizadas))]
    emissoes = [dados["emissoes"][i] for i in range(len(rotas_otimizadas))]

    # Salvar histórico da roteirização
    salvar_historico_roteirizacao(rotas_otimizadas, custos, tempos)

    return rotas_otimizadas

def obter_parametros():
    """
    Função para obter os parâmetros necessários para a roteirização.
    Retorna um dicionário com os parâmetros configurados.
    """
    parametros = {
        "distancia_maxima": 100,  # Exemplo de parâmetro
        "tempo_maximo": 8,       # Exemplo de parâmetro
        "numero_maximo_paradas": 10  # Exemplo de parâmetro
    }
    return parametros