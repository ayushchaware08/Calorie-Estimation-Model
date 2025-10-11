from fastapi.testclient import TestClient
from backend.main import app
from PIL import Image
import io


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_predict_with_fake_image():
    # create a small red image
    img = Image.new('RGB', (64, 64), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    files = {"file": ("test.jpg", buf, "image/jpeg")}
    r = client.post('/predict', files=files)
    assert r.status_code == 200
    data = r.json()
    assert 'items' in data
    assert 'total_calories' in data
