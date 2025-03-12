FROM python:3.12
WORKDIR /AIBot

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]