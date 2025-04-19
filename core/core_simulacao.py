import pandas as pd

def simular_cenario(pedidos, frota, aumento_pedidos=0, indisponibilidade_veiculos=0):
    """
    Simula cenários alterando o número de pedidos e a disponibilidade de veículos.

    :param pedidos: DataFrame com os dados dos pedidos.
    :param frota: DataFrame com os dados da frota.
    :param aumento_pedidos: Percentual de aumento no número de pedidos (ex: 0.2 para 20%).
    :param indisponibilidade_veiculos: Percentual de veículos indisponíveis (ex: 0.1 para 10%).
    :return: DataFrames simulados de pedidos e frota.
    """
    # Simular aumento de pedidos
    if aumento_pedidos > 0:
        novos_pedidos = pedidos.sample(frac=aumento_pedidos, replace=True, random_state=42)
        pedidos_simulados = pd.concat([pedidos, novos_pedidos], ignore_index=True)
    else:
        pedidos_simulados = pedidos.copy()

    # Simular indisponibilidade de veículos
    if indisponibilidade_veiculos > 0:
        frota_simulada = frota.copy()
        num_indisponiveis = int(len(frota) * indisponibilidade_veiculos)
        indisponiveis = frota_simulada.sample(n=num_indisponiveis, random_state=42).index
        frota_simulada.loc[indisponiveis, "Disponível"] = "não"
    else:
        frota_simulada = frota.copy()

    return pedidos_simulados, frota_simulada