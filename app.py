from flask import Flask, request, jsonify
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import os
import time
from prometheus_flask_exporter import PrometheusMetrics
from metrics import *

app = Flask(__name__)

# Initialize Prometheus metrics with an explicit path
metrics = PrometheusMetrics(app, path='/metrics')
init_metrics()
print("PrometheusMetrics initialized at /metrics")  # Debug output

# Static info for the app
metrics.info('app_info', 'Application info', version='1.0.0', environment='development')

DB_CONFIG = {
    'host': 'db',
    'user': 'root',
    'password': 'rootpass',
    'database': 'todos_db'
}

def get_db_connection(retries=10, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            DB_CONNECTIONS.inc()
            print("Successfully connected to MariaDB.")
            return conn
        except Error as e:
            attempt += 1
            DB_ERRORS.labels(operation='connect').inc()
            print(f"Attempt {attempt}/{retries} - Error connecting to MariaDB: {e}")
            if attempt == retries:
                raise Exception("Database connection failed after retries.")
            time.sleep(delay)

def init_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    task VARCHAR(255) NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)
            conn.commit()
            print("Database initialized successfully - 'todos' table ready.")
        except Error as e:
            DB_ERRORS.labels(operation='init').inc()
            print(f"Error initializing database: {e}")
            raise
        finally:
            cursor.close()
            DB_CONNECTIONS.dec()
            conn.close()

@app.route('/todos', methods=['POST'])
def add_todo():
    start_time = time.time()
    data = request.get_json()
    if not data or 'task' not in data:
        REQUEST_COUNT.labels(method='POST', endpoint='/todos', status='400').inc()
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method='POST', endpoint='/todos', status='400').observe(latency)
        return jsonify({"error": "Task is required"}), 400
    
    conn = get_db_connection()
    if not conn:
        REQUEST_COUNT.labels(method='POST', endpoint='/todos', status='500').inc()
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method='POST', endpoint='/todos', status='500').observe(latency)
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor()
        timestamp = datetime.now()
        query = "INSERT INTO todos (task, timestamp) VALUES (%s, %s)"
        cursor.execute(query, (data["task"], timestamp))
        conn.commit()
        
        todo = {
            "id": cursor.lastrowid,
            "task": data["task"],
            "timestamp": timestamp.isoformat()
        }
        TODO_CREATED.inc()
        status = '201'
    except Error as e:
        DB_ERRORS.labels(operation='insert').inc()
        status = '500'
        latency = time.time() - start_time
        REQUEST_COUNT.labels(method='POST', endpoint='/todos', status=status).inc()
        REQUEST_LATENCY.labels(method='POST', endpoint='/todos', status=status).observe(latency)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        DB_CONNECTIONS.dec()
        conn.close()
    
    latency = time.time() - start_time
    REQUEST_COUNT.labels(method='POST', endpoint='/todos', status=status).inc()
    REQUEST_LATENCY.labels(method='POST', endpoint='/todos', status=status).observe(latency)
    return jsonify(todo), 201

@app.route('/todos', methods=['GET'])
def list_todos():
    start_time = time.time()
    conn = get_db_connection()
    if not conn:
        REQUEST_COUNT.labels(method='GET', endpoint='/todos', status='500').inc()
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method='GET', endpoint='/todos', status='500').observe(latency)
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM todos")
        todos = cursor.fetchall()
        for todo in todos:
            todo['timestamp'] = todo['timestamp'].isoformat()
        TODO_LIST_REQUESTS.inc()
        status = '200'
    except Error as e:
        DB_ERRORS.labels(operation='select').inc()
        status = '500'
        latency = time.time() - start_time
        REQUEST_COUNT.labels(method='GET', endpoint='/todos', status=status).inc()
        REQUEST_LATENCY.labels(method='GET', endpoint='/todos', status=status).observe(latency)
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        DB_CONNECTIONS.dec()
        conn.close()
    
    latency = time.time() - start_time
    REQUEST_COUNT.labels(method='GET', endpoint='/todos', status=status).inc()
    REQUEST_LATENCY.labels(method='GET', endpoint='/todos', status=status).observe(latency)
    return jsonify(todos), 200

print("Starting application - waiting for database...")
init_db()

if __name__ == '__main__':
    # Remove debug=True for Docker compatibility
    app.run(port=5000, host='0.0.0.0')