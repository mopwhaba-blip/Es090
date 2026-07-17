FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential python3-dev
COPY requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app
RUN pip install --only-binary=:all: numba --onlybinary=:all: llvmlite
