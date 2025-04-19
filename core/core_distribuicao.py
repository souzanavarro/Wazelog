def verificar_disponibilidade_veiculos(frota):
    """
    Filtra os veículos disponíveis na frota.
    
    :param frota: Lista de veículos (dicionários).
    :return: Lista de veículos disponíveis.
    """
    return [veiculo for veiculo in frota if veiculo["Disponível"]]

def distribuir_carga_por_veiculo(pedidos, frota, criterio="peso_total"):
    """
    Distribui os pedidos entre os veículos disponíveis respeitando as capacidades.
    
    :param pedidos: Lista de pedidos (dicionários) com clusters atribuídos.
    :param frota: Lista de veículos disponíveis (dicionários).
    :param criterio: Critério de distribuição ('peso_total' ou 'volume_total').
    :return: Dicionário com a alocação de pedidos por veículo.
    """
    alocacao = {veiculo["Placa"]: [] for veiculo in frota}
    capacidade_restante = {veiculo["Placa"]: veiculo["Capac. Kg"] for veiculo in frota}

    for cluster_id in pedidos["cluster"].unique():
        pedidos_cluster = pedidos[pedidos["cluster"] == cluster_id].sort_values(by=criterio, ascending=False)
        
        for _, pedido in pedidos_cluster.iterrows():
            alocado = False
            for veiculo in frota:
                placa = veiculo["Placa"]
                if capacidade_restante[placa] >= pedido[criterio]:
                    alocacao[placa].append(pedido.to_dict())
                    capacidade_restante[placa] -= pedido[criterio]
                    alocado = True
                    break
            
            if not alocado:
                print(f"Pedido {pedido['Nº Pedido']} não pôde ser alocado devido à falta de capacidade.")
    
    return alocacao
