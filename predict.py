# save as test_predict.py and run with the venv active
import requests
r = requests.post("http://127.0.0.1:8000/predict", files={"file": open(r"G:\KyvraLabs\calorie-estimation-model\burger.jpg","rb")})
print(r.status_code, r.json())