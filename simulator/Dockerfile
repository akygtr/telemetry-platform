FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 simuser

WORKDIR /sim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY simulate.py .

USER simuser
CMD ["python", "simulate.py"]
