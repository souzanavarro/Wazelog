import pandas as pd

def analisar_performance(rotas_planejadas, rotas_executadas, tempos_estimados, tempos_reais):
    """
    Analisa a performance das rotas comparando as planejadas com as executadas.

    :param rotas_planejadas: Lista de rotas planejadas.
    :param rotas_executadas: Lista de rotas realmente executadas.
    :param tempos_estimados: Dicionário com tempos estimados por rota.
    :param tempos_reais: Dicionário com tempos reais por rota.
    :return: DataFrame com análise de atrasos, desvios e eficiência.
    """
    analise = []

    for i, rota_planejada in enumerate(rotas_planejadas):
        rota_executada = rotas_executadas[i] if i < len(rotas_executadas) else []
        tempo_estimado = tempos_estimados.get(f"Rota {i + 1}", 0)
        tempo_real = tempos_reais.get(f"Rota {i + 1}", 0)

        atraso = max(0, tempo_real - tempo_estimado)
        desvio = len(set(rota_planejada) - set(rota_executada))
        eficiencia = (tempo_estimado / tempo_real) * 100 if tempo_real > 0 else 0

        analise.append({
            "Rota": f"Rota {i + 1}",
            "Atraso (minutos)": atraso / 60,
            "Desvios": desvio,
            "Eficiência (%)": eficiencia
        })

    return pd.DataFrame(analise)

def sugestao_veiculos(historico, regiao):
    """
    Sugere veículos para uma região com base no histórico de roteirizações.
    """
    historico_regiao = historico[historico["regiao"] == regiao]

    if historico_regiao.empty:
        return "Nenhuma sugestão disponível para esta região."

    sugestao = historico_regiao["veiculo"].mode()[0]
    return sugestao

def analisar_configuracoes(rotas, configuracoes):
    """
    Analisa a eficiência das configurações de roteirização.
    """
    analise = []

    for rota in rotas:
        capacidade_utilizada = sum([pedido["peso"] for pedido in rota["pedidos"]])
        capacidade_maxima = configuracoes.get("capacidade_maxima", 0)
        eficiencia = (capacidade_utilizada / capacidade_maxima) * 100 if capacidade_maxima > 0 else 0

        analise.append({
            "Veiculo": rota["veiculo"],
            "Capacidade Utilizada (%)": eficiencia
        })

    return pd.DataFrame(analise)