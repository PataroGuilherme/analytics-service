import os
import sys
import threading
import json
import uuid
import time
import logging
import boto3
from botocore.config import Config
from flask import Flask, jsonify
from dotenv import load_dotenv

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

load_dotenv()

# --- Configuração ---
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SQS_QUEUE_URL = os.getenv("AWS_SQS_URL")             # http://sqs-local:9324/queue/togglemaster-events
DYNAMODB_TABLE = os.getenv("AWS_DYNAMODB_TABLE")     # ToggleMasterAnalytics
DYNAMODB_ENDPOINT = os.getenv("AWS_DYNAMODB_ENDPOINT") # http://dynamodb-local:8000

if not all([SQS_QUEUE_URL, DYNAMODB_TABLE, DYNAMODB_ENDPOINT]):
    log.critical("Variáveis obrigatórias não definidas!")
    sys.exit(1)

# --- Configuração do Boto3 para AMBIENTE LOCAL ---
boto_config = Config(retries={"max_attempts": 10, "mode": "standard"})

session = boto3.Session(
    aws_access_key_id="fake",
    aws_secret_access_key="fake",
    aws_session_token="fake",
    region_name=AWS_REGION
)

sqs_client = session.client(
    "sqs",
    endpoint_url=os.getenv("AWS_SQS_ENDPOINT", "http://sqs-local:9324"),  # http://sqs-local:9324
    config=boto_config
)

dynamodb_client = session.client(
    "dynamodb",
    endpoint_url=DYNAMODB_ENDPOINT,                  # http://dynamodb-local:8000
    config=boto_config
)

log.info("Clientes Boto3 inicializados para ambiente LOCAL")

# --- Processamento de mensagens SQS ---
def process_message(message):
    try:
        log.info(f"Processando mensagem ID: {message['MessageId']}")
        body = json.loads(message["Body"])

        event_id = str(uuid.uuid4())

        dynamodb_client.put_item(
            TableName=DYNAMODB_TABLE,
            Item={
                "event_id": {"S": event_id},
                "user_id": {"S": body["user_id"]},
                "flag_name": {"S": body["flag_name"]},
                "result": {"BOOL": body["result"]},
                "timestamp": {"S": body["timestamp"]}
            }
        )

        log.info(f"Evento salvo: {event_id}")

        sqs_client.delete_message(
            QueueUrl=SQS_QUEUE_URL,
            ReceiptHandle=message["ReceiptHandle"]
        )

    except Exception as e:
        log.error(f"Erro ao processar mensagem: {e}")

def sqs_worker():
    log.info("Worker SQS iniciado...")
    while True:
        try:
            resp = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10
            )

            msgs = resp.get("Messages", [])
            if not msgs:
                continue

            log.info(f"Recebidas {len(msgs)} mensagens")

            for m in msgs:
                process_message(m)

        except Exception as e:
            log.error(f"Erro no loop SQS: {e}")
            time.sleep(5)

# --- Flask ---
app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

def start_worker():
    t = threading.Thread(target=sqs_worker, daemon=True)
    t.start()

start_worker()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8006)))
