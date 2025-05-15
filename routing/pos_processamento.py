import pandas as pd
import numpy as np
from geopy.distance import geodesic
import logging
import json # Adicionado para exportar_rotas_para_geojson
from datetime import datetime # Adicionado para realocar_pedidos_restritos

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calcular_distancia_rota(rota, matriz_distancias):
    """
    Calcula a distância total de uma rota.
    Args:
        rota (list): Lista de índices dos nós visitados.
        matriz_distancias (np.ndarray): Matriz de distâncias.
    Returns:
        float: Distância total da rota ou np.inf se inválida.
    """
    distancia = 0
    for i in range(len(rota) - 1):
        idx_from = rota[i]
        idx_to = rota[i+1]
        if 0 <= idx_from < matriz_distancias.shape[0] and 0 <= idx_to < matriz_distancias.shape[1]:
            distancia += matriz_distancias[idx_from, idx_to]
        else:
            logging.warning(f"Índices ({idx_from}, {idx_to}) fora dos limites da matriz {matriz_distancias.shape} na rota {rota}.")
            return np.inf
    return distancia

def heuristica_2opt(rota, matriz_distancias):
    """
    Melhora a rota usando a heurística 2-opt.
    Assume que a rota começa e termina no depósito (índice 0).
    """
    if len(rota) <= 3:
        return rota
    melhor_rota = rota[:]
    melhor_distancia = calcular_distancia_rota(melhor_rota, matriz_distancias)
    if melhor_distancia == np.inf:
        logging.warning("Rota inicial inválida para 2-opt.")
        return rota
    melhorou = True
    while melhorou:
        melhorou = False
        for i in range(1, len(melhor_rota) - 2):
            for j in range(i + 1, len(melhor_rota) - 1):
                nova_rota = melhor_rota[:i] + melhor_rota[i:j+1][::-1] + melhor_rota[j+1:]
                nova_distancia = calcular_distancia_rota(nova_rota, matriz_distancias)
                if nova_distancia < melhor_distancia:
                    melhor_rota = nova_rota
                    melhor_distancia = nova_distancia
                    melhorou = True
                    break
            if melhorou:
                break
    return melhor_rota

def heuristica_3opt(rota, matriz_distancias):
    """
    Melhora a rota usando a heurística 3-opt (placeholder: usa 2-opt).
    """
    logging.info("heuristica_3opt está usando 2-opt como fallback.")
    return heuristica_2opt(rota, matriz_distancias)

def swap(rota, i, j):
    """
    Troca dois pontos (nós) da rota.
    Args:
        rota (list): Rota original.
        i (int): Índice do primeiro nó.
        j (int): Índice do segundo nó.
    Returns:
        list: Nova rota com os nós trocados.
    """
    if 0 < i < len(rota) -1 and 0 < j < len(rota) -1 and i != j:
        nova_rota = rota[:]
        nova_rota[i], nova_rota[j] = nova_rota[j], nova_rota[i]
        return nova_rota
    logging.warning(f"Índices de swap inválidos ({i}, {j}) para rota de tamanho {len(rota)}.")
    return rota

def split(rota, max_paradas_por_subrota):
    """
    Divide a rota em sub-rotas baseadas em um número máximo de paradas.
    Args:
        rota (list): Rota original.
        max_paradas_por_subrota (int): Máximo de paradas por sub-rota.
    Returns:
        list: Lista de sub-rotas.
    """
    if not isinstance(rota, list) or not rota:
        logging.warning("Rota inválida para split.")
        return []
    if rota[0] != 0 or rota[-1] != 0:
        logging.warning("Rota para split deve começar e terminar no depósito (0).")
        return [rota]
    if len(rota) <= 2:
        return [rota] if len(rota) > 0 else []
    if max_paradas_por_subrota <= 0:
        logging.warning("max_paradas_por_subrota deve ser positivo.")
        return [rota]
    sub_rotas = []
    paradas_atuais = [rota[0]]
    for parada in rota[1:-1]:
        paradas_atuais.append(parada)
        if len(paradas_atuais) -1 >= max_paradas_por_subrota:
            paradas_atuais.append(rota[0])
            sub_rotas.append(paradas_atuais)
            paradas_atuais = [rota[0]]
    if len(paradas_atuais) > 1:
        paradas_atuais.append(rota[0])
        sub_rotas.append(paradas_atuais)
    return sub_rotas

def merge(rotas, matriz_distancias, capacidade_maxima=None, demandas=None):
    """
    Tenta unir rotas adjacentes ou curtas se a combinação for viável e vantajosa.
    Args:
        rotas (list): Lista de rotas (listas de índices).
        matriz_distancias (np.ndarray): Matriz de distâncias.
        capacidade_maxima (float, opcional): Capacidade máxima da rota combinada.
        demandas (list, opcional): Lista de demandas por nó.
    Returns:
        list: Lista de rotas otimizadas.
    """
    if not isinstance(rotas, list) or len(rotas) <= 1:
        return rotas
    if demandas is not None and not isinstance(demandas, (list, np.ndarray)):
        logging.warning("'demandas' deve ser uma lista ou array numpy.")
        return rotas
    rotas_otimizadas = [r[:] for r in rotas if isinstance(r, list) and len(r) >= 2 and r[0] == 0 and r[-1] == 0]
    if len(rotas_otimizadas) <= 1:
        return rotas_otimizadas
    melhorou = True
    while melhorou:
        melhorou = False
        melhor_combinacao = None
        maior_economia = 0
        for i in range(len(rotas_otimizadas)):
            for j in range(i + 1, len(rotas_otimizadas)):
                rota_a = rotas_otimizadas[i]
                rota_b = rotas_otimizadas[j]
                nova_rota_ab = rota_a[:-1] + rota_b[1:]
                demanda_total_ab = 0
                valida_ab = True
                if demandas is not None:
                    try:
                        demanda_total_ab = sum(demandas[node] for node in nova_rota_ab if node != 0)
                    except (IndexError, TypeError):
                        valida_ab = False
                if valida_ab and (capacidade_maxima is None or demanda_total_ab <= capacidade_maxima):
                    dist_orig_a = calcular_distancia_rota(rota_a, matriz_distancias)
                    dist_orig_b = calcular_distancia_rota(rota_b, matriz_distancias)
                    if dist_orig_a != np.inf and dist_orig_b != np.inf:
                        nova_dist_ab = calcular_distancia_rota(nova_rota_ab, matriz_distancias)
                        if nova_dist_ab != np.inf:
                            economia_ab = (dist_orig_a + dist_orig_b) - nova_dist_ab
                            if economia_ab > maior_economia:
                                maior_economia = economia_ab
                                melhor_combinacao = (i, j, nova_rota_ab, economia_ab)
                nova_rota_ba = rota_b[:-1] + rota_a[1:]
                demanda_total_ba = 0
                valida_ba = True
                if demandas is not None:
                    try:
                        demanda_total_ba = sum(demandas[node] for node in nova_rota_ba if node != 0)
                    except (IndexError, TypeError):
                        valida_ba = False
                if valida_ba and (capacidade_maxima is None or demanda_total_ba <= capacidade_maxima):
                    dist_orig_a = calcular_distancia_rota(rota_a, matriz_distancias)
                    dist_orig_b = calcular_distancia_rota(rota_b, matriz_distancias)
                    if dist_orig_a != np.inf and dist_orig_b != np.inf:
                        nova_dist_ba = calcular_distancia_rota(nova_rota_ba, matriz_distancias)
                        if nova_dist_ba != np.inf:
                            economia_ba = (dist_orig_a + dist_orig_b) - nova_dist_ba
                            if economia_ba > maior_economia:
                                maior_economia = economia_ba
                                melhor_combinacao = (i, j, nova_rota_ba, economia_ba)
        if melhor_combinacao is not None:
            idx_a, idx_b, rota_combinada, economia = melhor_combinacao
            indices_para_remover = sorted([idx_a, idx_b], reverse=True)
            try:
                rotas_otimizadas.pop(indices_para_remover[0])
                rotas_otimizadas.pop(indices_para_remover[1])
                rotas_otimizadas.append(rota_combinada)
                melhorou = True
            except IndexError:
                logging.error("Erro ao remover rotas durante o merge. Parando.")
                melhorou = False
        else:
            melhorou = False
    return rotas_otimizadas
    pass
def exportar_rotas_para_csv(rotas, filepath):
    """
    Exporta uma lista de rotas para um arquivo CSV.
    Args:
        rotas (list): Lista de rotas (listas de índices).
        filepath (str): Caminho do arquivo CSV.
    """
    df = pd.DataFrame({'rota': rotas})
    df.to_csv(filepath, index=False, encoding='utf-8')
    logging.info(f"Rotas exportadas para {filepath}")
    pass
def exportar_rotas_para_geojson(rotas, coordenadas, filepath):
    """
    Exporta rotas para GeoJSON.
    Args:
        rotas (list): Lista de rotas (listas de índices).
        coordenadas (list): Lista de tuplas (lat, lon) indexadas pelo nó.
        filepath (str): Caminho do arquivo GeoJSON.
    """
    features = []
    for rota in rotas:
        coords = [coordenadas[idx] for idx in rota]
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat] for lat, lon in coords]
            },
            "properties": {}
        })
    geojson = {"type": "FeatureCollection", "features": features}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    logging.info(f"Rotas exportadas para {filepath} (GeoJSON)")
    pass
def balancear_carga_e_usar_todos_veiculos(
    rotas_df, frota, pedidos, max_iter=20, criterio_balanceamento='peso', priorizar_regiao=False
):
    """
    Balanceia a carga entre veículos.
    Permite balancear por 'peso' (Demanda) ou 'paradas' (número de pedidos).
    Se priorizar_regiao=True, tenta manter pedidos da mesma região juntos.
    """
    if rotas_df is None or rotas_df.empty or 'Veículo' not in rotas_df.columns:
        return rotas_df
    # --- Balanceamento ---
    for _ in range(max_iter):
        if criterio_balanceamento == 'paradas':
            cargas = rotas_df.groupby('Veículo').size()
        else:  # padrão: peso
            cargas = rotas_df.groupby('Veículo')['Demanda'].sum()
        v_max = cargas.idxmax()
        v_min = cargas.idxmin()
        if cargas[v_max] - cargas[v_min] < 1:
            break
        # Se priorizar região, tenta mover pedido da região predominante do v_max
        if priorizar_regiao and 'Região' in rotas_df.columns:
            regiao_predominante = rotas_df[rotas_df['Veículo'] == v_max]['Região'].mode().iloc[0]
            pedidos_vmax = rotas_df[(rotas_df['Veículo'] == v_max) & (rotas_df['Região'] == regiao_predominante)]
            if pedidos_vmax.empty:
                pedidos_vmax = rotas_df[rotas_df['Veículo'] == v_max]
        else:
            pedidos_vmax = rotas_df[rotas_df['Veículo'] == v_max]
        pedido_para_mover = pedidos_vmax.iloc[0]
        rotas_df.loc[rotas_df.index == pedido_para_mover.name, 'Veículo'] = v_min
    return rotas_df
    pass
def mover_para_vizinho_proximo(rotas_df, matriz_distancias, depot_index=0, max_iter=10):
    """
    Heurística de vizinhança: move pedidos para veículos que já atendem clientes próximos (minimizando distância incremental).
    """
    if rotas_df is None or rotas_df.empty or 'Veículo' not in rotas_df.columns or 'Node_Index_OR' not in rotas_df.columns:
        return rotas_df
    for _ in range(max_iter):
        melhorou = False
        for idx, pedido in rotas_df.iterrows():
            veic_atual = pedido['Veículo']
            node_idx = pedido['Node_Index_OR']
            min_delta = None
            melhor_veic = veic_atual
            for veic in rotas_df['Veículo'].unique():
                if veic == veic_atual:
                    continue
                # Calcula distância incremental para inserir o pedido na rota do outro veículo
                rota_veic = rotas_df[rotas_df['Veículo'] == veic]['Node_Index_OR'].tolist()
                if not rota_veic:
                    continue
                # Tenta inserir entre todos os pares consecutivos
                for i in range(len(rota_veic)):
                    antes = rota_veic[i-1] if i > 0 else depot_index
                    depois = rota_veic[i]
                    delta = matriz_distancias[antes][node_idx] + matriz_distancias[node_idx][depois] - matriz_distancias[antes][depois]
                    if min_delta is None or delta < min_delta:
                        min_delta = delta
                        melhor_veic = veic
            if melhor_veic != veic_atual and min_delta is not None and min_delta < 0:
                rotas_df.at[idx, 'Veículo'] = melhor_veic
                melhorou = True
        if not melhorou:
            break
    return rotas_df

def reservar_veiculos_para_regioes(rotas_df, frota, pedidos, n_reservas=1):
    """
    Reserva veículos para regiões críticas (com mais pedidos).
    """
    if 'Região' not in pedidos.columns or rotas_df is None or rotas_df.empty:
        return rotas_df
    if 'Região' not in rotas_df.columns:
        raise KeyError("A coluna 'Região' não está presente no DataFrame rotas_df. Verifique os dados de entrada.")
    regioes_criticas = pedidos['Região'].value_counts().head(n_reservas).index.tolist()
    veiculos_ativos = frota['ID Veículo'] if 'ID Veículo' in frota.columns else frota['Placa']
    veiculos_ativos = veiculos_ativos.dropna().unique().tolist()
    for i, reg in enumerate(regioes_criticas):
        if i < len(veiculos_ativos):
            veic = veiculos_ativos[i]
            idxs = rotas_df[rotas_df['Região'] == reg].index
            rotas_df.loc[idxs, 'Veículo'] = veic
    return rotas_df

def balanceamento_iterativo(rotas_df, frota, pedidos, matriz_distancias, max_iter=10):
    """
    Executa balanceamento iterativo por peso, paradas, região e vizinhança até convergência.
    """
    for _ in range(max_iter):
        antes = rotas_df['Veículo'].copy()
        rotas_df = balancear_carga_e_usar_todos_veiculos(rotas_df, frota, pedidos, criterio_balanceamento='peso')
        rotas_df = balancear_carga_e_usar_todos_veiculos(rotas_df, frota, pedidos, criterio_balanceamento='paradas')
        rotas_df = balancear_carga_e_usar_todos_veiculos(rotas_df, frota, pedidos, priorizar_regiao=True)
        rotas_df = mover_para_vizinho_proximo(rotas_df, matriz_distancias)
        if rotas_df['Veículo'].equals(antes):
            break
    return rotas_df

def checar_e_corrigir_excesso_carga(rotas_df, frota, limite_pct=120):
    """
    Garante que nenhum veículo ultrapasse o limite de capacidade (ex: 120%).
    Remove pedidos excedentes e tenta realocar para veículos com espaço.
    Retorna rotas_df corrigido e lista de veículos com excesso não resolvido.
    """
    if rotas_df is None or rotas_df.empty or 'Veículo' not in rotas_df.columns or 'Demanda' not in rotas_df.columns:
        return rotas_df, []
    # Mapeia capacidade dos veículos
    id_col = 'ID Veículo' if 'ID Veículo' in frota.columns else 'Placa'
    capacidades = frota.set_index(id_col)['Capacidade (Kg)'].to_dict()
    limite_cap = {k: v * limite_pct / 100.0 for k, v in capacidades.items()}
    excesso = []
    for veic, grupo in rotas_df.groupby('Veículo'):
        cap = limite_cap.get(veic, None)
        if cap is None:
            continue
        demanda_total = grupo['Demanda'].sum()
        if demanda_total > cap:
            excesso.append((veic, demanda_total, cap))
            # Remove pedidos até ficar dentro do limite
            grupo_sorted = grupo.sort_values('Demanda', ascending=False)
            demanda_acum = 0
            indices_para_remover = []
            for idx, row in grupo_sorted.iterrows():
                if demanda_acum + row['Demanda'] > cap:
                    indices_para_remover.append(idx)
                else:
                    demanda_acum += row['Demanda']
            # Remove do DataFrame
            rotas_df.loc[indices_para_remover, 'Veículo'] = None # Marca para realocação
    # Tenta realocar pedidos sem veículo
    pedidos_sem_veic = rotas_df[rotas_df['Veículo'].isnull()]
    for idx, row in pedidos_sem_veic.iterrows():
        for veic, cap in limite_cap.items():
            demanda_atual = rotas_df[rotas_df['Veículo'] == veic]['Demanda'].sum()
            if demanda_atual + row['Demanda'] <= cap:
                rotas_df.at[idx, 'Veículo'] = veic
                break
    # Recalcula excesso
    excesso_final = []
    for veic, grupo in rotas_df.groupby('Veículo'):
        cap = limite_cap.get(veic, None)
        if cap is None:
            continue
        demanda_total = grupo['Demanda'].sum()
        if demanda_total > cap:
            excesso_final.append((veic, demanda_total, cap))
    return rotas_df, excesso_final

## Função garantir_ocupacao_minima removida: regra de ocupação mínima por veículo não é mais utilizada.
# Função para garantir veículos suficientes por região, respeitando capacidade
def alocar_veiculos_por_capacidade_regiao(rotas_df, frota, pedidos, modo='capacidade', marcar_restrito=True):
    """
    Função unificada de alocação de veículos por região.
    Se modo='capacidade', divide pedidos entre vários veículos respeitando capacidade.
    Se modo='1_veiculo_por_regiao', cada região recebe no máximo 1 veículo (e cada veículo só atende uma região).
    Se faltar veículo, pode marcar pedidos como restritos.
    """
    if rotas_df is None or rotas_df.empty or 'Região' not in pedidos.columns:
        logging.warning("Dados insuficientes para alocação por região/capacidade.")
        return rotas_df
    id_col = 'ID Veículo' if 'ID Veículo' in frota.columns else 'Placa'
    veiculos_ativos = frota[id_col].dropna().unique().tolist()
    capacidade_veic = frota.set_index(id_col)['Capacidade (Kg)'].to_dict() if 'Capacidade (Kg)' in frota.columns else {}
    regioes = pedidos['Região'].dropna().unique().tolist()
    veiculos_usados = set()
    if modo == 'capacidade':
        for reg in regioes:
            veics_pref = frota[frota['Regiões Preferidas'].fillna('').str.lower().str.contains(reg.lower())][id_col].tolist()
            veic = None
            for v in veics_pref:
                if v not in veiculos_usados:
                    veic = v
                    break
            if veic is None:
                for v in veiculos_ativos:
                    if v not in veiculos_usados:
                        veic = v
                        break
            if veic is not None:
                idxs = rotas_df[rotas_df['Região'] == reg].index
                rotas_df.loc[idxs, 'Veículo'] = veic
                veiculos_usados.add(veic)
            else:
                if marcar_restrito:
                    idxs = rotas_df[rotas_df['Região'] == reg].index
                    rotas_df.loc[idxs, 'Alocacao_Restrita'] = True
                logging.warning(f"Não há veículo disponível para a região '{reg}'. Pedidos marcados como restritos.")
        return rotas_df
    elif modo == '1_veiculo_por_regiao':
        veiculos_usados = set()
        for reg in regioes:
            veics_pref = frota[frota['Regiões Preferidas'].fillna('').str.lower().str.contains(reg.lower())][id_col].tolist()
            veic = None
            for v in veics_pref:
                if v not in veiculos_usados:
                    veic = v
                    break
            if veic is None:
                for v in veiculos_ativos:
                    if v not in veiculos_usados:
                        veic = v
                        break
            if veic is not None:
                idxs = rotas_df[rotas_df['Região'] == reg].index
                rotas_df.loc[idxs, 'Veículo'] = veic
                veiculos_usados.add(veic)
            else:
                if marcar_restrito:
                    idxs = rotas_df[rotas_df['Região'] == reg].index
                    rotas_df.loc[idxs, 'Alocacao_Restrita'] = True
                logging.warning(f"Não há veículo disponível para a região '{reg}'. Pedidos marcados como restritos.")
        return rotas_df
    else:
        raise ValueError(f"Modo '{modo}' não reconhecido em alocar_veiculos_por_capacidade_regiao.")
def alocar_1_veiculo_por_regiao(rotas_df, frota, pedidos):
    """
    Compatibilidade: chama a função unificada com modo '1_veiculo_por_regiao'.
    """
    return alocar_veiculos_por_capacidade_regiao(rotas_df, frota, pedidos, modo='1_veiculo_por_regiao', marcar_restrito=True)
def realocar_pedidos_restritos(rotas_df, frota, pedidos, raio_km=5):
    # Raio padrão fixo de 5km para realocação
    raio_km = 5
    # Garante que a frota tenha as colunas de janela de tempo e preenche valores padrão se necessário
    if 'Janela Início' not in frota.columns:
        frota['Janela Início'] = '05:00'
    else:
        frota['Janela Início'] = frota['Janela Início'].fillna('05:00').replace('', '05:00')
    if 'Janela Fim' not in frota.columns:
        frota['Janela Fim'] = '18:00'
    else:
        frota['Janelati9 Fim'] = frota['Janela Fim'].fillna('18:00').replace('', '18:00')

    # Garante que rotas_df tenha as colunas de janela de tempo do pedido
    if 'Janela Início' not in rotas_df.columns:
        rotas_df['Janela Início'] = '05:00'
    else:
        rotas_df['Janela Início'] = rotas_df['Janela Início'].fillna('05:00').replace('', '05:00')
    if 'Janela Fim' not in rotas_df.columns:
        rotas_df['Janela Fim'] = '18:00'
    else:
        rotas_df['Janela Fim'] = rotas_df['Janela Fim'].fillna('18:00').replace('', '18:00')

    # Define id_col antes de qualquer uso
    id_col = 'ID Veículo' if 'ID Veículo' in frota.columns else 'Placa'

    # Cria dicionário de janelas da frota
    janela_inicio_frota = frota.set_index(id_col)['Janela Início'].to_dict()
    janela_fim_frota = frota.set_index(id_col)['Janela Fim'].to_dict()

    # Marca como restrito todo pedido cuja janela não está contida na janela do veículo
    for idx, row in rotas_df.iterrows():
        veic = row['Veículo']
        if pd.isnull(veic):
            continue
        janela_ini_ped = row['Janela Início'] if 'Janela Início' in row else '05:00'
        janela_fim_ped = row['Janela Fim'] if 'Janela Fim' in row else '18:00'
        janela_ini_veic = janela_inicio_frota.get(veic, '05:00')
        janela_fim_veic = janela_fim_frota.get(veic, '18:00')
        # Compara horários (formato HH:MM)
        try:
            fmt = '%H:%M'
            ini_ped = datetime.strptime(str(janela_ini_ped), fmt)
            fim_ped = datetime.strptime(str(janela_fim_ped), fmt)
            ini_veic = datetime.strptime(str(janela_ini_veic), fmt)
            fim_veic = datetime.strptime(str(janela_fim_veic), fmt)
            # Se pedido começa antes do veículo ou termina depois do veículo, marca como restrito
            if ini_ped < ini_veic or fim_ped > fim_veic:
                rotas_df.at[idx, 'Alocacao_Restrita'] = True
                logging.warning(f"Pedido {idx} com janela [{janela_ini_ped}-{janela_fim_ped}] não cabe na janela do veículo {veic} [{janela_ini_veic}-{janela_fim_veic}]. Marcado como restrito.")
        except Exception as e:
            logging.warning(f"Erro ao comparar janelas de tempo para pedido {idx}: {e}")
    """
    Tenta realocar pedidos marcados como Alocacao_Restrita para outros veículos que atendam até 2 regiões próximas (por nome e raio) e tenham capacidade disponível.
    Remove a marcação se conseguir realocar. Retorna o DataFrame atualizado e o número de realocações.
    """
    # Validação e padronização das colunas essenciais
    col_essenciais = ['Região', 'Latitude', 'Longitude', 'Veículo', 'Demanda']
    for col in col_essenciais:
        if col not in rotas_df.columns:
            logging.error(f"Coluna obrigatória '{col}' ausente em rotas_df. Abortando realocação.")
            return rotas_df, 0
    if pedidos is None or 'Região' not in pedidos.columns or 'Latitude' not in pedidos.columns or 'Longitude' not in pedidos.columns:
        logging.error("Pedidos DataFrame ausente ou sem colunas essenciais. Abortando realocação.")
        return rotas_df, 0
    # Padroniza nomes de regiões (strip, title)
    rotas_df['Região'] = rotas_df['Região'].astype(str).str.strip().str.title()
    pedidos['Região'] = pedidos['Região'].astype(str).str.strip().str.title()
    # Converte coordenadas para float e remove linhas inválidas
    rotas_df['Latitude'] = pd.to_numeric(rotas_df['Latitude'], errors='coerce')
    rotas_df['Longitude'] = pd.to_numeric(rotas_df['Longitude'], errors='coerce')
    pedidos['Latitude'] = pd.to_numeric(pedidos['Latitude'], errors='coerce')
    pedidos['Longitude'] = pd.to_numeric(pedidos['Longitude'], errors='coerce')
    # Remove pedidos restritos sem coordenadas válidas
    pedidos_restritos = rotas_df[(rotas_df['Alocacao_Restrita'] == True) & rotas_df['Latitude'].notnull() & rotas_df['Longitude'].notnull()]
    if pedidos_restritos.empty:
        logging.info("Nenhum pedido restrito com coordenadas válidas para realocação.")
        return rotas_df, 0
    id_col = 'ID Veículo' if 'ID Veículo' in frota.columns else 'Placa'
    capacidades = frota.set_index(id_col)['Capacidade (Kg)'].to_dict() if 'Capacidade (Kg)' in frota.columns else {}
    realocados = 0
    for idx, row in pedidos_restritos.iterrows():
        lat = row['Latitude']
        lon = row['Longitude']
        reg_pedido = row['Região']
        demanda = row['Demanda'] if 'Demanda' in row else 0
        veic_atual = row['Veículo']
        if pd.isnull(lat) or pd.isnull(lon) or not reg_pedido or pd.isnull(veic_atual):
            logging.warning(f"Pedido restrito ignorado por dados faltantes: idx={idx}, regiao={reg_pedido}, lat={lat}, lon={lon}, veic_atual={veic_atual}")
            continue
        melhor_veic = None
        menor_carga = None
        for veic in rotas_df['Veículo'].unique():
            if veic == veic_atual:
                continue
            pedidos_veic = rotas_df[rotas_df['Veículo'] == veic]
            if pedidos_veic.empty:
                continue
            regioes_pred = pedidos_veic['Região'].value_counts().index[:1].tolist()
            centroides = []
            for reg in regioes_pred:
                pedidos_regiao = pedidos[pedidos['Região'] == reg]
                if not pedidos_regiao.empty and 'Latitude' in pedidos_regiao.columns and 'Longitude' in pedidos_regiao.columns:
                    lat_centroide = pedidos_regiao['Latitude'].mean()
                    lon_centroide = pedidos_regiao['Longitude'].mean()
                    centroides.append((reg, (lat_centroide, lon_centroide)))
            permitido = False
            for reg, (lat_c, lon_c) in centroides:
                if reg_pedido == reg:
                    dist = geodesic((lat, lon), (lat_c, lon_c)).km
                    if dist <= raio_km:
                        permitido = True
                        break
            if not permitido:
                continue
            cap = capacidades.get(veic, None)
            carga_atual = rotas_df[rotas_df['Veículo'] == veic]['Demanda'].sum() if 'Demanda' in rotas_df.columns else 0
            if cap is not None and carga_atual + demanda <= cap:
                if menor_carga is None or carga_atual < menor_carga:
                    melhor_veic = veic
                    menor_carga = carga_atual
        if melhor_veic:
            rotas_df.at[idx, 'Veículo'] = melhor_veic
            rotas_df.at[idx, 'Alocacao_Restrita'] = False
            realocados += 1
    return rotas_df, realocados

def alocar_regiao_predominante_com_agrupamento_vizinho(rotas_df, frota, pedidos, raio_km=5, capacidade_min_pct=0.5, min_pedidos=5, capacidade_col='Capacidade (Kg)', demanda_col='Demanda'):
    """
    Aloca pedidos priorizando a região predominante do veículo, permitindo agrupamento
    com uma região vizinha mais próxima se o veículo estiver subutilizado.

    Regras:
    1. Veículo foca na sua região predominante.
    2. Se ocupação < capacidade_min_pct ou num_pedidos < min_pedidos, pode buscar
       pedidos na região vizinha mais próxima (centroide_vizinha a centroide_predominante <= raio_km).
    3. Pedidos da região predominante devem estar a <= raio_km do centroide da predominante.
    4. Pedidos de uma região vizinha (se agrupada) devem estar a <= raio_km do
       centroide da sua própria região.
    5. Pedidos fora dessas condições são marcados como 'Alocacao_Restrita'.
    """
    # Raio padrão fixo de 5km para agrupamento
    raio_km = 5
    if rotas_df is None or rotas_df.empty:
        logging.warning("alocar_regiao_predominante_com_agrupamento_vizinho: rotas_df vazio.")
        return rotas_df
    if frota is None or frota.empty:
        logging.warning("alocar_regiao_predominante_com_agrupamento_vizinho: frota vazia.")
        return rotas_df
    if pedidos is None or pedidos.empty:
        logging.warning("alocar_regiao_predominante_com_agrupamento_vizinho: pedidos vazio.")
        return rotas_df

    id_col_frota = 'ID Veículo' if 'ID Veículo' in frota.columns else 'Placa'
    cols_rotas_obrigatorias = ['Veículo', 'Região', 'Latitude', 'Longitude', demanda_col]
    cols_pedidos = ['Região', 'Latitude', 'Longitude']
    cols_frota = [id_col_frota, capacidade_col]

    for col in cols_rotas_obrigatorias:
        if col not in rotas_df.columns:
            logging.error(f"Coluna obrigatória '{col}' ausente em rotas_df.")
            return rotas_df
    for col in cols_pedidos:
        if col not in pedidos.columns:
            logging.error(f"Coluna '{col}' ausente em pedidos.")
            return rotas_df
    for col in cols_frota:
        if col not in frota.columns:
            logging.error(f"Coluna '{col}' ausente em frota.")
            return rotas_df
            
    rotas_df_proc = rotas_df.copy()
    rotas_df_proc['Alocacao_Restrita'] = False # Inicializa/Reseta

    pedidos_proc = pedidos.copy()
    for df in [pedidos_proc, rotas_df_proc]:
        df['Região'] = df['Região'].astype(str).str.strip().str.title()
        df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    rotas_df_proc[demanda_col] = pd.to_numeric(rotas_df_proc[demanda_col], errors='coerce').fillna(0)
    frota[capacidade_col] = pd.to_numeric(frota[capacidade_col], errors='coerce')
    capacidades_veic = frota.set_index(id_col_frota)[capacidade_col].to_dict()

    centroides_todas_regioes = {}
    for reg_nome, grupo_pedidos_regiao in pedidos_proc.groupby('Região'):
        pedidos_validos_reg = grupo_pedidos_regiao.dropna(subset=['Latitude', 'Longitude'])
        if not pedidos_validos_reg.empty:
            centroides_todas_regioes[reg_nome] = (pedidos_validos_reg['Latitude'].mean(), pedidos_validos_reg['Longitude'].mean())
        else:
            logging.info(f"Região '{reg_nome}' não tem coordenadas válidas para centroide.")
            
    if not centroides_todas_regioes:
        logging.warning("Nenhum centroide regional pôde ser calculado. Abortando agrupamento e validação geográfica.")
        return rotas_df_proc 

    veiculos_no_rotas_df = rotas_df_proc['Veículo'].dropna().unique()
    for veic_id in veiculos_no_rotas_df:
        pedidos_do_veiculo_atual_loop = rotas_df_proc[rotas_df_proc['Veículo'] == veic_id]
        if pedidos_do_veiculo_atual_loop.empty:
            continue

        capacidade_do_veiculo = capacidades_veic.get(veic_id)
        if capacidade_do_veiculo is None or pd.isnull(capacidade_do_veiculo):
            logging.warning(f"Veículo {veic_id} sem capacidade válida na frota. Pulando agrupamento.")
            continue

        carga_atual_kg = pedidos_do_veiculo_atual_loop[demanda_col].sum()
        num_pedidos_atual = len(pedidos_do_veiculo_atual_loop)
        
        regioes_veiculo_atual = pedidos_do_veiculo_atual_loop['Região'].dropna()
        if regioes_veiculo_atual.empty:
            logging.info(f"Veículo {veic_id} sem pedidos com região definida. Pulando agrupamento.")
            continue
        
        regiao_pred_veic_nome = regioes_veiculo_atual.mode()
        regiao_pred_veic_nome = regiao_pred_veic_nome[0] if not regiao_pred_veic_nome.empty else regioes_veiculo_atual.value_counts().index[0]

        centroide_reg_pred_veic = centroides_todas_regioes.get(regiao_pred_veic_nome)
        if not centroide_reg_pred_veic:
            logging.warning(f"Veículo {veic_id}: Região predominante '{regiao_pred_veic_nome}' sem centroide. Pulando agrupamento.")
            continue
            
        precisa_agrupar = False
        if capacidade_do_veiculo > 0 and (carga_atual_kg / capacidade_do_veiculo) < capacidade_min_pct:
            precisa_agrupar = True
        if num_pedidos_atual < min_pedidos:
            precisa_agrupar = True
        
        if precisa_agrupar:
            logging.info(f"Veículo {veic_id} (Região Pred: {regiao_pred_veic_nome}, Carga: {carga_atual_kg}/{capacidade_do_veiculo} kg, Pedidos: {num_pedidos_atual}) subutilizado. Buscando em regiões vizinhas.")
            # NOVO: Permitir múltiplas regiões vizinhas dentro do raio
            regioes_vizinhas = []
            for reg_vizinha_cand_nome, centroide_reg_vizinha_cand in centroides_todas_regioes.items():
                if reg_vizinha_cand_nome == regiao_pred_veic_nome:
                    continue
                dist_pred_a_vizinha = geodesic(centroide_reg_pred_veic, centroide_reg_vizinha_cand).km
                if dist_pred_a_vizinha <= raio_km:
                    regioes_vizinhas.append(reg_vizinha_cand_nome)

            if regioes_vizinhas:
                logging.info(f"Veículo {veic_id}: Regiões vizinhas dentro do raio: {regioes_vizinhas}.")
                pedidos_candidatos_vizinhos = rotas_df_proc[
                    rotas_df_proc['Região'].isin(regioes_vizinhas) &
                    ((rotas_df_proc['Veículo'] != veic_id) | rotas_df_proc['Veículo'].isnull())
                ].copy()

                for idx_pedido_vizinho, pedido_vizinho_row in pedidos_candidatos_vizinhos.iterrows():
                    coord_pedido_vizinho = (pedido_vizinho_row['Latitude'], pedido_vizinho_row['Longitude'])
                    demanda_pedido_vizinho = pedido_vizinho_row[demanda_col]

                    if pd.isnull(coord_pedido_vizinho[0]) or pd.isnull(coord_pedido_vizinho[1]) or pd.isnull(demanda_pedido_vizinho):
                        continue
                    # Checa se o pedido está próximo do centroide da sua própria região
                    centroide_reg_vizinha = centroides_todas_regioes.get(pedido_vizinho_row['Região'])
                    if centroide_reg_vizinha is None:
                        continue
                    dist_ped_vizinho_a_centroide_vizinha = geodesic(coord_pedido_vizinho, centroide_reg_vizinha).km
                    if dist_ped_vizinho_a_centroide_vizinha <= raio_km:
                        if carga_atual_kg + demanda_pedido_vizinho <= capacidade_do_veiculo:
                            veiculo_anterior = rotas_df_proc.at[idx_pedido_vizinho, 'Veículo']
                            rotas_df_proc.at[idx_pedido_vizinho, 'Veículo'] = veic_id
                            rotas_df_proc.at[idx_pedido_vizinho, 'Alocacao_Restrita'] = False
                            carga_atual_kg += demanda_pedido_vizinho
                            num_pedidos_atual += 1
                            pedido_id_log_vizinho = pedido_vizinho_row.get('Pedido_Index_DF', idx_pedido_vizinho)
                            logging.info(f"Pedido {pedido_id_log_vizinho} (Reg: {pedido_vizinho_row['Região']}) movido do veículo '{veiculo_anterior if pd.notnull(veiculo_anterior) else 'NÃO ALOCADO'}' para veículo {veic_id} (Região Pred: {regiao_pred_veic_nome}).")
    
    for veic_id_final in rotas_df_proc['Veículo'].dropna().unique():
        pedidos_veic_final = rotas_df_proc[rotas_df_proc['Veículo'] == veic_id_final]
        if pedidos_veic_final.empty:
            continue
        
        regioes_veic_final = pedidos_veic_final['Região'].dropna()
        if regioes_veic_final.empty:
            logging.info(f"Veículo {veic_id_final} (final): sem pedidos com região. Marcando todos como restritos se houver algum.")
            for idx_ped_veic_final in pedidos_veic_final.index: # Marcar mesmo se não tiver região?
                 rotas_df_proc.at[idx_ped_veic_final, 'Alocacao_Restrita'] = True
            continue
        
        regiao_pred_veic_final_nome_series = regioes_veic_final.mode()
        regiao_pred_veic_final_nome = regiao_pred_veic_final_nome_series[0] if not regiao_pred_veic_final_nome_series.empty else regioes_veic_final.value_counts().index[0]
        centroide_reg_pred_veic_final = centroides_todas_regioes.get(regiao_pred_veic_final_nome)

        if not centroide_reg_pred_veic_final:
            logging.warning(f"Veículo {veic_id_final} (final): Região predominante '{regiao_pred_veic_final_nome}' sem centroide. Marcado restrito.")
            for idx_ped_veic_final in pedidos_veic_final.index:
                rotas_df_proc.at[idx_ped_veic_final, 'Alocacao_Restrita'] = True
            continue

        for idx_ped, ped_row in pedidos_veic_final.iterrows():
            lat_ped, lon_ped, reg_ped_nome = ped_row['Latitude'], ped_row['Longitude'], ped_row['Região']
            pedido_id_log = ped_row.get('Pedido_Index_DF', idx_ped)

            if pd.isnull(lat_ped) or pd.isnull(lon_ped) or pd.isnull(reg_ped_nome) or reg_ped_nome == 'Nan':
                rotas_df_proc.at[idx_ped, 'Alocacao_Restrita'] = True
                logging.warning(f"Pedido {pedido_id_log} (V: {veic_id_final}) marcado restrito: dados geo/região faltantes.")
                continue

            permitido = False
            centroide_reg_ped = centroides_todas_regioes.get(reg_ped_nome)
            if not centroide_reg_ped:
                rotas_df_proc.at[idx_ped, 'Alocacao_Restrita'] = True
                logging.warning(f"Pedido {pedido_id_log} (Reg: {reg_ped_nome}, V: {veic_id_final}): Região do pedido sem centroide. Marcado restrito.")
                continue

            if reg_ped_nome == regiao_pred_veic_final_nome:
                if geodesic((lat_ped, lon_ped), centroide_reg_pred_veic_final).km <= raio_km:
                    permitido = True
            else:
                if geodesic(centroide_reg_ped, centroide_reg_pred_veic_final).km <= raio_km:
                    if geodesic((lat_ped, lon_ped), centroide_reg_ped).km <= raio_km:
                        permitido = True
            
            rotas_df_proc.at[idx_ped, 'Alocacao_Restrita'] = not permitido
            if not permitido:
                logging.warning(f"Pedido {pedido_id_log} (Reg: {reg_ped_nome}, V: {veic_id_final}, Pred: {regiao_pred_veic_final_nome}) não atende critérios de proximidade. Marcado restrito.")
                
    return rotas_df_proc

# Funcao antiga, substituida por alocar_regiao_predominante_com_agrupamento_vizinho
# def restringir_1_regiao_por_veiculo(rotas_df, raio_km=20, pedidos=None):
#     """
#     Para cada veículo, identifica a região predominante.
#     Permite pedidos da região predominante que estejam dentro de um raio_km do seu centroide.
#     Permite pedidos de OUTRAS regiões se o centroide dessas outras regiões estiver próximo ao
#     centroide da região predominante, e o pedido em si estiver próximo ao centroide da sua própria região.
#     Pedidos fora dessas condições são marcados como restritos.
#     """
#     from geopy.distance import geodesic
#     import numpy as np # Adicionado para isnan
#     import pandas as pd # Adicionado para isnull

#     if rotas_df is None or rotas_df.empty or 'Veículo' not in rotas_df.columns or 'Região' not in rotas_df.columns:
#         logging.warning("restringir_1_regiao_por_veiculo: rotas_df inválido ou colunas faltando.")
#         return rotas_df

#     # Fallback se não houver DataFrame de pedidos ou coordenadas para calcular centroides
#     if pedidos is None or 'Latitude' not in pedidos.columns or 'Longitude' not in pedidos.columns or \\
#        'Região' not in pedidos.columns or \\
#        'Latitude' not in rotas_df.columns or 'Longitude' not in rotas_df.columns:
#         logging.warning("restringir_1_regiao_por_veiculo: DataFrame de pedidos ou coordenadas ausentes. Usando fallback (restringe apenas por nome da região predominante).")
#         for veic in rotas_df['Veículo'].unique():
#             if pd.isnull(veic): continue
#             pedidos_veic = rotas_df[rotas_df['Veículo'] == veic]
#             if pedidos_veic.empty or pedidos_veic['Região'].isnull().all():
#                 continue
            
#             regiao_pred_series = pedidos_veic['Região'].mode()
#             if regiao_pred_series.empty:
#                 continue
#             regiao_pred = regiao_pred_series.iloc[0]
            
#             fora_regiao_pred = pedidos_veic[pedidos_veic['Região'] != regiao_pred]
#             for idx in fora_regiao_pred.index:
#                 rotas_df.at[idx, 'Alocacao_Restrita'] = True
#                 pedido_id_log = rotas_df.at[idx, 'Pedido_Index_DF'] if 'Pedido_Index_DF' in rotas_df.columns else idx
#                 logging.warning(f"Pedido {pedido_id_log} está fora da região predominante '{regiao_pred}' do veículo {veic} (fallback).")
#         return rotas_df

#     # Calcular centroides de todas as regiões uma vez
#     centroides_todas_regioes = {}
#     # Garante que pedidos['Região'] seja string para o groupby e get
#     pedidos_copy = pedidos.copy()
#     pedidos_copy['Região'] = pedidos_copy['Região'].astype(str).str.strip().str.title()

#     for reg_nome, grupo_pedidos_regiao in pedidos_copy.groupby('Região'):
#         pedidos_validos_reg = grupo_pedidos_regiao.dropna(subset=['Latitude', 'Longitude'])
#         if not pedidos_validos_reg.empty:
#             lat_centroide_reg = pedidos_validos_reg['Latitude'].mean()
#             lon_centroide_reg = pedidos_validos_reg['Longitude'].mean()
#             centroides_todas_regioes[reg_nome] = (lat_centroide_reg, lon_centroide_reg)
#         else:
#             logging.info(f"Região '{reg_nome}' não possui pedidos com coordenadas válidas para cálculo de centroide.")
            
#     if not centroides_todas_regioes:
#         logging.warning("Nenhum centroide regional pôde ser calculado. Abortando restrição geográfica.")
#         return rotas_df

#     for veic in rotas_df['Veículo'].unique():
#         if pd.isnull(veic): continue
#         pedidos_veic = rotas_df[rotas_df['Veículo'] == veic].copy() # Usar .copy() para evitar SettingWithCopyWarning
        
#         # Padroniza Região no slice do veículo também
#         pedidos_veic['Região'] = pedidos_veic['Região'].astype(str).str.strip().str.title()

#         if pedidos_veic.empty or pedidos_veic['Região'].isnull().all():
#             continue
        
#         regiao_pred_veic_series = pedidos_veic['Região'].value_counts()
#         if regiao_pred_veic_series.empty:
#             continue
#         regiao_pred_veic_nome = regiao_pred_veic_series.index[0]

#         centroide_reg_pred_veic = centroides_todas_regioes.get(regiao_pred_veic_nome)
#         if not centroide_reg_pred_veic:
#             logging.warning(f"Veículo {veic}: Região predominante '{regiao_pred_veic_nome}' não possui centroide. Pedidos podem ser marcados como restritos indevidamente.")
#             # Marcar todos os pedidos deste veículo como restritos se sua região predominante não tem centroide?
#             # Ou pular? Por segurança, marcar como restrito se não puder validar.
#             for idx_veic_ped in pedidos_veic.index:
#                  rotas_df.at[idx_veic_ped, 'Alocacao_Restrita'] = True
#             continue

#         for idx, row in pedidos_veic.iterrows():
#             lat_pedido = row['Latitude']
#             lon_pedido = row['Longitude']
#             reg_pedido_nome = row['Região'] # Já padronizado no slice pedidos_veic

#             pedido_id_log = row['Pedido_Index_DF'] if 'Pedido_Index_DF' in row and pd.notnull(row['Pedido_Index_DF']) else idx


#             if pd.isnull(lat_pedido) or pd.isnull(lon_pedido) or pd.isnull(reg_pedido_nome) or reg_pedido_nome == 'Nan':
#                 rotas_df.at[idx, 'Alocacao_Restrita'] = True
#                 logging.warning(f"Pedido {pedido_id_log} do veículo {veic} marcado como restrito devido a dados faltantes (lat/lon/região).")
#                 continue

#             permitido = False
#             if reg_pedido_nome == regiao_pred_veic_nome:
#                 dist_pedido_a_centroide_pred = geodesic((lat_pedido, lon_pedido), centroide_reg_pred_veic).km
#                 if dist_pedido_a_centroide_pred <= raio_km:
#                     permitido = True
#             else:
#                 centroide_reg_pedido = centroides_todas_regioes.get(reg_pedido_nome)
#                 if centroide_reg_pedido:
#                     dist_centroides_regionais = geodesic(centroide_reg_pedido, centroide_reg_pred_veic).km
#                     if dist_centroides_regionais <= raio_km:
#                         dist_pedido_a_seu_centroide = geodesic((lat_pedido, lon_pedido), centroide_reg_pedido).km
#                         if dist_pedido_a_seu_centroide <= raio_km:
#                             permitido = True
            
#             if permitido:
#                 # Garante que, se permitido, a marcação de restrição seja False (caso tenha sido marcada antes)
#                 if 'Alocacao_Restrita' in rotas_df.columns:
#                     rotas_df.at[idx, 'Alocacao_Restrita'] = False
#             else:
#                 rotas_df.at[idx, 'Alocacao_Restrita'] = True
#                 logging.warning(f"Pedido {pedido_id_log} (Região: {reg_pedido_nome}) do veículo {veic} (Região Pred: {regiao_pred_veic_nome}) marcado como restrito.")
#     return rotas_df

def priorizar_regioes_preferidas(rotas_df, frota, pedidos):
    """
    Move pedidos para veículos que tenham a região do pedido em suas 'Regiões Preferidas' (restrição dura).
    Se não houver capacidade, aloca para o veículo cuja região preferida seja mais próxima.
    Se ainda assim não couber, aloca para qualquer veículo disponível.
    """
    import pandas as pd
    import numpy as np
    from geopy.distance import geodesic
    if rotas_df is None or rotas_df.empty or 'Veículo' not in rotas_df.columns or 'Pedido_Index_DF' not in rotas_df.columns:
        return rotas_df, 0
    if 'Região' not in pedidos.columns:
        return rotas_df, 0
    id_col = 'ID Veículo' if 'ID Veículo' in frota.columns else 'Placa'
    regioes_pref_dict = {}
    regioes_centroides = {}
    for _, row in frota.iterrows():
        veic = row.get(id_col)
        regioes_pref = row.get('Regiões Preferidas', '')
        regioes_pref_list = [r.strip().lower() for r in str(regioes_pref).split(',') if r.strip()]
        regioes_pref_dict[veic] = regioes_pref_list
        # Calcula centroide das regiões preferidas do veículo
        for reg in regioes_pref_list:
            if reg and reg not in regioes_centroides and reg in pedidos['Região'].str.lower().values:
                pedidos_reg = pedidos[pedidos['Região'].str.lower() == reg]
                if not pedidos_reg.empty:
                    lat = pedidos_reg['Latitude'].mean()
                    lon = pedidos_reg['Longitude'].mean()
                    regioes_centroides[reg] = (lat, lon)
    pedido_regiao = pedidos['Região'].fillna('').astype(str).str.lower().tolist()
    pedido_lat = pedidos['Latitude'].tolist() if 'Latitude' in pedidos.columns else None
    pedido_lon = pedidos['Longitude'].tolist() if 'Longitude' in pedidos.columns else None
    capacidades = frota.set_index(id_col)['Capacidade (Kg)'].to_dict() if 'Capacidade (Kg)' in frota.columns else {}
    realocados = 0
    for idx, row in rotas_df.iterrows():
        veic_atual = row['Veículo']
        pedido_idx = row['Pedido_Index_DF']
        if pd.isnull(pedido_idx):
            continue
        pedido_idx = int(pedido_idx)
        regiao_pedido = pedido_regiao[pedido_idx] if pedido_idx < len(pedido_regiao) else ''
        lat_pedido = pedido_lat[pedido_idx] if pedido_lat and pedido_idx < len(pedido_lat) else None
        lon_pedido = pedido_lon[pedido_idx] if pedido_lon and pedido_idx < len(pedido_lon) else None
        if not regiao_pedido:
            continue
        # 1. Tenta alocar para veículos preferenciais (restrição dura)
        veics_pref = [v for v, regs in regioes_pref_dict.items() if regiao_pedido in regs]
        demanda = row['Demanda'] if 'Demanda' in row else 0
        melhor_veic = None
        menor_carga = None
        for v in veics_pref:
            cap = capacidades.get(v, None)
            if cap is None:
                continue
            carga_atual = rotas_df[rotas_df['Veículo'] == v]['Demanda'].sum() if 'Demanda' in rotas_df.columns else 0
            if carga_atual + demanda > cap:
                continue
            if menor_carga is None or carga_atual < menor_carga:
                melhor_veic = v
                menor_carga = carga_atual
        if melhor_veic and melhor_veic != veic_atual:
            rotas_df.at[idx, 'Veículo'] = melhor_veic
            realocados += 1
            continue
        # 2. Se não couber, busca veículo cuja região preferida seja mais próxima (restrição dura)
        if veics_pref and not melhor_veic:
            min_dist = None
            veic_mais_proximo = None
            for v, regs in regioes_pref_dict.items():
                for reg in regs:
                    if reg in regioes_centroides and lat_pedido is not None and lon_pedido is not None:
                        dist = geodesic((lat_pedido, lon_pedido), regioes_centroides[reg]).km
                        cap = capacidades.get(v, None)
                        carga_atual = rotas_df[rotas_df['Veículo'] == v]['Demanda'].sum() if 'Demanda' in rotas_df.columns else 0
                        if cap is not None and carga_atual + demanda <= cap:
                            if min_dist is None or dist < min_dist:
                                min_dist = dist
                                veic_mais_proximo = v
            if veic_mais_proximo and veic_mais_proximo != veic_atual:
                rotas_df.at[idx, 'Veículo'] = veic_mais_proximo
                realocados += 1
                continue
        # 3. Fallback: NÃO permite alocação para veículos fora das regiões preferidas
        # Ou seja, pedidos que não couberem em nenhum veículo preferencial permanecem como estão
        # (Opcional: pode-se marcar esses pedidos para análise posterior)
        # Exemplo de log para pedidos não alocados:
        if not veics_pref or (veics_pref and not melhor_veic and not veic_mais_proximo):
            logging.warning(f"Pedido {pedido_idx} (região '{regiao_pedido}') NÃO será alocado: nenhum veículo com região preferida disponível/capaz. Veículo atual: {veic_atual}.")
            # Opcional: marcar para análise
            rotas_df.at[idx, 'Alocacao_Restrita'] = True
            continue
    return rotas_df, realocados

# --- NOVAS FUNÇÕES DE LOOPS INTELIGENTES ---
def loop_realocacao_pedidos_restritos(rotas_df, frota, pedidos, raio_km=5, max_iter=10):
    """
    Repete a realocação de pedidos restritos até que o número de pedidos restritos não diminua mais.
    Retorna o DataFrame final e o número de realocações totais.
    """
    n_restritos_ant = -1
    total_realocados = 0
    for _ in range(max_iter):
        n_restritos = rotas_df['Alocacao_Restrita'].sum() if 'Alocacao_Restrita' in rotas_df.columns else 0
        if n_restritos_ant == n_restritos:
            break
        rotas_df, realocados = realocar_pedidos_restritos(rotas_df, frota, pedidos, raio_km=raio_km)
        total_realocados += realocados
        n_restritos_ant = n_restritos
    return rotas_df, total_realocados

def loop_reserva_dinamica_veiculos(rotas_df, frota, pedidos, max_iter=5, n_reservas=1):
    """
    Reserva veículos para regiões críticas de forma adaptativa, recalculando as regiões a cada iteração.
    Útil para cenários onde o volume de pedidos muda após realocações/balanceamentos.
    """
    for _ in range(max_iter):
        regioes_criticas = pedidos['Região'].value_counts().head(n_reservas).index.tolist()
        veiculos_ativos = frota['ID Veículo'] if 'ID Veículo' in frota.columns else frota['Placa']
        veiculos_ativos = veiculos_ativos.dropna().unique().tolist()
        for i, reg in enumerate(regioes_criticas):
            if i < len(veiculos_ativos):
                veic = veiculos_ativos[i]
                idxs = rotas_df[rotas_df['Região'] == reg].index
                rotas_df.loc[idxs, 'Veículo'] = veic
        # Após reserva, pode-se rebalancear ou realocar pedidos restritos, se desejado
    return rotas_df

def loop_simulacao_cenarios(
    rotas_df, frota, pedidos, matriz_distancias,
    cenarios,
    funcao_roteirizacao,
    metrica_avaliacao=None
):
    """
    Executa múltiplos cenários de roteirização variando parâmetros e retorna um comparativo dos resultados.
    - cenarios: lista de dicionários com parâmetros a variar (ex: [{'capacidade': 1000, 'raio': 20}, ...])
    - funcao_roteirizacao: função que executa o pipeline de roteirização dado um conjunto de parâmetros
    - metrica_avaliacao: função que recebe rotas_df e retorna um dicionário de métricas (ex: total km, balanceamento, etc)
    Retorna: lista de resultados por cenário
    """
    resultados = []
    for params in cenarios:
        # Executa pipeline de roteirização com os parâmetros do cenário
        rotas_df_copia = rotas_df.copy(deep=True)
        frota_copia = frota.copy(deep=True)
        pedidos_copia = pedidos.copy(deep=True)
        rotas_result = funcao_roteirizacao(
            rotas_df_copia, frota_copia, pedidos_copia, matriz_distancias, **params
        )
        if metrica_avaliacao:
            metricas = metrica_avaliacao(rotas_result, frota_copia, pedidos_copia, matriz_distancias)
        else:
            metricas = {'n_pedidos': len(rotas_result), 'n_veiculos': rotas_result['Veículo'].nunique()}
        resultados.append({'parametros': params, 'metricas': metricas, 'rotas_df': rotas_result})
    return resultados

# Placeholder para balanceamento visual/interativo
# (Sugestão: usar Streamlit AgGrid, Dash, ou JS para drag-and-drop)
def balanceamento_visual_placeholder():
    """
    Placeholder para futura integração de balanceamento visual/interativo.
    """
    pass

# Placeholder para agrupamento por aprendizado de máquina
def sugerir_agrupamento_ml(pedidos, historico=None):
    """
    Sugere agrupamento de pedidos usando modelo de ML treinado (placeholder).
    """
    # Exemplo: usar clustering, classificação, ou regras aprendidas do histórico
    # Integrar com routing/aprendizado.py futuramente
    pedidos['Cluster_ML'] = 0 # TODO: implementar
    return pedidos

# --- IDEIAS EXTRAS PARA BALANCEAMENTO E AGRUPAMENTO INTELIGENTE ---
# 1. Balanceamento multi-critério: combinar peso, número de paradas e distância total.
# 2. Penalizar rotas que cruzam regiões diferentes (aumentar custo se misturar regiões).
# 3. Usar heurísticas de vizinhança: mover pedidos para veículos que já atendem clientes próximos.
# 4. Permitir "reserva" de veículos para regiões críticas (ex: regiões com muitos pedidos).
# 5. Implementar balanceamento iterativo até convergência de todos os critérios.
# 6. Adicionar restrição de distância máxima por veículo.
# 7. Permitir balanceamento visual/interativo na interface (drag-and-drop).
# 8. Usar aprendizado de máquina para sugerir agrupamentos baseados em roteirizações históricas.

# Exemplo de uso modularizado (pode ser removido ou usado em testes)
def exemplo_uso():
    """Exemplo de uso das funções de pós-processamento."""
    dist_matrix = np.array([
        [0, 10, 15, 20, 25],
        [10, 0, 35, 25, 30],
        [15, 35, 0, 30, 20],
        [20, 25, 30, 0, 10],
        [25, 30, 20, 10, 0]
    ])
    rota_inicial = [0, 1, 3, 2, 4, 0]
    logging.info(f"Rota Inicial: {rota_inicial}, Distância: {calcular_distancia_rota(rota_inicial, dist_matrix)}")
    rota_otimizada_2opt = heuristica_2opt(rota_inicial, dist_matrix)
    logging.info(f"Rota Otimizada (2-opt): {rota_otimizada_2opt}, Distância: {calcular_distancia_rota(rota_otimizada_2opt, dist_matrix)}")
    rota_swap = swap(rota_otimizada_2opt, 1, 3)
    logging.info(f"Rota após Swap(1, 3): {rota_swap}, Distância: {calcular_distancia_rota(rota_swap, dist_matrix)}")
    rota_longa = [0, 1, 2, 3, 4, 1, 2, 3, 4, 0]
    sub_rotas = split(rota_longa, max_paradas_por_subrota=3)
    for sr in sub_rotas:
        logging.info(f"Sub-rota: {sr}, Distância: {calcular_distancia_rota(sr, dist_matrix)}")
    rotas_para_merge = [[0, 1, 0], [0, 4, 3, 0], [0, 2, 0]]
    demandas_exemplo = [0, 5, 8, 3, 6]
    capacidade_exemplo = 15
    rotas_merged = merge(rotas_para_merge, dist_matrix, capacidade_maxima=capacidade_exemplo, demandas=demandas_exemplo)
    for rm in rotas_merged:
        demanda_rm = sum(demandas_exemplo[node] for node in rm if node != 0 and node < len(demandas_exemplo))
        logging.info(f"Rota Merge: {rm}, Distância: {calcular_distancia_rota(rm, dist_matrix)}, Demanda: {demanda_rm}")
    rota_otimizada_3opt = heuristica_3opt(rota_inicial, dist_matrix)
    logging.info(f"Rota Otimizada (3-opt via 2-opt): {rota_otimizada_3opt}, Distância: {calcular_distancia_rota(rota_otimizada_3opt, dist_matrix)}")

if __name__ == '__main__':
    exemplo_uso()

# --- FIM DAS NOVAS FUNÇÕES DE LOOPS INTELIGENTES ---

def executar_pos_processamento_completo(rotas_df_inicial, frota_df, pedidos_df, matriz_distancias, progress_callback=None, **kwargs):
    """
    Orquestra o fluxo completo de pós-processamento das rotas.

    Args:
        rotas_df_inicial (pd.DataFrame): DataFrame com a alocação inicial.
        frota_df (pd.DataFrame): DataFrame com informações da frota.
        pedidos_df (pd.DataFrame): DataFrame com informações dos pedidos.
        matriz_distancias (np.ndarray): Matriz de distâncias.
        progress_callback (function, optional): Função para reportar progresso.
        respeitar_regioes_preferidas (bool, optional): Se True, executa priorização de regiões preferidas.
        raio_km_realocacao_restritos (float, optional): Raio em km para realocação de pedidos restritos.
        Outros kwargs opcionais podem ser adicionados conforme necessário.

    Returns:
        pd.DataFrame: DataFrame de rotas pós-processado.
    """
    # Permite argumentos opcionais
    import inspect
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    kwargs = values.get('kwargs', {}) if 'kwargs' in values else {}

    # Suporte a argumentos opcionais
    from typing import Any
    def get_kwarg(name: str, default: Any):
        if name in values:
            return values[name]
        if name in kwargs:
            return kwargs[name]
        return default

    respeitar_regioes_preferidas = get_kwarg('respeitar_regioes_preferidas', False)
    raio_km_realocacao_restritos = get_kwarg('raio_km_realocacao_restritos', 30.0)

    # Definição das suas constantes de configuração
    RAIO_KM_AGRUPAMENTO = 25.0
    CAPACIDADE_MIN_PCT_AGRUPAMENTO = 0.6
    MIN_PEDIDOS_AGRUPAMENTO = 5
    LIMITE_SOBRECARGA_PCT = 100
    RAIO_KM_REALOCACAO_RESTRITOS = raio_km_realocacao_restritos
    MAX_ITER_REALOCACAO = 5

    rotas_df = rotas_df_inicial.copy()

    if 'Alocacao_Restrita' not in rotas_df.columns:
        rotas_df['Alocacao_Restrita'] = False
    else:
        rotas_df['Alocacao_Restrita'] = rotas_df['Alocacao_Restrita'].fillna(False)

    logging.info("Iniciando Pós-processamento Completo.")
    if progress_callback: progress_callback(0.0, "Iniciando Pós-processamento...")

    # Etapa 1: Alocação inicial por capacidade e região
    if progress_callback: progress_callback(0.05, "Etapa 1/7: Alocação inicial por capacidade e região...")
    logging.info("Etapa 1: Alocação inicial por capacidade e região.")
    rotas_df = alocar_veiculos_por_capacidade_regiao(rotas_df, frota_df, pedidos_df, 
                                                     modo='capacidade', marcar_restrito=False)
    logging.info(f"Após alocação inicial: {len(rotas_df[rotas_df['Veículo'].notnull()])} pedidos alocados.")
    if progress_callback: progress_callback(0.15, "Etapa 1/7: Concluída.")

    # Etapa 2: Priorizar regiões preferidas (condicional)
    if respeitar_regioes_preferidas:
        if progress_callback: progress_callback(0.20, "Etapa 2/7: Priorizando regiões preferidas...")
        logging.info("Etapa 2: Priorizando regiões preferidas...")
        rotas_df, realocados_pref = priorizar_regioes_preferidas(rotas_df, frota_df, pedidos_df)
        logging.info(f"{realocados_pref} pedidos foram movidos para veículos com região preferida.")
        if progress_callback: progress_callback(0.30, "Etapa 2/7: Concluída.")
    else:
        if progress_callback: progress_callback(0.20, "Etapa 2/7: Pulando priorização de regiões preferidas...")
        logging.info("Etapa 2: Priorização de regiões preferidas pulada (opção desativada).")
        if progress_callback: progress_callback(0.30, "Etapa 2/7: Pulada.")
    
    # Etapa 3: Alocação por Região Predominante com Agrupamento Flexível
    if progress_callback: progress_callback(0.35, "Etapa 3/7: Aplicando agrupamento flexível de regiões...")
    logging.info("Etapa 3: Aplicando alocação por região predominante com agrupamento flexível...")
    rotas_df = alocar_regiao_predominante_com_agrupamento_vizinho(
        rotas_df, frota_df, pedidos_df,
        raio_km=RAIO_KM_AGRUPAMENTO,
        capacidade_min_pct=CAPACIDADE_MIN_PCT_AGRUPAMENTO,
        min_pedidos=MIN_PEDIDOS_AGRUPAMENTO
    )
    pedidos_restritos_apos_agrupamento = rotas_df['Alocacao_Restrita'].sum()
    logging.info(f"Após agrupamento flexível: {pedidos_restritos_apos_agrupamento} pedidos marcados como Alocacao_Restrita.")
    if progress_callback: progress_callback(0.50, "Etapa 3/7: Concluída.")

    # Etapa 4: Checar e Corrigir Excesso de Carga
    if progress_callback: progress_callback(0.55, "Etapa 4/7: Checando e corrigindo excesso de carga...")
    logging.info("Etapa 4: Checando e corrigindo excesso de carga...")
    rotas_df, excesso_final = checar_e_corrigir_excesso_carga(rotas_df, frota_df, limite_pct=LIMITE_SOBRECARGA_PCT)
    if excesso_final:
        logging.warning(f"Veículos com excesso de carga não resolvido: {excesso_final}")
    pedidos_sem_veiculo_apos_correcao_carga = rotas_df['Veículo'].isnull().sum()
    logging.info(f"{pedidos_sem_veiculo_apos_correcao_carga} pedidos ficaram sem veículo após correção de excesso de carga.")
    if progress_callback: progress_callback(0.65, "Etapa 4/7: Concluída.")

    # Etapa 5: Marcar Pedidos Sem Veículo como Restritos
    if progress_callback: progress_callback(0.70, "Etapa 5/7: Marcando pedidos sem veículo como restritos...")
    logging.info("Etapa 5: Marcando pedidos sem veículo como restritos...")
    pedidos_sem_veiculo_indices = rotas_df[rotas_df['Veículo'].isnull()].index
    if not pedidos_sem_veiculo_indices.empty:
        rotas_df.loc[pedidos_sem_veiculo_indices, 'Alocacao_Restrita'] = True

        logging.info(f"{len(pedidos_sem_veiculo_indices)} pedidos sem veículo foram marcados como Alocacao_Restrita.")
    if progress_callback: progress_callback(0.75, "Etapa 5/7: Concluída.")

    # Etapa 6: Realocar Pedidos Restritos (Iterativamente)
    if progress_callback: progress_callback(0.75, "Etapa 6/7: Realocando pedidos restritos...")
    logging.info("Etapa 6: Tentando realocar pedidos restritos...")
    rotas_df, total_realocados_loop = loop_realocacao_pedidos_restritos(
        rotas_df, frota_df, pedidos_df,
        raio_km=RAIO_KM_REALOCACAO_RESTRITOS,
        max_iter=MAX_ITER_REALOCACAO
    )
    logging.info(f"{total_realocados_loop} pedidos restritos foram realocados.")
    pedidos_restritos_final = rotas_df['Alocacao_Restrita'].sum()
    logging.info(f"Após loop de realocação: {pedidos_restritos_final} pedidos permanecem como Alocacao_Restrita.")
    if progress_callback: progress_callback(0.85, "Etapa 6/7: Concluída.")

    # Etapa 7: Balanceamento de Carga Final
    if progress_callback: progress_callback(0.85, "Etapa 7/7: Balanceando carga final...")
    logging.info("Etapa 7: Balanceando carga entre veículos utilizados...")
    rotas_df = balancear_carga_e_usar_todos_veiculos(rotas_df, frota_df, pedidos_df, 
                                                     criterio_balanceamento='peso', priorizar_regiao=True)
    rotas_df = balancear_carga_e_usar_todos_veiculos(rotas_df, frota_df, pedidos_df, 
                                                     criterio_balanceamento='paradas', priorizar_regiao=True)
    logging.info("Balanceamento de carga finalizado.")
    if progress_callback: progress_callback(1.0, "Pós-processamento Concluído.")
    
    logging.info("Pós-processamento Completo Finalizado.")
    return rotas_df