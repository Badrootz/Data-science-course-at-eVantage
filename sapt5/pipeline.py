import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

data = pd.read_csv("vehicle_emissions.csv")
print(data.head())
data.info()

X = data.drop(["CO2_Emissions"], axis=1)
y = data["CO2_Emissions"]

numerical_columns = ["Model_Year", "Engine_Size", "Cylinders", "Fuel_Consumption_in_City(L/100 km)",
             "Fuel_Consumption_in_City_Hwy(L/100 km)", "Fuel_Consumption_comb(L/100km)", "Smog_Level"]

categorial_columns = ["Make", "Model", "Vehicle_Class", "Transmission"]

numerical_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy="mean")),
    ('scaler', StandardScaler())
])

categorial_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy="most_frequent")),
    ('encoder', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer([
    ('num', numerical_pipeline, numerical_columns),
    ('cat', categorial_pipeline, categorial_columns)
])

pipeline = Pipeline([
    ('preproccesor', preprocessor),
    ('model', RandomForestRegressor())
])

X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.2, random_state=42)

pipeline.fit(X_train, y_train)

prediction = pipeline.predict(X_test)

# encoded_cols = pipeline.named_steps['preproccesor'].named_transformers_['cat']['encoder'].get_feature_names_out(categorial_columns)
# print(encoded_cols)

mse = mean_squared_error(y_test, prediction)
rmse = np.sqrt(mse)

r2 = r2_score(y_test, prediction)
mae = mean_squared_error(y_test, prediction)

print(f'Model Performance:')
print (f'R2 Score:{r2}')
print (f'Root Mean Square Error:{rmse}')
print(f'Mean Absolute Error:{mae}')

joblib.dump(pipeline,"vehicle_emissions_pipeline.joblib")