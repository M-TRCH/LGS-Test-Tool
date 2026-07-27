FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Docker mode is TCP-only: Windows hosts cannot pass COM ports into the
# container (on a Linux host you could add --device=/dev/ttyUSB0).
ENV LGS_TT_DATA_DIR=/app/data \
    LGS_TT_DOCKER=1

EXPOSE 8080
VOLUME /app/data

CMD ["python", "-m", "app.main"]
