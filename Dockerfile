FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install certifi and set SSL_CERT_FILE
RUN pip install certifi
ENV SSL_CERT_FILE=/usr/local/lib/python3.x/site-packages/certifi/cacert.pem

# Or dynamically
RUN echo "export SSL_CERT_FILE=$(python -m certifi)" >> /etc/environment


RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

COPY . .

USER myuser

ENV PATH="/home/myuser/.local/bin:$PATH"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]