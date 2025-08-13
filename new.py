import pandas as pd


df = pd.read_csv('air_quality_health_impact_data.csv')


print(df.head())
print(df.info())
print(df.describe())


print(df.isnull().sum())

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
import joblib
import sys 
sys.stdout.reconfigure(encoding='utf-8')


features_aqi = ['PM10', 'PM2_5', 'NO2', 'SO2', 'O3']
target_aqi = 'AQI'

X_aqi = df[features_aqi]
y_aqi = df[target_aqi]

# Chia dữ liệu
X_aqi_train, X_aqi_test, y_aqi_train, y_aqi_test = train_test_split(X_aqi, y_aqi, test_size=0.2, random_state=42)

# Huấn luyện mô hình Random Forest
aqi_estimator_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
aqi_estimator_model.fit(X_aqi_train, y_aqi_train)

# Đánh giá mô hình
predictions_aqi = aqi_estimator_model.predict(X_aqi_test)
mse_aqi = mean_squared_error(y_aqi_test, predictions_aqi)
print(f"Lỗi Trung bình Bình phương (MSE) của Mô hình Ước tính AQI: {mse_aqi:.2f}")

# Lưu lại mô hình 
joblib.dump(aqi_estimator_model, 'aqi_estimator_model.pkl')
print("Đã lưu mô hình ước tính AQI.")
# Chọn các đặc trưng và mục tiêu
features_health = ['AQI', 'Temperature', 'Humidity']
target_health = 'HealthImpactScore'

X_health = df[features_health]
y_health = df[target_health]

# Chia dữ liệu
X_health_train, X_health_test, y_health_train, y_health_test = train_test_split(X_health, y_health, test_size=0.2, random_state=42)

# Huấn luyện mô hình Random Forest 
health_predictor_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
health_predictor_model.fit(X_health_train, y_health_train)

#  Đánh giá mô hình
predictions_health = health_predictor_model.predict(X_health_test)
mse_health = mean_squared_error(y_health_test, predictions_health)
print(f"Lỗi Trung bình Bình phương (MSE) của Mô hình Dự đoán Sức khỏe: {mse_health:.2f}")

#  Lưu lại mô hình chính này
joblib.dump(health_predictor_model, 'health_predictor_model.pkl')
print("Đã lưu mô hình dự đoán sức khỏe.")