# Linux Server Monitoring Tool

A full-stack real-time monitoring system for Linux servers, built as a final-year project (team of 3). Tracks CPU, RAM, and disk usage on any registered server and sends automated alerts via email and WhatsApp when usage crosses defined thresholds.

I led the development phase of this project, building the full stack: backend API, monitoring agent, and web dashboard.

## What it does
 
- **Lightweight monitoring agent** a standalone Python script deployed on any Linux server, collecting CPU/RAM/disk metrics at regular intervals and sending them to a central backend
- **Centralized backend API** receives metrics, stores history, evaluates them against configurable thresholds, and triggers alerts
- **Automated alerting** sends real-time notifications via **email (SMTP)** and **WhatsApp (Twilio API)** when thresholds are crossed
- **User accounts** registration and login system; the schema supports linking multiple agents to a user account, though multi-user usage hasn't been tested end-to-end (development so far has used a single account)
- **Web dashboard** view live and historical metrics, and alert history, per user

## Architecture

```
Monitoring Agent (any Linux server)
        |
        |  1. registers with a one-time token
        |  2. sends CPU / RAM / disk metrics every few seconds
        v
Backend API (Flask)
        |
        |  stores metrics, checks against thresholds
        v
   MySQL Database
        |
        |  threshold exceeded?
        v
  ┌─────────────┬──────────────────┐
  |  Email Alert |  WhatsApp Alert  |
  |    (SMTP)    |  (Twilio API)    |
  └─────────────┴──────────────────┘

Web Dashboard (HTML/CSS/JS) <---- talks to Backend API ---> displays live metrics & alert history
```

## Tech stack

- **Backend:** Python, Flask, Flask-CORS
- **Agent:** Python (`psutil` for system metrics, `requests` for HTTP)
- **Database:** MySQL (`mysql-connector-python`)
- **Alerting:** SMTP (email), Twilio API (WhatsApp)
- **Frontend:** HTML, CSS, JavaScript (dashboard)
- **Environment config:** python-dotenv

## Project structure

```
├── backend/
│   ├── app.py                  # Flask API: auth, agent registration, metrics, alerts
│   ├── requirements.txt
│   └── .env.example             # Template for environment variables
├── agent/
│   └── agent.py                  # Runs on monitored servers, sends metrics to backend
├── frontend/
│   └── ...                        # Web dashboard (HTML/CSS/JS)
├── monitoring_db.sql            # Database schema
└── .gitignore
```

## Setup & Usage

### 1. Start the database
Import the schema:
```
mysql -u your_user -p monitoring_db < monitoring_db.sql
```

### 2. Configure environment variables
In `backend/`, copy `.env.example` to `.env` and fill in your real values:
```
TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
DB_HOST=127.0.0.1
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=monitoring_db
```

### 3. Start the backend
```
pip install -r requirements.txt
python3 backend/app.py
```
The API runs on `http://127.0.0.1:5000`.

### 4. Start the frontend
```
cd frontend
python3 -m http.server 5500
```
Then open `http://127.0.0.1:5500/login.html` in your browser and log in. You'll land on the dashboard (empty at first, since no agent is registered yet).

### 5. Generate an agent registration token
Log in through `login.html`, which takes you to the dashboard (`dashboard.html`). Click the **"Générer le token d'installation"** button on the dashboard — it calls the backend and displays a token directly in the UI. Copy it.
 
> Note: after the agent's very first successful registration, the token is no longer actually validated on subsequent agent restarts — the agent will still prompt for one, but any value works at that point.

### 6. Start the monitoring agent
```
python3 agent/agent.py
```
Paste the token when prompted. The agent registers itself and starts sending live CPU/RAM/disk metrics to the dashboard.

### 7. Test alerts manually
Simulate a high-usage reading to trigger an alert without waiting for real thresholds to be crossed:
```
curl -X POST http://127.0.0.1:5000/metrics \
  -H "Content-Type: application/json" \
  -d '{"cpu":92,"ram":88,"disk":97,"agent_id":1}'
```
(replace `agent_id` with your actual registered agent's ID)

### 8. Enable WhatsApp alerts
This project uses Twilio's WhatsApp sandbox for testing. To receive WhatsApp alerts, join the sandbox by sending the join code from your WhatsApp to the Twilio sandbox number, e.g.:
```
join meet-powder
join <sandbox-name>
```

## How agents relate to users
 
Each agent is linked to a user through a foreign key in the database, and in theory, if a user is deleted, their associated agents become invalid and would need to be reset with a new token. This relationship exists in the schema but hasn't been tested with multiple concurrent users development so far has used a single account.

## Team & my role

Built as a team of 3 for our final-year project. I led the development phase designing and coding the backend, the frontend, the monitoring agent, and the alerting logic.

## Author

Omar El Badri Computer Engineering student.