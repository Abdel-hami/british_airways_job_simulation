from pydantic import Field, BaseModel
from typing import Optional


## defining schemas for both input and output 


class BookingInput(BaseModel):
    purchase_lead: int = Field(..., ge=0, description="Days between booking and travel")
    length_of_stay: int = Field(..., ge=1, description="Number of days at destination")
    flight_hour: int = Field(..., ge=0, le=23, description="Hour of flight departure (0-23)")
    flight_day: int = Field(..., ge=1, le=7, description="Day of week (1=Mon, 7=Sun)")
    route: str = Field(..., description="Flight route (e.g., AKLDEL)")
    booking_origin: str = Field(..., description="Country of booking origin")
    wants_extra_baggage: int = Field(..., ge=0, le=1, description="Extra baggage (0 or 1)")
    wants_preferred_seat: int = Field(..., ge=0, le=1, description="Preferred seat (0 or 1)")
    wants_in_flight_meals: int = Field(..., ge=0, le=1, description="In-flight meals (0 or 1)")
    flight_duration: float = Field(..., gt=0, description="Flight duration in hours")
    num_passengers: Optional[int] = Field(1, ge=1, description="Number of passengers")
    sales_channel: Optional[str] = Field("Internet", description="Sales channel")
    trip_type: Optional[str] = Field("RoundTrip", description="Trip type")

class PredictionOutput(BaseModel):
    booking_prediction: int
    booking_probabilty: float
    recommendation: str

