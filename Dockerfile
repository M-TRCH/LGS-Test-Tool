FROM python:3.12-slim

# Hospital-server deployment: TCP to the gateways only. ST-Link, COM ports
# and Opta DFU need USB on the cabinet side and are not used from a server.
#
# tzdata + TZ: soak CSVs are stamped in local time and the 03:00 scheduled
# reset is found by its clock time; a container left on UTC would put it at
# 20:00 and call every one of them unexplained.
# fonts-thai-tlwg-ttf: the site report PDF needs a Thai font, and the ones
# it looks for on Windows do not exist here (app/report_pdf.py).
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata fonts-thai-tlwg-ttf \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV TZ=Asia/Bangkok \
    LGS_TT_DATA_DIR=/app/data \
    LGS_TT_DOCKER=1 \
    PYTHONUNBUFFERED=1

# 8080 web UI; 123/udp the built-in NTP server for the gateways (optional)
EXPOSE 8080 123/udp
VOLUME /app/data

HEALTHCHECK --interval=60s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('LGS_TT_PORT', '8080') + '/', timeout=8)"

CMD ["python", "-m", "app.main"]
