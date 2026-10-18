"""Tests for POST /predict and GET /model-info."""

from fastapi.testclient import TestClient

SPAM_MESSAGE = "Congratulations! You won a 1000 prize. Call 08001234567 now to claim."
HAM_MESSAGE = "Hi, are we still meeting for lunch tomorrow at noon?"


def test_predict_spam_message(client: TestClient) -> None:
    response = client.post("/predict", json={"message": SPAM_MESSAGE})

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "Penipuan"
    assert set(body["probabilities"]) == {"Penipuan", "Bukan Penipuan"}
    assert body["probabilities"]["Penipuan"] > body["probabilities"]["Bukan Penipuan"]
    assert body["probabilities"]["Penipuan"] > 0.5
    assert "<phone>" in body["processed_text"]
    assert "08001234567" not in body["processed_text"]


def test_predict_ham_message(client: TestClient) -> None:
    response = client.post("/predict", json={"message": HAM_MESSAGE})

    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "Bukan Penipuan"
    assert body["probabilities"]["Bukan Penipuan"] > body["probabilities"]["Penipuan"]
    assert body["processed_text"] == "hi still meeting lunch tomorrow noon"


def test_probabilities_sum_to_one(client: TestClient) -> None:
    body = client.post("/predict", json={"message": SPAM_MESSAGE}).json()

    total = sum(body["probabilities"].values())
    assert abs(total - 1.0) < 0.001


def test_label_matches_the_larger_probability(client: TestClient) -> None:
    body = client.post("/predict", json={"message": "Please confirm the meeting agenda"}).json()

    probabilities = body["probabilities"]
    assert probabilities[body["label"]] == max(probabilities.values())


def test_processes_the_text_the_same_way_as_training(client: TestClient) -> None:
    message = "FREE!!! Visit http://x.co or call 081234567890 about 500 cash"
    body = client.post("/predict", json={"message": message}).json()

    assert body["processed_text"] == "free visit <url> call <phone> <num> cash"


def test_empty_message_is_rejected(client: TestClient) -> None:
    response = client.post("/predict", json={"message": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_message_is_rejected(client: TestClient) -> None:
    response = client.post("/predict", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_too_long_message_is_rejected(client: TestClient) -> None:
    response = client.post("/predict", json={"message": "a" * 1001})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_model_info_returns_metadata(client: TestClient) -> None:
    response = client.get("/model-info")

    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "Multinomial Naive Bayes"
    assert 0.0 < body["accuracy"] <= 100.0
    assert body["train_size"] + body["test_size"] == body["dataset_size"]
    assert body["dataset"]["name"] in ("UCI SMS Spam Collection", "Indonesian SMS Spam Collection")
    assert body["split"]["stratified"] is True
