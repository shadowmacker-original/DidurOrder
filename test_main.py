import pytest
import requests
from fastapi.testclient import TestClient
from main import app, PRODUCT_SERVICE_URL
from database import database

# Мокуємо базу даних, щоб тести працювали на GitHub Actions без реальної MySQL
@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    async def mock_connect():
        pass

    async def mock_disconnect():
        pass

    async def mock_execute(query):
        return 1  # Повертаємо фейковий id останнього запису

    # Створюємо простий клас, щоб поля можна було викликати через крапку (order.id)
    class FakeRecord(dict):
        def __getattr__(self, key):
            try:
                return self[key]
            except KeyError:
                raise AttributeError(f"'FakeRecord' object has no attribute '{key}'")

    async def mock_fetch_all(query):
        # Якщо запит йде до таблиці orders
        if "orders" in str(query):
            return [
                FakeRecord({"id": 1, "total_amount": 2800.50})
            ]
        # Якщо запит йде до таблиці order_items
        return [
            FakeRecord({"id": 1, "order_id": 1, "product_id": 1, "quantity": 1}),
            FakeRecord({"id": 2, "order_id": 1, "product_id": 2, "quantity": 2})
        ]

    monkeypatch.setattr(database, "connect", mock_connect)
    monkeypatch.setattr(database, "disconnect", mock_disconnect)
    monkeypatch.setattr(database, "execute", mock_execute)
    monkeypatch.setattr(database, "fetch_all", mock_fetch_all)

client = TestClient(app)

# 1. Успішне створення замовлення
def test_create_order_success(requests_mock):
    requests_mock.get(f"{PRODUCT_SERVICE_URL}/1", json={"id": 1, "name": "Laptop", "price": 1200.50}, status_code=200)
    requests_mock.get(f"{PRODUCT_SERVICE_URL}/2", json={"id": 2, "name": "Smartphone", "price": 800.00}, status_code=200)

    payload = [
        {"product_id": 1, "quantity": 1},
        {"product_id": 2, "quantity": 2}
    ]

    response = client.post("/orders", json=payload)

    assert response.status_code == 201, f"Response error: {response.text}"
    data = response.json()
    assert data["total_amount"] == 2800.50
    assert len(data["items"]) == 2

# 2. Помилка 400 Bad Request при неіснуючому product_id
def test_create_order_product_not_found(requests_mock):
    requests_mock.get(f"{PRODUCT_SERVICE_URL}/999", status_code=404)

    payload = [
        {"product_id": 999, "quantity": 1}
    ]

    response = client.post("/orders", json=payload)

    assert response.status_code == 400
    assert "not found" in response.json()["detail"]

# 3. Помилка 503 Service Unavailable, коли сервіс продуктів недоступний
def test_create_order_service_unavailable(requests_mock):
    requests_mock.get(f"{PRODUCT_SERVICE_URL}/1", exc=requests.exceptions.ConnectTimeout)

    payload = [
        {"product_id": 1, "quantity": 1}
    ]

    response = client.post("/orders", json=payload)

    assert response.status_code == 503
    assert "Cannot connect to Product service" in response.json()["detail"]

# 4. Додатковий тест для перевірки GET /orders
def test_get_orders_success(requests_mock):
    response = client.get("/orders")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "total_amount" in data[0]
    assert "items" in data[0]