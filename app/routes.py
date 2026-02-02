from fastapi import APIRouter, HTTPException
import pandas as pd

from app.schemas import BookingInput, PredictionOutput
from app.services import predict_booking


router = APIRouter()

@router.get('/')
def check_health():
    return {"health_check":"OK"}

@router.post('/predict',response_model=PredictionOutput)
def predict( booking: BookingInput):
    try:
        
        input_df = pd.DataFrame([booking.dict()])
        prediction, probabilty, recommendation = predict_booking(input_df)
        return PredictionOutput(
            booking_prediction=prediction,
            booking_probabilty=probabilty,
            recommendation=recommendation)

    except Exception as e:
        raise HTTPException(status_code = 401, detail = str(e))
