from flask import Flask, request, jsonify
import aiohttp
import logging
import os
from typing import Any, Dict
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

# Configurando o logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Variáveis padrão para maxresults e distancia
DEFAULT_MAXRESULTS = 30
DEFAULT_DISTANCE = 100

# Carregando chaves de API das variáveis de ambiente
OPENCHARGEMAP_API_KEY = os.getenv('OPENCHARGEMAP_API_KEY')

# Verificando se as chaves de API estão configuradas
if not all([OPENCHARGEMAP_API_KEY]):
    logger.error("Uma ou mais chaves de API não estão configuradas nas variáveis de ambiente.")
    raise EnvironmentError("Configure todas as chaves de API nas variáveis de ambiente.")

@lru_cache(maxsize=128)
async def busca_locais_opencharge(session: aiohttp.ClientSession, latitude: float, longitude: float) -> Dict[str, Any]:
    try:
        logger.info("Executando busca_locais_opencharge")
        url = (
            "https://api.openchargemap.io/v3/poi/"
            f"?output=json&latitude={latitude}&longitude={longitude}"
            f"&distance={DEFAULT_DISTANCE}&maxresults={DEFAULT_MAXRESULTS}"
            f"&key={OPENCHARGEMAP_API_KEY}"
        )
        async with session.get(url, timeout=10) as response:
            logger.debug(f"HTTP GET {url}")
            response.raise_for_status()
            result = await response.json()
            logger.debug(f"Resultado da resposta OpenChargeMap: {result}")
            return result
    except Exception as e:
        logger.error(f"Erro ao buscar locais no OpenChargeMap: {str(e)}")
        return {"error": str(e)}
