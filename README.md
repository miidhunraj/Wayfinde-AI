# Wayfinder AI — Travel Disruption Recovery

Hackathon prototype for **PS 4.1: AI Agent for Travel Disruption Recovery**.

Wayfinder simulates travel disruptions, matches them to reservations, ranks alternatives against traveller constraints, and creates a recovery itinerary with actions for the traveller.

## Features

- Dashboard for flight, train, and hotel bookings.
- Disruption simulator for delays, cancellations, overbooking, weather, and operational issues.
- Booking matching by travel type, route/city, and date.
- Constraint-based alternative ranking using additional budget, arrival-delay tolerance, inventory, and overnight preferences.
- Recovery proposal with a recommended option, up to two alternatives, rationale, extra cost, and next action.
- Demo acceptance state and copyable itinerary.
- Persistent demo state stored in `data/demo_data.json`.
- Reset button to restore the sample journey.

## Technology

- Python 3.10+
- Flask
- HTML, CSS, vanilla JavaScript
- JSON file persistence (no database installation required)

## Run locally

### Windows (PowerShell)

```powershell
cd travel_recovery_agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
pip install -r requirements.txt
python app.py
```

### macOS / Linux

```bash
cd travel_recovery_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## Suggested demo script (2–3 minutes)

1. Show the upcoming journey and four sample bookings.
2. In **Disruption simulator**, choose `Flight`, select Bengaluru → Chennai (or Bengaluru → Mumbai), and use the displayed travel date.
3. Click **Detect affected bookings**. The app matches the disruption to relevant reservations and marks them disrupted.
4. Click **Build recovery plan** on the new event.
5. Explain that the decision engine filters by route, date, available inventory, extra budget, arrival tolerance, and overnight preference, then ranks eligible options.
6. Review the recommended alternative, rationale, extra cost, and fallback options.
7. Copy the itinerary or click **Accept proposal (demo)** to show the proposed state change.
8. Use **Reset demo data** before another demo run.

For a train scenario, choose Mumbai → Pune. For a hotel scenario, choose Pune. The demo includes a Bengaluru → Chennai booking and sample replacement flights.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/state` | Read current bookings, disruptions, alternatives, and plans |
| `POST` | `/api/disruptions` | Create a simulated disruption and identify affected bookings |
| `POST` | `/api/recover/<disruption_id>` | Generate a constraint-based recovery proposal |
| `POST` | `/api/confirm/<plan_id>` | Mark the plan accepted in demo mode |
| `POST` | `/api/reset` | Restore sample data |

### Example: create a flight disruption

```json
{
  "type": "flight",
  "from": "Bengaluru",
  "to": "Mumbai",
  "date": "YYYY-MM-DD",
  "reason": "Cancelled"
}
```

Replace `YYYY-MM-DD` with the date shown in the dashboard.

## Important prototype limitations

- **Disruptions are simulated**, not detected from live airline, railway, hotel, or flight-tracking feeds.
- Alternatives are sample records, not live availability or live prices.
- The “AI decision engine” is an explainable, deterministic ranking engine. It is not connected to an LLM or external agent framework.
- Accepting a plan only updates the local demo state. It does not cancel, rebook, charge, or contact a provider.
- Data is stored in a local JSON file and is intended for a single-user demo, not concurrent production use.
- Do not enter real passenger or payment data.

## Project structure

```text
travel_recovery_agent/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── demo_data.json       # created automatically on first run
├── static/
│   ├── app.js
│   └── style.css
└── templates/
    └── index.html
```

## Production extensions

For a production-grade system, add authenticated user accounts, a relational database, real provider integrations, event/webhook ingestion, inventory verification, idempotent booking workflows, audit logs, and human approval before booking changes. Keep price, cancellation, and availability claims grounded in provider responses.
