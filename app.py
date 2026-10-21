from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime, timedelta
import json
import uuid

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "demo_data.json"


def seed_data():
    now = datetime.now()
    date = (now + timedelta(days=3)).strftime("%Y-%m-%d")
    return {
        "traveller": {
            "name": "Aarav Sharma",
            "email": "aarav@example.com",
            "home_city": "Bengaluru",
            "preferences": {"max_extra_budget": 4500, "arrival_tolerance_hours": 5, "avoid_overnight": True}
        },
        "bookings": [
            {
                "id": "BK-1042", "traveller": "Aarav Sharma", "type": "flight",
                "provider": "SkyWays", "reference": "SW8K2Q", "from": "Bengaluru", "to": "Mumbai",
                "date": date, "departure": "08:30", "arrival": "10:15", "price": 5200,
                "status": "confirmed", "disruption_id": None
            },
            {
                "id": "BK-1043", "traveller": "Aarav Sharma", "type": "train",
                "provider": "RailConnect", "reference": "RC482910", "from": "Mumbai", "to": "Pune",
                "date": date, "departure": "13:00", "arrival": "16:10", "price": 780,
                "status": "confirmed", "disruption_id": None
            },
            {
                "id": "BK-1044", "traveller": "Aarav Sharma", "type": "hotel",
                "provider": "Harbor Stay", "reference": "HS-9214", "city": "Pune",
                "date": date, "check_in": "18:00", "check_out": "11:00", "price": 3200,
                "status": "confirmed", "disruption_id": None
            },
            {
                "id": "BK-1077", "traveller": "Meera Iyer", "type": "flight",
                "provider": "Deccan Air", "reference": "DA4P9L", "from": "Chennai", "to": "Goa",
                "date": date, "departure": "09:20", "arrival": "10:45", "price": 4600,
                "status": "confirmed", "disruption_id": None
            },
            {
                "id": "BK-1045", "traveller": "Aarav Sharma", "type": "flight",
                "provider": "SkyWays", "reference": "SW3C8N", "from": "Bengaluru", "to": "Chennai",
                "date": date, "departure": "09:00", "arrival": "11:00", "price": 5000,
                "status": "confirmed", "disruption_id": None
            }
        ],
        "disruptions": [],
        "alternatives": [
            {"id":"ALT-F1","type":"flight","provider":"Deccan Air","from":"Bengaluru","to":"Mumbai","date":date,"departure":"09:15","arrival":"11:00","price":5900,"seats":4,"overnight":False,"note":"Direct flight; arrives 45 minutes later than original."},
            {"id":"ALT-F2","type":"flight","provider":"AirSwift","from":"Bengaluru","to":"Mumbai","date":date,"departure":"12:10","arrival":"13:55","price":4700,"seats":6,"overnight":False,"note":"Lower fare; later departure may affect the onward train."},
            {"id":"ALT-F3","type":"flight","provider":"SkyWays","from":"Bengaluru","to":"Mumbai","date":date,"departure":"07:10","arrival":"08:55","price":6400,"seats":2,"overnight":False,"note":"Earlier departure with limited seats."},
            {"id":"ALT-F4","type":"flight","provider":"Deccan Air","from":"Bengaluru","to":"Chennai","date":date,"departure":"09:45","arrival":"11:45","price":5600,"seats":5,"overnight":False,"note":"Direct flight; arrives 45 minutes later than the original booking."},
            {"id":"ALT-F5","type":"flight","provider":"AirSwift","from":"Bengaluru","to":"Chennai","date":date,"departure":"10:30","arrival":"12:25","price":4800,"seats":7,"overnight":False,"note":"Lower-fare direct option with available seats."},
            {"id":"ALT-F6","type":"flight","provider":"SkyWays","from":"Bengaluru","to":"Chennai","date":date,"departure":"08:00","arrival":"10:00","price":6200,"seats":2,"overnight":False,"note":"Earlier arrival with limited seats."},
            {"id":"ALT-T1","type":"train","provider":"InterCity Express","from":"Mumbai","to":"Pune","date":date,"departure":"14:00","arrival":"17:20","price":920,"seats":18,"overnight":False,"note":"Direct train; reaches Pune 70 minutes later."},
            {"id":"ALT-T2","type":"train","provider":"Deccan Rail","from":"Mumbai","to":"Pune","date":date,"departure":"16:30","arrival":"19:40","price":620,"seats":30,"overnight":False,"note":"Budget option; late arrival."},
            {"id":"ALT-T3","type":"train","provider":"Western Link","from":"Mumbai","to":"Pune","date":date,"departure":"11:20","arrival":"14:40","price":1100,"seats":8,"overnight":False,"note":"Earlier service, but requires a tight airport-to-station transfer."},
            {"id":"ALT-H1","type":"hotel","provider":"CityNest Pune","city":"Pune","date":date,"check_in":"18:00","check_out":"11:00","price":3600,"seats":5,"overnight":False,"note":"Near the central station; free cancellation until 24 hours before check-in."},
            {"id":"ALT-H2","type":"hotel","provider":"Maple Rooms","city":"Pune","date":date,"check_in":"20:00","check_out":"10:00","price":2500,"seats":3,"overnight":False,"note":"Budget stay; check-in starts later."},
            {"id":"ALT-H3","type":"hotel","provider":"Grand Orchid","city":"Pune","date":date,"check_in":"15:00","check_out":"11:00","price":4900,"seats":2,"overnight":False,"note":"Premium option with early check-in subject to availability."}
        ],
        "recovery_plans": []
    }


def load_data():
    if not DATA_FILE.exists():
        save_data(seed_data())
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def minutes(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def hours_between(start, end):
    return (minutes(end) - minutes(start)) / 60


def find_booking(data, booking_id):
    return next((b for b in data["bookings"] if b["id"] == booking_id), None)


def affected_booking_ids(data, disruption):
    affected = []
    for b in data["bookings"]:
        if b["status"] not in ("confirmed", "disrupted"):
            continue
        if b["type"] != disruption["type"]:
            continue
        if b["date"] != disruption["date"]:
            continue
        if b["type"] in ("flight", "train"):
            if b.get("from") == disruption.get("from") and b.get("to") == disruption.get("to"):
                affected.append(b["id"])
        elif b["type"] == "hotel" and b.get("city") == disruption.get("city"):
            affected.append(b["id"])
    return affected


def ensure_demo_recovery_options(data, booking):
    """Create clearly simulated options for routes/cities not in the seed catalogue."""
    matching = [
        a for a in data["alternatives"]
        if a.get("type") == booking["type"] and a.get("date") == booking["date"]
        and ((booking["type"] in ("flight", "train") and a.get("from") == booking.get("from") and a.get("to") == booking.get("to"))
             or (booking["type"] == "hotel" and a.get("city") == booking.get("city")))
    ]
    if matching:
        return
    if booking["type"] in ("flight", "train"):
        providers = ["DemoConnect", "SwiftRoute", "ValueWay"]
        price_offsets = [500, 900, -200]
        times = [("09:30", "11:30"), ("12:00", "14:00"), ("08:00", "10:00")]
        for i, provider in enumerate(providers):
            data["alternatives"].append({
                "id": "ALT-GEN-" + uuid.uuid4().hex[:6].upper(), "type": booking["type"],
                "provider": provider, "from": booking["from"], "to": booking["to"],
                "date": booking["date"], "departure": times[i][0], "arrival": times[i][1],
                "price": max(300, int(booking["price"]) + price_offsets[i]), "seats": [8, 5, 3][i],
                "overnight": False, "note": "Simulated alternative generated for this route; not live inventory."
            })
    else:
        for i, (provider, offset, checkin, seats) in enumerate([
            ("DemoStay Central", 400, "15:00", 8),
            ("Value Rooms", -300, "18:00", 5),
            ("Comfort Lodge", 700, "14:00", 3)
        ]):
            data["alternatives"].append({
                "id": "ALT-GEN-" + uuid.uuid4().hex[:6].upper(), "type": "hotel",
                "provider": provider, "city": booking["city"], "date": booking["date"],
                "check_in": checkin, "check_out": "11:00",
                "price": max(500, int(booking["price"]) + offset), "seats": seats,
                "overnight": False, "note": "Simulated hotel alternative for this city; not live inventory."
            })


def score_alternatives(data, booking, constraints):
    """Deterministic decision engine: budget, timing, destination and availability."""
    max_extra = int(constraints.get("max_extra_budget", data["traveller"]["preferences"]["max_extra_budget"]))
    tolerance = float(constraints.get("arrival_tolerance_hours", data["traveller"]["preferences"]["arrival_tolerance_hours"]))
    avoid_overnight = bool(constraints.get("avoid_overnight", True))
    candidates = []
    for alt in data["alternatives"]:
        if alt["type"] != booking["type"] or alt.get("date") != booking["date"] or int(alt.get("seats", 0)) < 1:
            continue
        if booking["type"] in ("flight", "train"):
            if alt.get("from") != booking.get("from") or alt.get("to") != booking.get("to"):
                continue
        elif alt.get("city") != booking.get("city"):
            continue

        extra = int(alt["price"]) - int(booking["price"])
        if extra > max_extra:
            continue
        if avoid_overnight and alt.get("overnight", False):
            continue

        delay = 0
        if booking["type"] in ("flight", "train"):
            delay = max(0, hours_between(booking["arrival"], alt["arrival"]))
            if delay > tolerance:
                continue
        # Lower score is better. Favors low additional cost, minimal delay, and available inventory.
        score = max(extra, 0) * 0.55 + delay * 300 - min(int(alt.get("seats", 1)), 20) * 2
        candidates.append({
            **alt,
            "extra_cost": extra,
            "arrival_delay_hours": round(delay, 2),
            "score": round(score, 2),
            "reason": (
                f"Within your additional budget (₹{max_extra:,}), "
                + (f"arrival delay is {round(delay, 2)} hour(s), " if booking["type"] in ("flight", "train") else "")
                + f"and {alt.get('seats', 0)} slot(s) are available."
            )
        })
    return sorted(candidates, key=lambda item: item["score"])


@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", data=data)


@app.get("/api/state")
def api_state():
    return jsonify(load_data())


@app.post("/api/reset")
def reset():
    save_data(seed_data())
    return jsonify({"ok": True, "message": "Demo data reset."})


@app.post("/api/disruptions")
def create_disruption():
    data = load_data()
    payload = request.get_json(force=True)
    required = ["type", "date", "reason"]
    if any(not payload.get(k) for k in required):
        return jsonify({"error": "Type, date and reason are required."}), 400
    if payload["type"] in ("flight", "train") and (not payload.get("from") or not payload.get("to")):
        return jsonify({"error": "Origin and destination are required."}), 400
    if payload["type"] == "hotel" and not payload.get("city"):
        return jsonify({"error": "City is required for hotel disruptions."}), 400
    disruption = {
        "id": "DSP-" + uuid.uuid4().hex[:6].upper(),
        "type": payload["type"], "date": payload["date"], "reason": payload["reason"],
        "from": payload.get("from", ""), "to": payload.get("to", ""),
        "city": payload.get("city", ""), "created_at": datetime.now().isoformat(timespec="minutes"),
        "status": "detected"
    }
    disruption["affected_booking_ids"] = affected_booking_ids(data, disruption)
    # Flexible demo mode: if the chosen route/city has no seeded booking, create a
    # clearly synthetic booking so the recovery workflow can still be demonstrated.
    if not disruption["affected_booking_ids"]:
        if disruption["type"] in ("flight", "train"):
            booking = {
                "id": "BK-DEMO-" + uuid.uuid4().hex[:6].upper(),
                "traveller": data["traveller"]["name"], "type": disruption["type"],
                "provider": "Demo Original Provider", "reference": "DEMO",
                "from": disruption["from"], "to": disruption["to"], "date": disruption["date"],
                "departure": "09:00", "arrival": "11:00", "price": 5000 if disruption["type"] == "flight" else 900,
                "status": "disrupted", "disruption_id": disruption["id"], "synthetic": True
            }
        else:
            booking = {
                "id": "BK-DEMO-" + uuid.uuid4().hex[:6].upper(),
                "traveller": data["traveller"]["name"], "type": "hotel",
                "provider": "Demo Original Hotel", "reference": "DEMO",
                "city": disruption["city"], "date": disruption["date"],
                "check_in": "18:00", "check_out": "11:00", "price": 3200,
                "status": "disrupted", "disruption_id": disruption["id"], "synthetic": True
            }
        data["bookings"].append(booking)
        disruption["affected_booking_ids"] = [booking["id"]]
    for booking_id in disruption["affected_booking_ids"]:
        booking = find_booking(data, booking_id)
        if booking:
            booking["status"] = "disrupted"
            booking["disruption_id"] = disruption["id"]
    data["disruptions"].insert(0, disruption)
    save_data(data)
    return jsonify({"ok": True, "disruption": disruption, "affected_count": len(disruption["affected_booking_ids"])})


@app.post("/api/recover/<disruption_id>")
def recover(disruption_id):
    data = load_data()
    disruption = next((d for d in data["disruptions"] if d["id"] == disruption_id), None)
    if not disruption:
        return jsonify({"error": "Disruption not found."}), 404
    payload = request.get_json(silent=True) or {}
    constraints = {
        "max_extra_budget": payload.get("max_extra_budget", data["traveller"]["preferences"]["max_extra_budget"]),
        "arrival_tolerance_hours": payload.get("arrival_tolerance_hours", data["traveller"]["preferences"]["arrival_tolerance_hours"]),
        "avoid_overnight": payload.get("avoid_overnight", data["traveller"]["preferences"]["avoid_overnight"])
    }
    plan = {
        "id": "REC-" + uuid.uuid4().hex[:6].upper(),
        "disruption_id": disruption_id,
        "created_at": datetime.now().isoformat(timespec="minutes"),
        "constraints": constraints,
        "items": [],
        "status": "proposed",
        "summary": ""
    }
    affected = [find_booking(data, bid) for bid in disruption["affected_booking_ids"]]
    affected = [b for b in affected if b]
    total_extra = 0
    for booking in affected:
        ensure_demo_recovery_options(data, booking)
        options = score_alternatives(data, booking, constraints)
        chosen = options[0] if options else None
        item = {
            "booking_id": booking["id"],
            "booking_type": booking["type"],
            "original": booking,
            "alternatives": options[:3],
            "recommended": chosen,
            "action_required": (
                f"Review and confirm {chosen['provider']} option" if chosen
                else "Contact the provider; no matching option satisfies the current constraints."
            )
        }
        if chosen:
            total_extra += chosen["extra_cost"]
        plan["items"].append(item)
    plan["total_extra_cost"] = total_extra
    recommended_count = sum(1 for item in plan["items"] if item["recommended"])
    plan["summary"] = (
        f"{recommended_count} of {len(plan['items'])} affected booking(s) have a recommended alternative. "
        f"Estimated net additional cost: ₹{total_extra:,}. This is a proposal; no booking or payment is made."
    )
    data["recovery_plans"].insert(0, plan)
    disruption["status"] = "recovery_proposed"
    save_data(data)
    return jsonify({"ok": True, "plan": plan})


@app.post("/api/confirm/<plan_id>")
def confirm_plan(plan_id):
    data = load_data()
    plan = next((p for p in data["recovery_plans"] if p["id"] == plan_id), None)
    if not plan:
        return jsonify({"error": "Recovery plan not found."}), 404
    plan["status"] = "accepted_demo"
    for item in plan["items"]:
        if item["recommended"]:
            booking = find_booking(data, item["booking_id"])
            if booking:
                booking["status"] = "recovery_accepted_demo"
    save_data(data)
    return jsonify({"ok": True, "message": "Plan marked accepted in demo mode. No external booking was made."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
