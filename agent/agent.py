import psutil
import time
import requests
import os
import socket
import platform


AGENT_TOKEN = os.getenv("AGENT_TOKEN")
if not AGENT_TOKEN:
    AGENT_TOKEN = input("🔑 Entrez le token d'installation : ").strip()



# ================== CONFIG ==================
BACKEND_REGISTER_URL = "http://127.0.0.1:5000/agents/register"
BACKEND_METRICS_URL = "http://127.0.0.1:5000/metrics"
INTERVAL = 3  # secondes

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "agent.conf")
# ============================================


def load_agent_id():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return f.read().split("=")[1].strip()
    return None


def save_agent_id(agent_id):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"AGENT_ID={agent_id}")


def register_agent():
    payload = {
    	"hostname": socket.gethostname(),
    	"ip": socket.gethostbyname(socket.gethostname()),
    	"os": platform.system(),
    	"token": AGENT_TOKEN   # 🔥 AJOUT IMPORTANT
    }


    r = requests.post(BACKEND_REGISTER_URL, json=payload, timeout=5)
    r.raise_for_status()

    agent_id = r.json()["agent_id"]
    save_agent_id(agent_id)

    print(f"✅ Agent enregistré avec ID {agent_id}")
    return agent_id


def collect_metrics(agent_id):
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "agent_id": int(agent_id)
    }


def send_metrics(data):
    try:
        r = requests.post(BACKEND_METRICS_URL, json=data, timeout=5)
        if r.status_code == 200:
            print("✔ Metrics envoyées :", data)
        else:
            print("✖ Erreur backend :", r.status_code)
    except requests.exceptions.RequestException as e:
        print("✖ Backend non disponible :", e)


# ================== MAIN ==================
if __name__ == "__main__":
    print("🟢 Agent de monitoring démarré")

    agent_id = load_agent_id()
    if not agent_id:
        agent_id = register_agent()

    print("🖥️ Agent ID :", agent_id)

    while True:
        metrics = collect_metrics(agent_id)
        send_metrics(metrics)
        time.sleep(INTERVAL)

