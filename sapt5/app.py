from fastapi import FastAPI
from pydantic import BaseModel, Field
from predict import predict

app = FastAPI(title="Vehicle CO2 Emissions API")

class VehicleInput(BaseModel):
    Model_Year: int
    Make: str
    Model: str
    Vehicle_Class: str
    Engine_Size: float = Field(..., gt=0)
    Cylinders: int = Field(..., gt=0)
    Transmission: str
    Fuel_Consumption_in_City: float = Field(..., alias="Fuel_Consumption_in_City(L/100 km)", gt=0)
    Fuel_Consumption_Hwy: float = Field(..., alias="Fuel_Consumption_in_City_Hwy(L/100 km)", gt=0)
    Fuel_Consumption_comb: float = Field(..., alias="Fuel_Consumption_comb(L/100km)", gt=0)
    Smog_Level: int

    class Config:
        populate_by_name = True


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/predict")
def predict_emissions(vehicle: VehicleInput):
    vehicle_dict = {
        "Model_Year": vehicle.Model_Year,
        "Make": vehicle.Make,
        "Model": vehicle.Model,
        "Vehicle_Class": vehicle.Vehicle_Class,
        "Engine_Size": vehicle.Engine_Size,
        "Cylinders": vehicle.Cylinders,
        "Transmission": vehicle.Transmission,
        "Fuel_Consumption_in_City(L/100 km)": vehicle.Fuel_Consumption_in_City,
        "Fuel_Consumption_in_City_Hwy(L/100 km)": vehicle.Fuel_Consumption_Hwy,
        "Fuel_Consumption_comb(L/100km)": vehicle.Fuel_Consumption_comb,
        "Smog_Level": vehicle.Smog_Level,
    }
    prediction = predict(vehicle_dict)
    return {"predicted_co2_emissions": round(prediction, 2), "unit": "g/km"}
