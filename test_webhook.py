import httpx
import json

# Đọc payload
with open("test_payload.json") as f:
    payload = json.load(f)

# Test 1: Gửi request với token đúng
print("=== Test 1: Gửi với X-Gitlab-Token ===")
response = httpx.post(
    "http://localhost:8000/gitlab/webhook",
    json=payload,
    headers={"X-Gitlab-Token": "chamchi123"}
)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}\n")

# Test 2: Gửi không có token (sẽ lỗi)
print("=== Test 2: Gửi không có token (expect 401) ===")
response2 = httpx.post(
    "http://localhost:8000/gitlab/webhook",
    json=payload
)
print(f"Status Code: {response2.status_code}")
print(f"Response: {response2.text}\n")

# Test 3: Gửi event không phải MR
print("=== Test 3: Gửi event khác (sẽ bị ignore) ===")
other_payload = {"object_kind": "push", "user": {"name": "test"}}
response3 = httpx.post(
    "http://localhost:8000/gitlab/webhook",
    json=other_payload,
    headers={"X-Gitlab-Token": "chamchi123"}
)
print(f"Status Code: {response3.status_code}")
print(f"Response: {response3.text}")
