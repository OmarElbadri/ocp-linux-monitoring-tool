from flask import Flask, request, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
import smtplib
from email.mime.text import MIMEText
from twilio.rest import Client
from flask_cors import CORS
import secrets
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()



TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM")  # numéro Twilio sandbox




app = Flask(__name__)
CORS(app)


# Seuils
CPU_THRESHOLD = 80
RAM_THRESHOLD = 80
DISK_THRESHOLD = 90

SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
    except mysql.connector.Error as err:
        print("Erreur MySQL :", err)
        return None


def check_thresholds(cpu, ram, disk):
    alerts = []

    if cpu >= CPU_THRESHOLD:
        alerts.append(("CPU", f"CPU usage high: {cpu}%", "critical"))

    if ram >= RAM_THRESHOLD:
        alerts.append(("RAM", f"RAM usage high: {ram}%", "warning"))

    if disk >= DISK_THRESHOLD:
        alerts.append(("DISK", f"Disk usage high: {disk}%", "critical"))

    return alerts


def save_alerts(db, alerts, user_id):
    cursor = db.cursor()
    for alert in alerts:
        cursor.execute(
            "INSERT INTO alerts (type, message, level, user_id) VALUES (%s, %s, %s, %s)",
            (alert[0], alert[1], alert[2], user_id)
        )
    db.commit()
    cursor.close()


def get_user_contacts(db, user_id):
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT email, whatsapp FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    cursor.close()
    return user


def send_email_alert(receiver, alert_type, message, level):
    subject = f"[ALERTE {level.upper()}] {alert_type}"
    body = f"""
Alerte détectée sur le serveur :

Type : {alert_type}
Niveau : {level}
Message : {message}
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email envoyé à", receiver)
    except Exception as e:
        print("Erreur email :", e)

def send_whatsapp_alert(to_number, alert_type, message, level):
    client = Client(TWILIO_SID, TWILIO_TOKEN)

    body = f"""
🚨 ALERTE SERVEUR 🚨
Type : {alert_type}
Niveau : {level}
Message : {message}
"""

    try:
        client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,   # OBLIGATOIRE pour le sandbox
            to=f"whatsapp:{to_number}",     # ex: +2126XXXXXXXX
            body=body
        )
        print("WhatsApp envoyé à", to_number)
    except Exception as e:
        print("Erreur WhatsApp :", e)



@app.route("/register", methods=["POST"])
def register():
    data = request.json

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    whatsapp = data.get("whatsapp")

    if not username or not email or not password or not whatsapp:
        return jsonify({"error": "Missing fields"}), 400

    hashed_password = generate_password_hash(password)

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = db.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password, whatsapp) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, whatsapp)
        )
        db.commit()
    except mysql.connector.Error as err:
        cursor.close()
        db.close()
        return jsonify({"error": str(err)}), 500

    cursor.close()
    db.close()

    return jsonify({"status": "user registered successfully"}), 201






@app.route("/login", methods=["POST"])
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = db.cursor(dictionary=True, buffered=True)
    cursor.execute(
        "SELECT id, password FROM users WHERE email = %s",
        (email,)
    )
    user = cursor.fetchone()

    cursor.close()
    db.close()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Login réussi
    return jsonify({
        "status": "login successful",
        "user_id": user["id"]
    }), 200


@app.route("/metrics", methods=["POST"])
def receive_metrics():
    data = request.json

    cpu = data.get("cpu")
    ram = data.get("ram")
    disk = data.get("disk")
    agent_id = data.get("agent_id")

    if not agent_id:
        return jsonify({"error": "Agent not authenticated"}), 401

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = db.cursor(dictionary=True)

    # Récupérer le user lié à l’agent
    cursor.execute(
        "SELECT user_id FROM agents WHERE id = %s",
        (agent_id,)
    )
    agent = cursor.fetchone()

    if not agent:
        cursor.close()
        db.close()
        return jsonify({"error": "Unknown agent"}), 403

    user_id = agent["user_id"]

    # Enregistrer les métriques
    cursor.execute(
        "INSERT INTO metrics (cpu, ram, disk, user_id) VALUES (%s, %s, %s, %s)",
        (cpu, ram, disk, user_id)
    )
    db.commit()

    # Vérifier les seuils
    alerts = check_thresholds(cpu, ram, disk)

    if alerts:
        save_alerts(db, alerts, user_id)


        contacts = get_user_contacts(db, user_id)
        if contacts:
            for alert in alerts:
                send_email_alert(
                    contacts["email"],
                    alert[0],
                    alert[1],
                    alert[2]
                )
                send_whatsapp_alert(
                    contacts["whatsapp"],
                    alert[0],
                    alert[1],
                    alert[2]
                )

    cursor.close()
    db.close()

    return jsonify({"status": "ok"}), 200


@app.route("/metrics/history/<int:user_id>", methods=["GET"])
def metrics_history(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT cpu, ram, disk, created_at
        FROM metrics
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 20
    """, (user_id,))

    data = cursor.fetchall()
    cursor.close()
    db.close()

    return jsonify(data), 200

@app.route("/alerts/history/<int:user_id>", methods=["GET"])
def alerts_history(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT type, message, level, created_at
        FROM alerts
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, (user_id,))

    data = cursor.fetchall()
    cursor.close()
    db.close()

    return jsonify(data), 200


@app.route("/agents/register", methods=["POST"])
def register_agent():
    data = request.json

    token = data.get("token")
    hostname = data.get("hostname")
    ip_address = data.get("ip")
    os_name = data.get("os")

    if not token or not hostname or not ip_address or not os_name:
        return jsonify({"error": "Missing data"}), 400

    db = get_db_connection()
    if db is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = db.cursor(dictionary=True)

    # 1️⃣ Vérifier le token
    cursor.execute(
        "SELECT user_id FROM agent_tokens WHERE token = %s AND expires_at > NOW()",
        (token,)
    )
    row = cursor.fetchone()

    if not row:
        cursor.close()
        db.close()
        return jsonify({"error": "Invalid or expired token"}), 403

    user_id = row["user_id"]

    # 2️⃣ Enregistrer l'agent
    cursor.execute(
        """
        INSERT INTO agents (hostname, ip_address, os, user_id)
        VALUES (%s, %s, %s, %s)
        """,
        (hostname, ip_address, os_name, user_id)
    )
    db.commit()

    agent_id = cursor.lastrowid

    # 3️⃣ Supprimer le token (usage unique)
    cursor.execute(
        "DELETE FROM agent_tokens WHERE token = %s",
        (token,)
    )
    db.commit()

    cursor.close()
    db.close()

    return jsonify({"agent_id": agent_id}), 201


@app.route("/agents/token", methods=["POST"])
def generate_agent_token():
    user_id = request.json.get("user_id")

    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(minutes=10)

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO agent_tokens (token, user_id, expires_at) VALUES (%s, %s, %s)",
        (token, user_id, expires_at)
    )
    db.commit()
    cursor.close()
    db.close()

    return jsonify({"token": token})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

