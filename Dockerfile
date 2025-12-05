# Imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do serviço
COPY . .

# Expõe as portas necessárias
EXPOSE 8000
EXPOSE 8080
EXPOSE 80
EXPOSE 443

# Comando padrão para iniciar o serviço
CMD ["python", "app.py"]
