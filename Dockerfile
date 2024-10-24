# Usar uma imagem base Python otimizada
FROM python:3.13-slim AS builder

# Atualizar e instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev

# Definir o diretório de trabalho
WORKDIR /app

# Copiar apenas os requisitos para aproveitar o cache de camadas do Docker
COPY requirements.txt .

# Instalar as dependências do Python em uma camada separada
RUN pip install --no-cache-dir -r requirements.txt

# Segunda fase: criar uma imagem mais limpa e otimizada
FROM python:3.13-slim

# Atualizar e instalar ferramentas de sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim procps psmisc

# Definir o diretório de trabalho
WORKDIR /app

# Copiar as dependências instaladas da imagem de construção
COPY --from=builder /usr/local /usr/local

# Copiar apenas o código da aplicação, excluindo requirements.txt para evitar duplicação
COPY *.py ./
COPY .env ./
RUN rm -f requirements.txt

# Criar um arquivo .env com variáveis de ambiente necessárias
RUN echo "OPENCHARGEMAP_API_KEY=cbf5ac49-7c93-488c-a124-686ec20d4bcd\nSUPABASE_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0dWdqdW1neHd5dmZkYm94ZGhqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY3NzY1MjYsImV4cCI6MjA0MjM1MjUyNn0.9tV2xrsMLv8eZxJth8-U0mwMkJO7QpzmX_ruSWQS9U4\nSUPABASE_AUTH_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml0dWdqdW1neHd5dmZkYm94ZGhqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjY3NzY1MjYsImV4cCI6MjA0MjM1MjUyNn0.9tV2xrsMLv8eZxJth8-U0mwMkJO7QpzmX_ruSWQS9U4\nMAPBOX_ACCESS_TOKEN=pk.eyJ1IjoicmVsbHVtbXVsbGVyIiwiYSI6ImNtMWFzMWphcDE1dWYyam9mYnEzZ2k0dnkifQ.K9MDEUYaJnRwtc7O2jiWIQ" > .env

# Definir variáveis de ambiente (se necessário)
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Criar e usar um usuário não-root específico
RUN adduser --disabled-password --gecos '' evpostosuser01 \
    && echo "evpostosuser01:Feito#2Melh0rqPerfeito!3" | chpasswd

# Alterar proprietário da pasta para o usuário criado
RUN chown -R evpostosuser01:evpostosuser01 /app

# Alternar para o usuário não-root
USER evpostosuser01

# Criar um ambiente virtual e instalar Flask com suporte a async, python-dotenv e aiohttp
RUN python -m venv venv \
    && ./venv/bin/pip install --no-cache-dir "flask[async]" python-dotenv aiohttp

# Expor a porta 5000
EXPOSE 5000

# Comando para executar a aplicação Flask
CMD ["./venv/bin/python", "app.py"]
