FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    git \
    python3-venv \
    python3-pip \
    build-essential \
    curl \
    poppler-utils \
    nodejs \
    npm \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/helmholtz_os

COPY backend/requirements.txt backend/requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r requirements.txt

RUN npm install -g @google/gemini-cli

# --- CUA install (inside existing image) ---
WORKDIR /opt
RUN git clone https://github.com/trycua/cua.git

WORKDIR /opt/cua
RUN python -m venv .venv \
 && . .venv/bin/activate \
 && pip install -U pip \
 && pip install -e .

WORKDIR /workspace/helmholtz_os
COPY . .

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
