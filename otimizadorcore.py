import logging
import re
from typing import Any, Dict, List

# Configurando o logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def trajetos_otimizados_internal(
    data: Dict[str, Any],
    varInfoOpenMaps: List[Dict[str, Any]],
    varInfoDadosVeiculo: Dict[str, Any]
) -> Dict[str, Any]:
    try:
        logger.info("Executando trajetos_otimizados_internal")
        
        # Extraindo prioridades e definindo pesos
        prioridades = [data.get(f"priorizacao_parametro{i}") for i in range(1, 4)]
        pesos = {"tempo": 0, "distancia": 0, "custo": 0}
        for i, prioridade in enumerate(prioridades):
            if prioridade == "Tempo":
                pesos["tempo"] = 10 - i
            elif prioridade == "Distância":
                pesos["distancia"] = 10 - i
            elif prioridade == "Custo":
                pesos["custo"] = 10 - i
            else:
                # Definindo um peso padrão se a prioridade não for encontrada
                pesos["tempo"] = 5
                pesos["distancia"] = 5
                pesos["custo"] = 5

        # Definindo velocidade média e capacidade da bateria
        velocidade_media = 80  # km/h
        capacidade_bateria = varInfoDadosVeiculo.get("capacidade_bateria", 50)  # kWh (exemplo)

        postos_otimizados = []
        for posto in varInfoOpenMaps:
            # Extrair distância, garantindo que seja um float
            distancia = posto.get("AddressInfo", {}).get("Distance")
            if distancia is None:
                distancia = 1.0
            else:
                distancia = float(distancia)

            # Extrair custo (remover caracteres não numéricos e ajustar separadores)
            usage_cost_str = posto.get("UsageCost") or "0"
            usage_cost_str = str(usage_cost_str)
            # Remover caracteres não numéricos (exceto '.' e ',')
            usage_cost_clean = re.sub(r'[^0-9.,]', '', usage_cost_str)
            # Remover separadores de milhar (pontos)
            usage_cost_clean = usage_cost_clean.replace('.', '')
            # Substituir vírgula por ponto para separador decimal
            usage_cost_clean = usage_cost_clean.replace(',', '.')
            # Verificar se o resultado é um número válido
            try:
                usage_cost = float(usage_cost_clean) if usage_cost_clean else 0.0
            except ValueError:
                logger.warning(f"Uso de custo inválido '{usage_cost_str}' no posto {posto.get('ID')}, definindo como 0.0")
                usage_cost = 0.0

            # Calcular tempo de carregamento
            connections = posto.get("Connections") or []
            power_kws = [conector.get("PowerKW", 0) or 0 for conector in connections]
            max_power_kw = max(power_kws) if power_kws else 0
            if max_power_kw > 0:
                tempo_carregamento = capacidade_bateria / max_power_kw  # horas para carregar 100%
            else:
                tempo_carregamento = float('inf')  # Sem capacidade de carregamento

            # Calcular tempo de viagem
            tempo_viagem = distancia / velocidade_media  # horas
            tempo_total = tempo_viagem + tempo_carregamento

            # Calcular score com base nos pesos
            score = (
                pesos["tempo"] * tempo_total +
                pesos["distancia"] * distancia +
                pesos["custo"] * usage_cost
            )

            # Adicionar informações ao posto
            posto["score"] = score
            posto["tempo_total"] = tempo_total
            posto["distancia"] = distancia
            posto["usage_cost"] = usage_cost

            postos_otimizados.append(posto)

        # Ordenar os postos pelo score (menor score é melhor)
        postos_otimizados = sorted(postos_otimizados, key=lambda x: x["score"])

        # Manter somente os 5 primeiros registros
        postos_otimizados = postos_otimizados[:5]

        logger.debug(f"Resultado da otimização de trajetos: {postos_otimizados}")
        return {"postos_otimizados": postos_otimizados}
    except Exception as e:
        logger.error(f"Erro na função trajetos_otimizados_internal: {str(e)}")
        return {"error": str(e)}