# Roteirizador Inteligente

Bem-vindo ao **Roteirizador Inteligente**, uma aplicação para otimizar a logística de entregas, desde a importação de pedidos até a geração de rotas otimizadas e aprendizado contínuo.

## Funcionalidades

1. **Importação de Pedidos**:
   - Suporte para arquivos Excel e CSV.
   - Correção de endereços com erros (fuzzy matching).
   - Geocodificação de endereços para obter coordenadas (latitude/longitude).
   - Validação de dados (peso, volume, janelas de entrega).

2. **Clusterização**:
   - Agrupamento de pedidos por proximidade geográfica usando KMeans ou DBSCAN.
   - Associação de clusters a centroides.
   - Priorização de clusters por volume ou urgência.

3. **Distribuição de Carga**:
   - Verificação da disponibilidade dos veículos.
   - Respeito às capacidades máximas (peso/volume).
   - Alocação de pedidos por cluster para veículos.

4. **Otimização de Rotas**:
   - Definição da melhor ordem de entrega usando Google OR-Tools.
   - Minimização de distância ou tempo.
   - Consideração de janelas de entrega e ponto de partida.

5. **Visualização e Exportação**:
   - Geração de mapas interativos com Folium.
   - Exportação de rotas para Excel.
   - Salvamento no histórico para aprendizado futuro.

6. **Aprendizado Contínuo**:
   - Avaliação de performance (atrasos, desvios, tempos reais).
   - Reforço de rotas que funcionaram bem.
   - Ajustes baseados em feedback.

## Tecnologias Utilizadas

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: Python
- **Bibliotecas**:
  - `pandas`, `numpy`, `scikit-learn` para manipulação de dados e aprendizado de máquina.
  - `folium`, `geopy` para mapas e geocodificação.
  - `ortools` para otimização de rotas.
  - `fuzzywuzzy` para correção de endereços.
  - `requests` para integração com APIs.

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/roteirizador-inteligente.git
   cd roteirizador-inteligente
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Execute o aplicativo:
   ```bash
   streamlit run app.py
   ```

## Estrutura do Projeto

```
/workspaces/WazeLog
├── app.py                  # Página inicial e navegação
├── frota.py                # Cadastro e gerenciamento de frota
├── pedidos.py              # Upload e validação de pedidos
├── roteirizacao.py         # Fluxo completo de roteirização
├── core/                   # Módulos principais
│   ├── core_pedidos.py     # Importação e preparação de pedidos
│   ├── core_frota.py       # Gerenciamento de frota
│   ├── core_clusterizacao.py # Clusterização de pedidos
│   ├── core_distribuicao.py  # Distribuição de carga por veículo
│   ├── core_roteirizacao.py  # Otimização de rotas
│   ├── core_exportacao.py    # Exportação e visualização de rotas
│   ├── core_feedback.py      # Feedback e aprendizado contínuo
├── requirements.txt        # Dependências do projeto
└── README.md               # Documentação do projeto
```

## Fluxo do Sistema

```
Importar Pedidos
     ↓
Geocodificar Endereços
     ↓
Separar por Região (Clustering)
     ↓
Distribuir Carga por Veículo
     ↓
Otimizar Rota Interna
     ↓
Gerar Mapa e Exportar
     ↓
Salvar no Histórico para IA
```

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).