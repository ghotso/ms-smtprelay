FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY smtp_relay.py .

EXPOSE 587

CMD ["python", "smtp_relay.py"] 