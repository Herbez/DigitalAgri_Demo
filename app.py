from __future__ import annotations

import calendar
import json
import os
from datetime import datetime
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, RecommendationHistory, db


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "digital_agri.db"
DATASET_PATH = BASE_DIR / "ahs_dataset_nisr.csv"
MODEL_PATH = BASE_DIR / "models" / "crop_recommendation_pipeline.joblib"

FEATURE_COLUMNS = [
    "soil_ph",
    "nitrogen",
    "phosphorus",
    "potassium",
    "annual_rainfall_mm",
    "avg_temperature_C",
    "avg_humidity_pct",
    "altitude_m",
]

FEATURE_META = {
    "soil_ph": {"label": "Soil pH", "step": "0.01", "min": "4.0", "max": "8.5"},
    "nitrogen": {"label": "Nitrogen", "step": "0.001", "min": "0.02", "max": "1.2"},
    "phosphorus": {"label": "Phosphorus", "step": "0.001", "min": "0.005", "max": "0.5"},
    "potassium": {"label": "Potassium", "step": "0.001", "min": "0.02", "max": "1.5"},
    "annual_rainfall_mm": {
        "label": "Annual Rainfall (mm)",
        "step": "0.1",
        "min": "300",
        "max": "1800",
    },
    "avg_temperature_C": {
        "label": "Avg Temperature (C)",
        "step": "0.1",
        "min": "10",
        "max": "35",
    },
    "avg_humidity_pct": {
        "label": "Avg Humidity (%)",
        "step": "0.1",
        "min": "35",
        "max": "100",
    },
    "altitude_m": {"label": "Altitude (m)", "step": "1", "min": "900", "max": "2500"},
}

CROP_META = {
    "beans": {"label": "Beans", "color": "#f59e0b"},
    "cassava": {"label": "Cassava", "color": "#22884f"},
    "irish_potato": {"label": "Irish Potato", "color": "#3b82f6"},
    "maize": {"label": "Maize", "color": "#8b5cf6"},
    "rice": {"label": "Rice", "color": "#14b8a6"},
}

ALERT_STYLES = {
    "success": {"bg": "#ecfdf5", "fg": "#059669"},
    "warning": {"bg": "#fffbeb", "fg": "#d97706"},
    "info": {"bg": "#eff6ff", "fg": "#2563eb"},
}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "digital-agri-dev-secret")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def init_db() -> None:
    with app.app_context():
        db.create_all()




def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_user() is None:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("signin"))
        return view(*args, **kwargs)

    return wrapped_view


@lru_cache(maxsize=1)
def load_model():
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def load_district_profiles() -> dict[str, dict[str, Any]]:
    df = pd.read_csv(DATASET_PATH)
    grouped = (
        df.groupby(["district_real", "province"], as_index=False)[FEATURE_COLUMNS + ["farm_size_ha"]]
        .mean(numeric_only=True)
        .sort_values("district_real")
    )

    profiles: dict[str, dict[str, Any]] = {}
    for record in grouped.to_dict("records"):
        district = record["district_real"]
        profiles[district] = {
            "district": district,
            "province": record["province"],
            "farm_size_ha": round(float(record["farm_size_ha"]), 2),
            **{
                feature: round(float(record[feature]), 3 if feature in {"nitrogen", "phosphorus", "potassium"} else 2)
                for feature in FEATURE_COLUMNS
            },
        }
    return profiles


def district_choices() -> list[str]:
    return sorted(load_district_profiles().keys())


def province_for_district(district: str) -> str:
    profile = load_district_profiles().get(district, {})
    return str(profile.get("province", ""))


def humanize_crop(crop_key: str) -> str:
    return CROP_META.get(crop_key, {"label": crop_key.replace("_", " ").title()})["label"]


def current_user() -> dict[str, Any] | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = User.query.get(user_id)
    if user is None:
        return None
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "district": user.district,
        "province": user.province,
        "farm_size_ha": user.farm_size_ha,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def predict_crop_scores(features: dict[str, float]) -> tuple[str, dict[str, float]]:
    model = load_model()
    input_frame = pd.DataFrame([[features[column] for column in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
    predicted_crop = str(model.predict(input_frame)[0])

    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(input_frame)[0]
        scores = {
            str(label): round(float(probability) * 100, 1)
            for label, probability in zip(model.classes_, probabilities)
        }
    else:
        scores = {predicted_crop: 100.0}

    return predicted_crop, scores


def score_cards(scores: dict[str, float]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for crop_key, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
        if score >= 75:
            tag = "high"
        elif score >= 55:
            tag = "medium"
        else:
            tag = "low"

        cards.append(
            {
                "key": crop_key,
                "label": humanize_crop(crop_key),
                "score": round(score, 1),
                "tag": tag,
                "color": CROP_META.get(crop_key, {}).get("color", "#22884f"),
            }
        )
    return cards


def monthly_labels(count: int) -> list[str]:
    now = datetime.now()
    labels: list[str] = []
    for offset in range(count - 1, -1, -1):
        month = ((now.month - offset - 1) % 12) + 1
        labels.append(calendar.month_abbr[month])
    return labels


def build_environment_series(features: dict[str, float]) -> dict[str, Any]:
    labels = monthly_labels(6)
    multipliers = [0.88, 0.94, 0.98, 1.02, 1.06, 1.1]
    rainfall_base = features["annual_rainfall_mm"] / 12
    rainfall = [round(rainfall_base * factor, 1) for factor in multipliers]
    temperature = [round(features["avg_temperature_C"] + shift, 1) for shift in (-1.2, -0.8, -0.4, 0.0, 0.4, 0.8)]
    humidity = [round(features["avg_humidity_pct"] + shift, 1) for shift in (-4.0, -2.5, -1.0, 0.0, 1.5, 3.0)]
    return {
        "labels": labels,
        "rainfall": rainfall,
        "temperature": temperature,
        "humidity": humidity,
    }


def build_history_chart(history_rows: list[dict[str, Any]], fallback_scores: dict[str, float]) -> dict[str, Any]:
    if history_rows:
        rows = list(reversed(history_rows[:6]))
        labels = [datetime.fromisoformat(row["created_at"]).strftime("%b %d") for row in rows]
        crops = list(sorted(fallback_scores, key=fallback_scores.get, reverse=True))
        datasets = []
        for crop_key in crops:
            data = []
            for row in rows:
                score_payload = json.loads(row["score_payload"])
                data.append(round(float(score_payload.get(crop_key, 0.0)), 1))
            datasets.append(
                {
                    "label": humanize_crop(crop_key),
                    "data": data,
                    "color": CROP_META.get(crop_key, {}).get("color", "#22884f"),
                }
            )
        return {"labels": labels, "datasets": datasets}

    top_crops = list(sorted(fallback_scores, key=fallback_scores.get, reverse=True))
    return {
        "labels": ["Preview"],
        "datasets": [
            {
                "label": humanize_crop(crop_key),
                "data": [round(float(score), 1)],
                "color": CROP_META.get(crop_key, {}).get("color", "#22884f"),
            }
            for crop_key, score in sorted(fallback_scores.items(), key=lambda item: item[1], reverse=True)
            if crop_key in top_crops
        ],
    }


def build_alerts(features: dict[str, float], top_crop: str, top_score: float) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    soil_ph = features["soil_ph"]
    if soil_ph < 5.5:
        alerts.append(
            {
                "variant": "warning",
                "title": "Soil pH is on the acidic side",
                "description": f"Current pH is {soil_ph:.2f}. Consider liming before planting for better nutrient uptake.",
            }
        )
    else:
        alerts.append(
            {
                "variant": "success",
                "title": "Soil pH is within a workable range",
                "description": f"Current pH is {soil_ph:.2f}, which is suitable for the current crop selection run.",
            }
        )

    rainfall = features["annual_rainfall_mm"]
    if rainfall < 800:
        alerts.append(
            {
                "variant": "warning",
                "title": "Lower rainfall profile detected",
                "description": "Plan mulch or irrigation support because annual rainfall is below 800 mm.",
            }
        )
    else:
        alerts.append(
            {
                "variant": "info",
                "title": "Rainfall profile supports field planning",
                "description": f"Estimated rainfall is {rainfall:.1f} mm, enough for a strong advisory baseline.",
            }
        )

    alerts.append(
        {
            "variant": "info",
            "title": f"Top recommendation: {humanize_crop(top_crop)}",
            "description": f"The model assigned a confidence score of {top_score:.1f}% for this crop.",
        }
    )

    return alerts[:3]


def feature_fields(values: dict[str, float]) -> list[dict[str, Any]]:
    fields = []
    for name in FEATURE_COLUMNS:
        fields.append(
            {
                "name": name,
                "label": FEATURE_META[name]["label"],
                "step": FEATURE_META[name]["step"],
                "min": FEATURE_META[name]["min"],
                "max": FEATURE_META[name]["max"],
                "value": values[name],
            }
        )
    return fields


def parse_feature_values(form_data) -> dict[str, float]:
    parsed: dict[str, float] = {}
    for feature in FEATURE_COLUMNS:
        raw_value = form_data.get(feature, "").strip()
        if not raw_value:
            raise ValueError(f"{FEATURE_META[feature]['label']} is required.")
        try:
            parsed[feature] = float(raw_value)
        except ValueError as exc:
            raise ValueError(f"{FEATURE_META[feature]['label']} must be numeric.") from exc
    return parsed


def latest_recommendation_for_user(user_id: int) -> dict[str, Any] | None:
    record = (
        RecommendationHistory.query
        .filter_by(user_id=user_id)
        .order_by(RecommendationHistory.created_at.desc(), RecommendationHistory.id.desc())
        .first()
    )
    if record is None:
        return None
    return {
        "id": record.id,
        "user_id": record.user_id,
        "district": record.district,
        "province": record.province,
        "soil_ph": record.soil_ph,
        "nitrogen": record.nitrogen,
        "phosphorus": record.phosphorus,
        "potassium": record.potassium,
        "annual_rainfall_mm": record.annual_rainfall_mm,
        "avg_temperature_C": record.avg_temperature_C,
        "avg_humidity_pct": record.avg_humidity_pct,
        "altitude_m": record.altitude_m,
        "predicted_crop": record.predicted_crop,
        "confidence": record.confidence,
        "score_payload": json.loads(record.score_payload),
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def recommendation_history_for_user(user_id: int, limit: int = 6) -> list[dict[str, Any]]:
    records = (
        RecommendationHistory.query
        .filter_by(user_id=user_id)
        .order_by(RecommendationHistory.created_at.desc(), RecommendationHistory.id.desc())
        .limit(limit)
        .all()
    )
    history = []
    for record in records:
        history.append({
            "id": record.id,
            "district": record.district,
            "province": record.province,
            "predicted_crop": record.predicted_crop,
            "confidence": record.confidence,
            "score_payload": record.score_payload,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "predicted_crop_label": humanize_crop(record.predicted_crop),
            "created_label": datetime.fromisoformat(record.created_at.isoformat()).strftime("%d %b %Y %H:%M") if record.created_at else "",
        })
    return history


def build_dashboard_payload(user: dict[str, Any]) -> dict[str, Any]:
    profiles = load_district_profiles()
    profile = profiles[user["district"]]
    latest = latest_recommendation_for_user(int(user["id"]))
    history = recommendation_history_for_user(int(user["id"]))

    if latest:
        current_inputs = {feature: float(latest[feature]) for feature in FEATURE_COLUMNS}
        current_scores = latest["score_payload"]
        predicted_crop = latest["predicted_crop"]
        confidence = float(latest["confidence"])
        source_label = f"Saved from {datetime.fromisoformat(latest['created_at']).strftime('%d %b %Y %H:%M')}"
    else:
        current_inputs = {feature: float(profile[feature]) for feature in FEATURE_COLUMNS}
        predicted_crop, current_scores = predict_crop_scores(current_inputs)
        confidence = float(current_scores[predicted_crop])
        source_label = "Preview generated from district averages"

    cards = score_cards(current_scores)
    best_card = cards[0]
    alerts = build_alerts(current_inputs, predicted_crop, confidence)

    return {
        "current_inputs": current_inputs,
        "current_scores": current_scores,
        "score_cards": cards,
        "best_crop_label": best_card["label"],
        "best_crop_score": best_card["score"],
        "predicted_crop_label": humanize_crop(predicted_crop),
        "confidence": round(confidence, 1),
        "source_label": source_label,
        "environment_series": build_environment_series(current_inputs),
        "history_chart": build_history_chart(history, current_scores),
        "alerts": alerts,
        "history_rows": history,
        "total_recommendations": len(history),
        "monthly_rainfall": round(current_inputs["annual_rainfall_mm"] / 12, 1),
        "feature_fields": feature_fields(current_inputs),
        "district_profile": profile,
    }


@app.route("/")
def index():
    if current_user() is not None:
        return redirect(url_for("dashboard"))
    return redirect(url_for("signin"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        district = request.form.get("district", "").strip()
        farm_size_raw = request.form.get("farm_size_ha", "").strip()

        if not full_name or not email or not password or not district:
            flash("Please fill in all required signup fields.", "warning")
            return render_template("auth.html", mode="signup", districts=district_choices())

        if district not in load_district_profiles():
            flash("Please select a valid district.", "warning")
            return render_template("auth.html", mode="signup", districts=district_choices())

        farm_size = float(farm_size_raw) if farm_size_raw else None
        password_hash = generate_password_hash(password)

        try:
            user = User(
                full_name=full_name,
                email=email,
                password_hash=password_hash,
                district=district,
                province=province_for_district(district),
                farm_size_ha=farm_size,
            )
            db.session.add(user)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("An account with that email already exists.", "warning")
            return render_template("auth.html", mode="signup", districts=district_choices())

        session.clear()
        session["user_id"] = user.id
        flash("Account created successfully. Welcome to DigitalAgri!", "success")
        return redirect(url_for("dashboard"))

    return render_template("auth.html", mode="signup", districts=district_choices())


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "warning")
            return render_template("auth.html", mode="signin", districts=district_choices())

        session.clear()
        session["user_id"] = user.id
        flash("Signed in successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("auth.html", mode="signin", districts=district_choices())


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("signin"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if user is None:
        return redirect(url_for("signin"))

    payload = build_dashboard_payload(user)
    initials = "".join(part[0] for part in user["full_name"].split()[:2]).upper()

    return render_template(
        "user_dashboard.html",
        user=user,
        initials=initials,
        districts=district_choices(),
        district_profiles=load_district_profiles(),
        **payload,
    )


@app.route("/planting-calendar")
@login_required
def planting_calendar():
    user = current_user()
    if user is None:
        return redirect(url_for("signin"))

    initials = "".join(part[0] for part in user["full_name"].split()[:2]).upper()

    return render_template(
        "planting_calendar.html",
        user=user,
        initials=initials,
        districts=district_choices(),
        district_profiles=load_district_profiles(),
    )


@app.post("/recommend")
@login_required
def recommend():
    user = current_user()
    if user is None:
        return redirect(url_for("signin"))

    district = request.form.get("district", "").strip()
    farm_size_raw = request.form.get("farm_size_ha", "").strip()

    if district not in load_district_profiles():
        flash("Please select a valid district before requesting a recommendation.", "warning")
        return redirect(url_for("dashboard"))

    try:
        inputs = parse_feature_values(request.form)
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("dashboard"))

    predicted_crop, scores = predict_crop_scores(inputs)
    confidence = float(scores[predicted_crop])
    farm_size = float(farm_size_raw) if farm_size_raw else user.get("farm_size_ha")

    user_obj = User.query.get(user["id"])
    user_obj.district = district
    user_obj.province = province_for_district(district)
    user_obj.farm_size_ha = farm_size

    recommendation = RecommendationHistory(
        user_id=user["id"],
        district=district,
        province=province_for_district(district),
        soil_ph=inputs["soil_ph"],
        nitrogen=inputs["nitrogen"],
        phosphorus=inputs["phosphorus"],
        potassium=inputs["potassium"],
        annual_rainfall_mm=inputs["annual_rainfall_mm"],
        avg_temperature_C=inputs["avg_temperature_C"],
        avg_humidity_pct=inputs["avg_humidity_pct"],
        altitude_m=inputs["altitude_m"],
        predicted_crop=predicted_crop,
        confidence=confidence,
        score_payload=json.dumps(scores),
    )
    db.session.add(recommendation)
    db.session.commit()

    flash(
        f"Recommendation saved: {humanize_crop(predicted_crop)} with {confidence:.1f}% confidence.",
        "success",
    )
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)
