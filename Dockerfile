FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY run.py .

RUN mkdir -p data

EXPOSE 8000

CMD ["python", "run.py"]