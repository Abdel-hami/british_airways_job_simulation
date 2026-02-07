
import os
import json
import requests
import gradio as gr

DEFAULT_API = os.getenv("API_BASE_URL", "http://16.16.162.70:8000").rstrip("/")
DEFAULT_ENDPOINT = os.getenv("PREDICT_ENDPOINT", "/predict/")

SESSION = requests.Session()

def url_join(base: str, endpoint: str) -> str:
    base = (base or "").strip().rstrip("/")
    endpoint = (endpoint or "").strip()
    if not base.startswith(("http://", "https://")):
        base = "http://" + base
    return base + "/" + endpoint.lstrip("/")

def to_float_maybe(x):
    if x is None:
        return None
    if isinstance(x, bool):
        return float(int(x))
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip().replace("%", "").replace(",", ".")
        s = "".join(ch for ch in s if (ch.isdigit() or ch in ".-"))
        if s in ("", ".", "-", "-."):
            return None
        try:
            return float(s)
        except ValueError:
            return None
    try:
        return float(x)
    except Exception:
        return None

def format_probability(prob_raw) -> str:
    v = to_float_maybe(prob_raw)
    if v is None:
        return "N/A"
    if 0 <= v <= 1:
        return f"{v * 100:.2f}%"
    if 1 < v <= 100:
        return f"{v:.2f}%"
    return "N/A"

def to_int(b):
    return 1 if b else 0

def predict(
    api_base, endpoint,
    purchase_lead, length_of_stay, flight_hour, flight_day,
    route, booking_origin,
    wants_extra_baggage, wants_preferred_seat, wants_in_flight_meals,
    flight_duration, num_passengers, sales_channel, trip_type
):
    api_url = url_join(api_base, endpoint)

    payload = {
        "purchase_lead": int(purchase_lead),
        "length_of_stay": int(length_of_stay),
        "flight_hour": int(flight_hour),
        "flight_day": int(flight_day),
        "route": (route or "").strip(),
        "booking_origin": (booking_origin or "").strip(),
        "wants_extra_baggage": int(wants_extra_baggage),
        "wants_preferred_seat": int(wants_preferred_seat),
        "wants_in_flight_meals": int(wants_in_flight_meals),
        "flight_duration": float(flight_duration),
        "num_passengers": int(num_passengers),
        "sales_channel": sales_channel,
        "trip_type": trip_type,
    }

    try:
        r = SESSION.post(api_url, json=payload, timeout=(5, 30))
        r.raise_for_status()

        # Single source of truth
        response_data = r.json()

        pred = response_data.get("booking_prediction")
        reco = response_data.get("recommendation", "")
        prob_raw = response_data.get("booking_probability")

        prob_label = format_probability(prob_raw)
        pred_label = "BOOK ✅" if pred == 1 else "NO BOOK ❌"

        debug_line = f"Raw probability: {repr(prob_raw)} (type={type(prob_raw).__name__})"

        result_md = f"""
### Result
- **Prediction:** {pred_label}
- **Recommendation:** {reco}

""".strip()

        return result_md, json.dumps(response_data, indent=2)

    except requests.exceptions.RequestException as e:
        msg = f"### API request failed\n```text\n{type(e).__name__}: {e}\n```\n\nAPI URL:\n```text\n{api_url}\n```"
        return msg, json.dumps(payload, indent=2)

with gr.Blocks(title="Booking Predictor") as demo:
    gr.Markdown("# ✈️ Booking Predictor")

    with gr.Accordion("API settings", open=False):
        api_base = gr.Textbox(label="API Base URL", value=DEFAULT_API)
        endpoint = gr.Textbox(label="Endpoint", value=DEFAULT_ENDPOINT)

    with gr.Row():
        purchase_lead = gr.Number(label="Purchase lead (days)", value=80, precision=0)
        length_of_stay = gr.Number(label="Stay (days)", value=1, precision=0)
        num_passengers = gr.Number(label="Passengers", value=1, precision=0)

    with gr.Row():
        flight_hour = gr.Slider(0, 23, value=23, step=1, label="Flight hour")
        flight_day = gr.Slider(1, 7, value=1, step=1, label="Flight day")
        flight_duration = gr.Number(label="Duration (hours)", value=1.0)

    with gr.Row():
        wants_extra_baggage = gr.Checkbox(label="Extra baggage", value=True)
        wants_preferred_seat = gr.Checkbox(label="Preferred seat", value=True)
        wants_in_flight_meals = gr.Checkbox(label="In-flight meals", value=True)

    with gr.Row():
        route = gr.Textbox(label="Route", value="AKLKUL")
        booking_origin = gr.Textbox(label="Origin", value="Malaysia")

    with gr.Row():
        sales_channel = gr.Dropdown(["Internet", "Mobile", "Travel Agent", "Other"], value="Internet", label="Sales channel")
        trip_type = gr.Dropdown(["RoundTrip", "OneWay", "CircleTrip"], value="RoundTrip", label="Trip type")

    btn = gr.Button("Predict", variant="primary")
    out_md = gr.Markdown()
    out_json = gr.Code(label="Raw response / payload on error", language="json")

    btn.click(
        fn=lambda api, ep, pl, los, fh, fd, rt, bo, beb, ps, im, dur, pax, sc, tt:
            predict(api, ep, pl, los, fh, fd, rt, bo,
                    to_int(beb), to_int(ps), to_int(im),
                    dur, pax, sc, tt),
        inputs=[
            api_base, endpoint,
            purchase_lead, length_of_stay, flight_hour, flight_day,
            route, booking_origin,
            wants_extra_baggage, wants_preferred_seat, wants_in_flight_meals,
            flight_duration, num_passengers, sales_channel, trip_type
        ],
        outputs=[out_md, out_json]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
