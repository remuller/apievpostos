from flask import Flask, request, jsonify
import asyncio
import logging

from dotenv import load_dotenv

from postootimizadocompleto import postosotimizados
from postootimizadosimples import postosotimizadosindividual
# Carregando as variáveis de ambiente
load_dotenv()

# Inicializando o Flask app
app = Flask(__name__)

# Configurando o logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Rota de exemplo para testar a API
@app.route('/api/hello', methods=['GET'])
async def hello():
    logger.info("/api/hello endpoint called")
    return jsonify({"message": "Hello, World!"})

# Rota para obter postos próximos
@app.route('/api/postocompleto', methods=['POST'])
async def completopostosotimizados():
    result  = await postosotimizados()
    return result

@app.route('/api/postosimples', methods=['POST'])
async def simplepostosotimizados():
    result = await postosotimizadosindividual()
    return result


if __name__ == '__main__':
    logger.info("Iniciando o servidor Flask")
    app.run(debug=True, host='0.0.0.0', port=5000)
