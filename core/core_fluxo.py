from core.core_pedidos import carregar_dados_pedidos
from core.core_frota import carregar_dados_frota
from core.core_mapas import calcular_distancia_osrm
from core.core_roteirizador import resolver_vrp
from core.core_regras_negocio import aplicar_regras_negocio, carregar_regras_personalizadas
from core.core_feedback import registrar_feedback, avaliar_performance

def fluxo_completo(caminho_pedidos, caminho_frota):
    """
    Executa o fluxo completo de roteirização profissional.
    """
    # 1. Importação de pedidos e frota
    pedidos = carregar_dados_pedidos(caminho_pedidos)
    frota = carregar_dados_frota(caminho_frota)

    # 2. Geocodificação dos endereços (exemplo simplificado)
    for pedido in pedidos:
        pedido["latitude_origem"], pedido["longitude_origem"] = -23.55052, -46.633308  # Exemplo fixo
        pedido["latitude_destino"], pedido["longitude_destino"] = -23.561414, -46.655881  # Exemplo fixo

    # 3. Clusterização (agrupamento por região)
    # Aqui você pode usar a função de clustering do core_ia.py (exemplo omitido)

    # 4. Otimização da rota por veículo
    distancias = []
    for pedido in pedidos:
        origem = (pedido["latitude_origem"], pedido["longitude_origem"])
        destino = (pedido["latitude_destino"], pedido["longitude_destino"])
        resultado = calcular_distancia_osrm(origem, destino)
        if resultado:
            distancias.append(resultado)

    parametros = {"veiculos": len(frota), "deposito": 0}
    rotas = resolver_vrp({"distancias": distancias, "veiculos": len(frota), "deposito": 0}, parametros)

    # 5. Aplicação de regras de negócio
    regras = carregar_regras_personalizadas()
    pedidos_filtrados = aplicar_regras_negocio(pedidos, regras)

    # 6. Simulação e visualização no mapa (exemplo omitido)

    # 7. Exportação para app do motorista / PDF / planilha
    # Aqui você pode salvar as rotas em um arquivo ou enviar para um app (exemplo omitido)

    # 8. Feedback após entrega
    entregas_realizadas = [{"Nº Pedido": pedido["Nº Pedido"], "distancia": 10, "tempo_estimado": 15, "tempo_real": 20} for pedido in pedidos_filtrados]
    feedbacks = [{"Nº Pedido": pedido["Nº Pedido"], "atraso": 5, "desvio": 0} for pedido in pedidos_filtrados]
    df_consolidado = registrar_feedback(entregas_realizadas, feedbacks)
    performance = avaliar_performance(df_consolidado)

    return {
        "rotas": rotas,
        "performance": performance
    }
