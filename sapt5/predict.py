import sys
import joblib
import numpy as np
import pandas as pd

def add_engineered_features(df):
    df = df.copy()
    df["fuel_efficiency_gap"] = df["Fuel_Consumption_in_City(L/100 km)"] - df["Fuel_Consumption_in_City_Hwy(L/100 km)"]
    df["engine_per_cylinder"] = df["Engine_Size"] / df["Cylinders"]
    trans = df["Transmission"].astype(str)
    df["Transmission"] = np.where(trans.str.startswith("A"), "Automatic", np.where(trans.str.startswith("M"), "Manual", "Other"))
    return df

sys.modules["__main__"].add_engineered_features = add_engineered_features

pipeline = joblib.load("vehicle_emissions_pipeline.joblib")


def predict(vehicle_dict: dict) -> float:
    df = pd.DataFrame([vehicle_dict])
    return float(pipeline.predict(df)[0])


if __name__ == "__main__":
    sample = {
        "Model_Year": 2021, "Make": "Acura", "Model": "ILX", "Vehicle_Class": "COMPACT",
        "Engine_Size": 2.4, "Cylinders": 4, "Transmission": "AM8",
        "Fuel_Consumption_in_City(L/100 km)": 9.9, "Fuel_Consumption_in_City_Hwy(L/100 km)": 7.0,
        "Fuel_Consumption_comb(L/100km)": 8.6, "Smog_Level": 3
    }
    print("Predicted CO2 Emissions:", round(predict(sample), 2), "g/km")
