from flask import Flask, request, jsonify
import asyncio
import aiohttp
import logging
import os
import re
from typing import Any, Dict, List
from dotenv import load_dotenv
from functools import lru_cache

# Carregando as variáveis de ambiente
load_dotenv()

# Inicializando o Flask app
app = Flask(__name__)

# Configurando o logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Carregando chaves de API das variáveis de ambiente
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')
SUPABASE_AUTH_TOKEN = os.getenv('SUPABASE_AUTH_TOKEN')

# Verificando se as chaves de API estão configuradas
if not all([SUPABASE_API_KEY, SUPABASE_AUTH_TOKEN]):
    logger.error("Uma ou mais chaves de API não estão configuradas nas variáveis de ambiente.")
    raise EnvironmentError("Configure todas as chaves de API nas variáveis de ambiente.")

# URL base do Supabase
SUPABASE_BASE_URL = "https://itugjumgxwyvfdboxdhj.supabase.co/rest/v1"

@lru_cache(maxsize=128)
async def dados_supabase(session: aiohttp.ClientSession, table: str, record_id: str, id_column: str = "id") -> Dict[str, Any]:
    try:
        logger.info(f"Executando dados_supabase para a tabela: {table}, ID: {record_id}")
        url = f"{SUPABASE_BASE_URL}/{table}?{id_column}=eq.{record_id}&select=*"
        headers = {
            "apikey": SUPABASE_API_KEY,
            "Authorization": f"Bearer {SUPABASE_AUTH_TOKEN}",
            "Range": "0-9"
        }
        async with session.get(url, headers=headers, timeout=10) as response:
            logger.debug(f"HTTP GET {url}")
            response.raise_for_status()
            data = await response.json()
            logger.debug(f"Resultado da resposta Supabase: {data}")
            return data[0] if data else {}
    except Exception as e:
        logger.error(f"Erro ao buscar dados do Supabase ({table}): {str(e)}")
        return {"error": str(e)}