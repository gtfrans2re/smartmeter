"""Locust load generator for the smart-meter pipeline.

Each simulated user produces smart-meter readings to Kafka using the SAME
canonical contract the Spark jobs consume:

    topic   : sensor-data
    payload : {"meter_id": <int>, "voltage": <float>, "timestamp": <float epoch>}

It also emits forecast requests to the ``forecast-data`` topic (consumed by
spark_app5) and exposes Prometheus metrics on :8000.

Run from the Locust container (see docker-compose); the realistic voltage values
come from the interpolated provider classes in this folder.
"""
import json
import random
import time

from locust import User, TaskSet, task, between
from confluent_kafka import Producer
from prometheus_client import start_http_server, Gauge

from valueProvider import ConsumerInterpolatedVoltageProvider

# Prometheus metrics (scraped by Prometheus at locust:8000).
cpu_usage_metric = Gauge('locust_cpu_usage', 'Simulated CPU usage')
voltage_metric = Gauge('locust_voltage_data', 'Last simulated voltage value')

start_http_server(8000)

SENSOR_TOPIC = "sensor-data"
FORECAST_TOPIC = "forecast-data"


class SmartMeterBehavior(TaskSet):
    def on_start(self):
        self.voltage_provider = ConsumerInterpolatedVoltageProvider(
            slot=1, users_per_sec=100, streaming_duration=60,
            randomness=0.5, prediction_length=12,
        )
        self.meter_id = random.randint(1, 50)
        self.producer = Producer({
            'bootstrap.servers': 'kafka:9092',
            'client.id': 'smart-meter-client',
        })

    def on_stop(self):
        self.producer.flush()

    def _send(self, topic, message):
        self.producer.produce(topic, value=json.dumps(message).encode('utf-8'))
        self.producer.poll(0)

    @task(3)
    def send_voltage_data(self):
        """Send a canonical voltage reading to the sensor-data topic."""
        voltage = float(self.voltage_provider.voltage())
        message = {
            "meter_id": self.meter_id,
            "voltage": round(voltage, 3),
            "timestamp": float(int(time.time())),
        }
        self._send(SENSOR_TOPIC, message)
        voltage_metric.set(voltage)
        print(f"sensor-data <- {message}")

    @task(1)
    def send_forecast_request(self):
        """Send a forecast request (future timestamp, no voltage) for app5 to predict."""
        message = {
            "meter_id": self.meter_id,
            "voltage": None,
            "timestamp": float(int(time.time()) + 3600),  # one hour ahead
        }
        self._send(FORECAST_TOPIC, message)
        print(f"forecast-data <- {message}")

    @task(1)
    def simulate_cpu_usage(self):
        cpu_usage = random.uniform(10, 90)
        cpu_usage_metric.set(cpu_usage)


class KafkaUser(User):
    """A non-HTTP user: it talks to Kafka directly, not over HTTP."""
    tasks = [SmartMeterBehavior]
    wait_time = between(1, 3)
