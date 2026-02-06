# Etapa 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependencias de compilación
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Etapa 2: Runner
FROM python:3.11-slim

WORKDIR /app

# Crear usuario no root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar dependencias instaladas
COPY --from=builder /install /usr/local

# Configurar PYTHONPATH para que 'back' sea reconocido como paquete
ENV PYTHONPATH=/app

# Copiar el código dentro del directorio 'back'
COPY . ./back

# Ajustar permisos y crear directorio de datos
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

# En produccion no usamos --reload
CMD ["uvicorn", "back.main:app", "--host", "0.0.0.0", "--port", "8000"]