"""Main Flask application for the SQDIP system."""

from __future__ import annotations

from datetime import date

from flask import Flask, jsonify, render_template
from waitress import serve

from database import get_db_connection
from sqdip_charts import sqdip_charts_bp


# Flask must be created before registering Blueprints.
app = Flask(__name__)

# Register the generic SQDIP chart API routes.
app.register_blueprint(sqdip_charts_bp)


@app.route("/safety")
def safety():
    return render_template("safety.html")


@app.route("/quality")
def quality():
    return render_template("quality.html")


@app.route("/deliverables")
def deliverables():
    return render_template("deliverables.html")


@app.route("/inventory")
def inventory():
    return render_template("inventory.html")


@app.route("/productivity")
def productivity():
    return render_template("productivity.html")


@app.route("/api/status")
def status():
    return jsonify({
        "status": "running",
        "server": "Waitress",
        "database": "Pcubed",
        "date": date.today().isoformat()
    })


if __name__ == "__main__":
    print(
        "Starting SQDIP application on "
        "http://0.0.0.0:5002"
    )

    serve(
        app,
        host="0.0.0.0",
        port=5002,
        threads=8
    )