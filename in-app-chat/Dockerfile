FROM 617217039186.dkr.ecr.eu-central-1.amazonaws.com/local_python:latest

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install dependencies
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     gcc \
#     libpq-dev \
#     kafkacat && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8046
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8046", "--reload"]
