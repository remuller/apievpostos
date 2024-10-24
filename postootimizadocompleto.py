from flask import request, jsonify
import asyncio
import aiohttp
import logging
from typing import Any, Dict, List
from dotenv import load_dotenv
from functools import lru_cache

from integramapbox import busca_rotas_mapbox
from integraopencharge import busca_locais_opencharge
from integrasupabase import dados_supabase
from otimizadorcore import trajetos_otimizados_internal

# Carregando as variáveis de ambiente
load_dotenv()

# Configurando o logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)



# Rota para obter postos próximos
async def postosotimizados():
    try:
        logger.info("/api/postosotimizados endpoint called")
        # Obtendo dados da requisição
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        if not data:
            logger.error("Nenhum dado enviado.")
            return jsonify({"error": "Nenhum dado enviado."}), 400

        # Verificando se os parâmetros necessários estão presentes
        required_params = ["latitude", "longitude", "veiculo_id", "usuario_id"]
        missing_params = [param for param in required_params if data.get(param) is None]
        if missing_params:
            logger.error(f"Parâmetros obrigatórios ausentes: {', '.join(missing_params)}")
            return jsonify({"error": f"Parâmetros obrigatórios ausentes: {', '.join(missing_params)}."}), 400

        latitude = data["latitude"]
        longitude = data["longitude"]
        veiculo_id = data["veiculo_id"]
        usuario_id = data["usuario_id"]

        logger.info("Iniciando busca de informações simultâneas")
        # Executando as funções assíncronas em paralelo
        async with aiohttp.ClientSession() as session:
            tasks = [
                busca_locais_opencharge(session, latitude, longitude),
                dados_supabase(session, "users", usuario_id),
                dados_supabase(session, "veiculos_detalhes_completos", veiculo_id, "veiculo_id")
            ]
            varInfoOpenMaps, varInfoDadosUsuario, varInfoDadosVeiculo = await asyncio.gather(*tasks)

            logger.debug(f"Resultado busca_locais_opencharge: {varInfoOpenMaps}")
            logger.debug(f"Resultado dados_usuario_supabase: {varInfoDadosUsuario}")
            logger.debug(f"Resultado dados_veiculo_supabase: {varInfoDadosVeiculo}")

            if not varInfoOpenMaps or "error" in varInfoOpenMaps:
                logger.error("Não há postos disponíveis nas configurações atuais.")
                return jsonify({"error": "Não há postos disponíveis nas configurações atuais.", "code": 1001}), 400

            if "error" in varInfoDadosUsuario:
                logger.error("Erro ao buscar dados do usuário.")
                return jsonify({"error": "Erro ao buscar dados do usuário."}), 500

            if "error" in varInfoDadosVeiculo:
                logger.error("Erro ao buscar dados do veículo.")
                return jsonify({"error": "Erro ao buscar dados do veículo."}), 500

            # Chamada da função trajetos_otimizados
            prioridades = ["priorizacao_parametro1", "priorizacao_parametro2", "priorizacao_parametro3"]
            prioridades_usuario = {p: varInfoDadosUsuario.get(p) for p in prioridades}
            logger.debug(f"Prioridades do usuário: {prioridades_usuario}")
            if not all(prioridades_usuario.values()):
                logger.error("Parâmetros de priorização do usuário são obrigatórios.")
                return jsonify({"error": "Parâmetros de priorização do usuário são obrigatórios."}), 400

            trajetos_data = prioridades_usuario
            varInfoLogisticaOtimizada = trajetos_otimizados_internal(trajetos_data, varInfoOpenMaps, varInfoDadosVeiculo)
            logger.debug(f"Resultado trajetos_otimizados_internal: {varInfoLogisticaOtimizada}")

            # Chamada da função busca_rotas_mapbox
            varInfoDadosPostosOtimizado = []
            for idx in range(len(varInfoLogisticaOtimizada.get("postos_otimizados", []))):
                posto = varInfoLogisticaOtimizada["postos_otimizados"][idx]
                rota = await busca_rotas_mapbox(session, latitude, longitude, varInfoDadosVeiculo, [posto])
                varInfoDadosPostosOtimizado.append(rota)
                logger.debug(f"Resultado busca_rotas_mapbox para posto {posto}: {rota}")

        return jsonify({
            "message": "Postos próximos encontrados e trajetos otimizados com sucesso.",
            "varInfoOpenMaps": varInfoOpenMaps,
            "varInfoDadosUsuario": varInfoDadosUsuario,
            "varInfoDadosVeiculo": varInfoDadosVeiculo,
            "varInfoLogisticaOtimizada": varInfoLogisticaOtimizada,
            "varInfoDadosPostosOtimizado": varInfoDadosPostosOtimizado
        })
    except Exception as e:
        logger.error(f"Erro no endpoint /api/postosotimizados: {str(e)}")
        return jsonify({"error": str(e)}), 500


