import aiohttp
import logging
import os
from typing import Any, Dict
from dotenv import load_dotenv

# Carregando as variáveis de ambiente
load_dotenv()

# Configurando o logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Carregando chaves de API das variáveis de ambiente
MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN')

# Verificando se as chaves de API estão configuradas
if not all([MAPBOX_ACCESS_TOKEN]):
    logger.error("Uma ou mais chaves de API não estão configuradas nas variáveis de ambiente.")
    raise EnvironmentError("Configure todas as chaves de API nas variáveis de ambiente.")


async def busca_rotas_mapbox(session: aiohttp.ClientSession, latitude: float, longitude: float, veiculo_data: Dict[str, Any], postos_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        logger.info("Executando busca_rotas_mapbox")
        # Extraindo dados necessários
        ev_max_charge = veiculo_data.get("veiculo_capacidadebateria", 40000) * 1000
        ev_initial_charge = veiculo_data.get("statusbateriapercentual", 30)
        ev_initial_charge = (ev_initial_charge / 100) * ev_max_charge

        # Construindo a lista de coordenadas para a API do Mapbox
        destinos = []
        postos_detalhes = []
        for posto in postos_data[:25]:
            lat = posto.get('AddressInfo', {}).get('Latitude')
            lon = posto.get('AddressInfo', {}).get('Longitude')
            posto_id = posto.get("ID")
            distancia = posto.get("distancia")
            score = posto.get("score")
            tempo_total = posto.get("tempo_total")
            usage_cost = posto.get("usage_cost")
            power_kw = posto.get('Connections', [{}])[0].get('PowerKW')
            title = posto.get('AddressInfo', {}).get('Title')

            if lat is not None and lon is not None:
                destinos.append(f"{lon}%2C{lat}")
                postos_detalhes.append({
                    "posto_id": posto_id,
                    "distancia": distancia,
                    "score": score,
                    "tempo_total": tempo_total,
                    "usage_cost": usage_cost,
                    "power_kw": power_kw,
                    "title": title
                })

        if not destinos:
            logger.warning("Nenhum posto válido encontrado para calcular rotas.")
            return {"error": "Nenhum posto válido encontrado para calcular rotas."}

        coordinates = f"{longitude}%2C{latitude}%3B{('%3B'.join(destinos))}"

        url = (
            f"https://api.mapbox.com/directions/v5/mapbox/driving/{coordinates}?"
            "alternatives=false&geometries=geojson&language=pt&overview=full&steps=true"
            "&engine=electric"
            f"&ev_initial_charge={ev_initial_charge}"
            f"&ev_max_charge={ev_max_charge}"
            f"&access_token={MAPBOX_ACCESS_TOKEN}"
        )
        
        async with session.get(url, timeout=10) as response:
            logger.debug(f"HTTP GET {url}")
            response.raise_for_status()
            result = await response.json()
            logger.debug(f"Resultado da resposta Mapbox: {result}")

            # Inserindo detalhes dos postos diretamente na raiz do JSON de retorno
            for posto_detalhe in postos_detalhes:
                posto_id = posto_detalhe.get("posto_id")
                if posto_id is not None:
                    result.update(posto_detalhe)
            
            return result
    except Exception as e:
        logger.error(f"Erro ao buscar rotas no Mapbox: {str(e)}")
        return {"error": str(e)}
