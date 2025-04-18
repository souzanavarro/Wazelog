def aplicar_regras_negocio(pedidos, regras):
    """
    Aplica regras de negócio personalizadas aos pedidos.
    
    :param pedidos: Lista de pedidos (dicionários).
    :param regras: Dicionário de regras personalizadas por cliente.
    :return: Lista de pedidos ordenados e filtrados conforme as regras.
    """
    # Ordenar por prioridade (clientes VIPs primeiro)
    pedidos.sort(key=lambda p: regras.get(p['Cód. Cliente'], {}).get('prioridade', 999))

    # Filtrar por horários preferenciais e restrições
    pedidos_filtrados = []
    for pedido in pedidos:
        cliente_regras = regras.get(pedido['Cód. Cliente'], {})
        
        # Verificar janela de entrega
        janela = cliente_regras.get('janela_entrega')
        if janela:
            if not (janela[0] <= pedido['horario_entrega'] <= janela[1]):
                continue  # Ignorar pedidos fora da janela
        
        # Verificar zonas proibidas
        zonas_proibidas = cliente_regras.get('zonas_proibidas', [])
        if pedido['zona_entrega'] in zonas_proibidas:
            continue  # Ignorar pedidos em zonas proibidas
        
        pedidos_filtrados.append(pedido)

    return pedidos_filtrados

def carregar_regras_personalizadas():
    """
    Carrega regras de negócio personalizadas (exemplo estático).
    """
    return {
        "123": {  # Código do cliente
            "prioridade": 1,  # Cliente VIP
            "janela_entrega": ("08:00", "12:00"),  # Horário preferencial
            "zonas_proibidas": ["Zona A"],  # Restrições de acesso
        },
        "456": {
            "prioridade": 2,
            "janela_entrega": ("14:00", "18:00"),
        },
        # ... outras regras ...
    }
