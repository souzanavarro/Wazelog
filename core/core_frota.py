import pandas as pd

def carregar_dados_frota(caminho_planilha="frota.xlsx"):
    """
    Carrega os dados da planilha de frota e retorna uma lista de dicionários.
    """
    try:
        df = pd.read_excel(caminho_planilha)
        frota = df.to_dict(orient="records")
        return frota
    except Exception as e:
        print(f"Erro ao carregar a planilha de frota: {e}")
        return []

def cadastrar_veiculo(placa, transportador, descricao, capacidade_kg, capacidade_m3, tipo, custo_km, disponibilidade, local_partida, local_chegada):
    """
    Cadastra um novo veículo na frota.
    """
    novo_veiculo = {
        "Placa": placa,
        "Transportador": transportador,
        "Descrição Veículo": descricao,
        "Capacidade (Kg)": capacidade_kg,
        "Capacidade (m³)": capacidade_m3,
        "Tipo": tipo,
        "Custo por Km": custo_km,
        "Disponibilidade": disponibilidade,
        "Local de Partida": local_partida,
        "Local de Chegada": local_chegada
    }
    # Aqui você pode salvar o veículo em um banco de dados ou arquivo
    return novo_veiculo