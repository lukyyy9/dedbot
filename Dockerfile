# Dockerfile V2 - Bot DCA avec interface web (Secured & Non-root)
FROM python:3.11-slim

ARG BOT_UID=1000
ARG BOT_GID=1000

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Création d'un groupe et utilisateur non-root dédié
RUN groupadd -g ${BOT_GID} botgroup \
    && useradd -m -u ${BOT_UID} -g botgroup -s /usr/sbin/nologin botuser

WORKDIR /app

# Copier les requirements et installer les dépendances avec pip sécurisé
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copier l'application
COPY core/ /app/core/
COPY templates/ /app/templates/
COPY static/ /app/static/
COPY bot_daily_score_v2.py /app/
COPY backtest_v2.py /app/
COPY web_app.py /app/

# Créer le répertoire de données et ajuster les permissions
RUN mkdir -p /data \
    && chown -R botuser:botgroup /data /app \
    && chmod 700 /data

USER botuser

ENV PYTHONUNBUFFERED=1

# Par défaut, lancer le bot (peut être overridé par docker-compose)
CMD ["python", "bot_daily_score_v2.py"]
