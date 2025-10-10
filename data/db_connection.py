import psycopg2
import json
import os

def get_connection():
    config_path = os.path.join(os.path.dirname(__file__), "../config/config.json")
    with open(config_path) as f:
        config = json.load(f)["postgres"]

    conn = psycopg2.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"]
    )
    return conn
