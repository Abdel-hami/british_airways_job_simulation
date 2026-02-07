from fastapi import HTTPException
import pandas as pd
import numpy as np
import pickle
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / "model"
## loading the model
model = None
with open(MODEL_DIR / 'model.pkl', 'rb') as f:
    model = pickle.load(f)

## loading features mapping
feature_mapings = None
with open( MODEL_DIR / 'feature_mapping.pkl', 'rb') as fm:
    feature_mapings = pickle.load(fm)



def enginner_feature(df):
        df['purchase_lead_log'] = np.log1p(df['purchase_lead'])
        df['length_of_stay_log'] = np.log1p(df['length_of_stay'])
        df['is_last_minute'] =( df['purchase_lead'] <= 7).astype(int)
        df['is_night_flight'] = ((df['flight_hour'] >= 22) | (df['flight_hour'] <= 5)).astype(int)
        df['is_weeken_flight'] = df['flight_day'].isin([6,7]).astype(int)
        df['extra_count'] = (df['wants_extra_baggage']+df['wants_preferred_seat']+df['wants_in_flight_meals'])
     
        if feature_mapings and 'route_popularity' in feature_mapings:
            df['route_popularity'] = df['route'].map(feature_mapings['route_popularity']).fillna(0.0)    
        else:
            df['route_popularity'] = 0.0  # Default value

        if feature_mapings and 'booking_origin_popularity' in feature_mapings:
            df['booking_origin_popularity'] = df['booking_origin'].map(feature_mapings['booking_origin_popularity']).fillna(0.0)     
        else:
            df['booking_origin_popularity'] = 0.0  # Default value
        return df

def predict_booking(input_df: pd.DataFrame):
    
        if model is None:
            raise HTTPException(status_code = 503, detail="model_not_found")
        ## feature enginner data as in training
        processed_data = enginner_feature(input_df)

        prediction = model.predict(processed_data)[0]
        probability = model.predict_proba(processed_data)[0][1]

        if probability >= 0.7:
            recommendation = "High likelihood - No intervention needed"
        elif probability >= 0.5:
            recommendation = "Moderate likelihood - Consider small incentive"
        elif probability >= 0.3:
            recommendation = "Low likelihood - Offer targeted promotion"
        else:
            recommendation = "Very low likelihood - Consider aggressive discount"

        return int(prediction), round(float(probability),4), str(recommendation)
