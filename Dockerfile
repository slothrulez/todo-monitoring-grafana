FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install flask mysql-connector-python prometheus-client prometheus-flask-exporter

EXPOSE 5000

CMD ["python", "app.py"]