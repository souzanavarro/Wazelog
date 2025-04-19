import requests

def calcular_distancia_osrm(origem, destino, perfil="driving"):
    """
    Calcula a distância e o tempo entre dois pontos usando OSRM.
    
    :param origem: Coordenadas de origem (latitude, longitude).
    :param destino: Coordenadas de destino (latitude, longitude).
    :param perfil: Perfil de transporte (driving, cycling, walking).
    :return: Dicionário com distância (em metros) e duração (em segundos).
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/{perfil}/{origem[1]},{origem[0]};{destino[1]},{destino[0]}"
        response = requests.get(url, params={"overview": "false"})
        if response.status_code == 200:
            dados = response.json()
            rota = dados["routes"][0]
            return {"distancia": rota["distance"], "duracao": rota["duration"]}
        else:
            print(f"Erro na API OSRM: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao calcular distância: {e}")
        return None

def calcular_distancia_google_maps(origem, destino, api_key, modo="driving"):
    """
    Calcula a distância e o tempo entre dois pontos usando Google Maps API.
    
    :param origem: Endereço ou coordenadas de origem.
    :param destino: Endereço ou coordenadas de destino.
    :param api_key: Chave da API do Google Maps.
    :param modo: Modo de transporte (driving, walking, bicycling, transit).
    :return: Dicionário com distância (em metros) e duração (em segundos).
    """
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": origem,
            "destinations": destino,
            "mode": modo,
            "key": api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            dados = response.json()
            elemento = dados["rows"][0]["elements"][0]
            return {"distancia": elemento["distance"]["value"], "duracao": elemento["duration"]["value"]}
        else:
            print(f"Erro na API Google Maps: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao calcular distância: {e}")
        return None

def calcular_distancia_tempo_origem_destino(origem, destino, api_key=None):
    """
    Calcula a distância e o tempo de viagem entre dois pontos usando a API do OpenStreetMap (gratuita).

    :param origem: Tupla com latitude e longitude do ponto de origem (ex: (lat, lon)).
    :param destino: Tupla com latitude e longitude do ponto de destino (ex: (lat, lon)).
    :param api_key: Não é necessário para OpenStreetMap.
    :return: Dicionário com distância (em metros) e tempo (em segundos).
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{origem[1]},{origem[0]};{destino[1]},{destino[0]}?overview=false"
    response = requests.get(url)

    if response.status_code == 200:
        dados = response.json()
        if dados.get("routes"):
            rota = dados["routes"][0]
            return {
                "distancia": rota["distance"],  # em metros
                "tempo": rota["duration"]       # em segundos
            }
        else:
            raise ValueError("Nenhuma rota encontrada entre os pontos fornecidos.")
    else:
        raise ConnectionError(f"Erro ao acessar a API do OpenStreetMap: {response.status_code}")
