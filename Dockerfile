FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Tạo thư mục logs
RUN mkdir -p logs

COPY elasticsearch/ ./elasticsearch/

CMD ["python", "elasticsearch/create_index.py"]
