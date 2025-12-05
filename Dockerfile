FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DYNAMODB_ENDPOINT=http://analytics-dynamodb:8000

EXPOSE 8000 8080 80 443

CMD ["python", "app.py"]
