
from locust import HttpUser, task, between
import random

class PredictionUser(HttpUser):
    wait_time = between(1, 2)
    
    def on_start(self):
        self.api_key = "race-weekend-key-2026"
        self.headers = {
            "X-Apex-Key": self.api_key,
            "Content-Type": "application/json"
        }
        self.drivers = ["HAM", "VER", "LEC", "NOR", "ALO"]
        self.circuits = ["monaco", "spa", "silverstone", "monza"]

    @task(3)
    def predict_lap_time(self):
        payload = {
            "driver_id": random.choice(self.drivers),
            "circuit_id": random.choice(self.circuits),
            "fuel_load": random.uniform(10.0, 100.0),
            "tire_compound": random.choice(["SOFT", "MEDIUM", "HARD"]),
            "track_temp": random.uniform(20.0, 45.0),
            "session_type": "RACE"
        }
        self.client.post("/v1/predict", json=payload, headers=self.headers)

    @task(1)
    def check_health(self):
        self.client.get("/health")

    @task(1)
    def predict_batch(self):
        requests = []
        for _ in range(5):
            requests.append({
                "driver_id": random.choice(self.drivers),
                "circuit_id": random.choice(self.circuits),
                "fuel_load": random.uniform(10.0, 100.0),
                "tire_compound": random.choice(["SOFT", "MEDIUM", "HARD"]),
                "track_temp": random.uniform(20.0, 45.0),
                "session_type": "RACE"
            })
        self.client.post("/v1/predict/batch", json={"requests": requests}, headers=self.headers)
