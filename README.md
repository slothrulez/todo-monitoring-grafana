# Flask TODO Monitoring

This project features a Flask-based TODO API for managing tasks through REST endpoints, with implemented POST and GET routes to add and list todos, stored in a MariaDB database. Prometheus is integrated to collect custom metrics such as request counts, latency, database connections, and todo actions, defined in a separate `metrics.py` file. Grafana is configured with a custom 15-panel dashboard to visualize these metrics in real-time. The entire setup—Flask, MariaDB, Prometheus, and Grafana—is containerized using Docker Compose for straightforward deployment.

## Setup

1. Clone the repo:
```bash
git clone https://github.com/yourusername/flask-todo-monitoring.git
cd flask-todo-monitoring
```
2. Run with Docker:
```bash
docker-compose up --build
```

* API: http://localhost:5000
* Prometheus: http://localhost:9090
* Grafana: http://localhost:3000 (admin/admin)
  
## Usage
Add a TODO:
```bash
curl -X POST -H "Content-Type: application/json" -d '{"task":"Buy groceries"}' http://localhost:5000/todos
```

List TODOs:
```bash
curl http://localhost:5000/todos
```

View metrics in Grafana:
* Import flask_app_monitoring.json at http://localhost:3000.

## Files

* app.py: Flask API
* metrics.py: Custom metrics
* Dockerfile: Flask app container
* docker-compose.yml: Multi-service setup
* prometheus.yml: Prometheus config
* flask_app_monitoring.json: Grafana dashboard

## Requirements
* Docker
* Git
