"""CityServe - Smart City Service Application (SEPM micro project prototype).
Citizens report civic issues; the system prioritises them, routes them to a
department and tracks them through an Agile-style status workflow."""
import sqlite3, os
from datetime import datetime, timezone
from flask import Flask, jsonify, request, send_from_directory, g

CATEGORIES = {  # category -> (department, base urgency 1-5, SLA hours)
    "water_leak":   ("Water Dept", 4, 24),
    "power_outage": ("Electricity Dept", 5, 12),
    "pothole":      ("Roads Dept", 3, 72),
    "streetlight":  ("Electricity Dept", 2, 96),
    "waste":        ("Sanitation Dept", 3, 48),
    "traffic":      ("Traffic Police", 4, 24),
}
STATUSES = ["Reported", "Assigned", "In Progress", "Resolved"]
SEVERITY = {"low": 0, "medium": 1, "high": 2}


def compute_priority(category, severity, affected):
    """Priority score 1-10 = base urgency + severity bonus + reach bonus."""
    base = CATEGORIES[category][1]
    reach = 2 if affected >= 100 else 1 if affected >= 10 else 0
    return min(10, base + SEVERITY[severity] * 1 + reach + (1 if severity == "high" else 0))


def label(score):
    return "Critical" if score >= 8 else "High" if score >= 6 else "Medium" if score >= 4 else "Low"


def create_app(db_path=None):
    app = Flask(__name__, static_folder="static")
    app.config["DB"] = db_path or os.path.join(os.path.dirname(__file__), "cityserve.db")

    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DB"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close(_):
        d = g.pop("db", None)
        if d:
            d.close()

    with sqlite3.connect(app.config["DB"]) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS issues(
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, category TEXT NOT NULL,
            description TEXT, location TEXT NOT NULL, severity TEXT NOT NULL, affected INTEGER NOT NULL,
            priority INTEGER NOT NULL, department TEXT NOT NULL, status TEXT NOT NULL,
            created TEXT NOT NULL, updated TEXT NOT NULL)""")

    def row(r):
        d = dict(r)
        d["priority_label"] = label(d["priority"])
        d["sla_hours"] = CATEGORIES[d["category"]][2]
        return d

    @app.get("/")
    def index():
        return send_from_directory("static", "index.html")

    @app.get("/api/categories")
    def cats():
        return jsonify({k: {"department": v[0], "sla_hours": v[2]} for k, v in CATEGORIES.items()})

    @app.post("/api/issues")
    def create():
        j = request.get_json(silent=True) or {}
        errs = []
        if not str(j.get("title", "")).strip():
            errs.append("title is required")
        if not str(j.get("location", "")).strip():
            errs.append("location is required")
        if j.get("category") not in CATEGORIES:
            errs.append("invalid category")
        if j.get("severity") not in SEVERITY:
            errs.append("invalid severity")
        try:
            affected = int(j.get("affected", 1))
            if affected < 1:
                raise ValueError
        except (TypeError, ValueError):
            errs.append("affected must be a positive integer")
        if errs:
            return jsonify({"errors": errs}), 400
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        p = compute_priority(j["category"], j["severity"], affected)
        cur = db().execute(
            "INSERT INTO issues(title,category,description,location,severity,affected,priority,department,status,created,updated)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (j["title"].strip(), j["category"], j.get("description", ""), j["location"].strip(), j["severity"],
             affected, p, CATEGORIES[j["category"]][0], "Reported", now, now))
        db().commit()
        r = db().execute("SELECT * FROM issues WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(row(r)), 201

    @app.get("/api/issues")
    def listing():
        q, args = "SELECT * FROM issues WHERE 1=1", []
        for f in ("status", "category", "department"):
            if request.args.get(f):
                q += f" AND {f}=?"
                args.append(request.args[f])
        q += " ORDER BY priority DESC, created ASC"
        return jsonify([row(r) for r in db().execute(q, args)])

    @app.patch("/api/issues/<int:iid>/status")
    def advance(iid):
        r = db().execute("SELECT * FROM issues WHERE id=?", (iid,)).fetchone()
        if not r:
            return jsonify({"error": "not found"}), 404
        new = (request.get_json(silent=True) or {}).get("status")
        if new not in STATUSES:
            return jsonify({"error": "invalid status"}), 400
        if STATUSES.index(new) != STATUSES.index(r["status"]) + 1:
            return jsonify({"error": f"cannot move from {r['status']} to {new}"}), 409
        db().execute("UPDATE issues SET status=?, updated=? WHERE id=?",
                     (new, datetime.now(timezone.utc).isoformat(timespec="seconds"), iid))
        db().commit()
        return jsonify(row(db().execute("SELECT * FROM issues WHERE id=?", (iid,)).fetchone()))

    @app.get("/api/stats")
    def stats():
        rows = [row(r) for r in db().execute("SELECT * FROM issues")]
        by = lambda k: {x: sum(1 for r in rows if r[k] == x) for x in sorted({r[k] for r in rows})}
        open_ = [r for r in rows if r["status"] != "Resolved"]
        return jsonify({"total": len(rows), "open": len(open_), "resolved": len(rows) - len(open_),
                        "critical_open": sum(1 for r in open_ if r["priority_label"] == "Critical"),
                        "by_status": by("status"), "by_category": by("category"), "by_department": by("department")})

    return app


if __name__ == "__main__":
    create_app().run(debug=False, port=5000)
