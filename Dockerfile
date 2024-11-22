FROM python:3.9-slim
WORKDIR /microblog
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY app .
RUN mkdir -p /app/static /app/media

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]