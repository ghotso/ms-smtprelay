FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY smtp_relay.py .

EXPOSE 587

# Use Gunicorn as the production server
CMD ["gunicorn", "--bind", "0.0.0.0:587", "--log-level", "info", "smtp_relay:app"] 