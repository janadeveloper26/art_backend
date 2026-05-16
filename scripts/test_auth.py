import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_auth_flow():
    # 1. Request OTP (Check if blocked)
    print("\n--- 1. Requesting OTP ---")
    resp = requests.post(f"{BASE_URL}/auth/otp/request", json={"phone": "+919876543210"})
    print(f"Status: {resp.status_code}")
    print(resp.json())

    # 2. Login with Mock Token
    print("\n--- 2. Login with Mock Token (Initial) ---")
    login_payload = {
        "id_token": "test-token-123",
        "device": {
            "install_id": "test-device-001",
            "platform": "android",
            "device_model": "Pixel 7"
        }
    }
    resp = requests.post(f"{BASE_URL}/auth/firebase/login", json=login_payload)
    print(f"Status: {resp.status_code}")
    print(resp.json())
    
    # It should fail with 403 if device is not approved (or success if admin is auto-approved)
    # But wait, my logic says if it's the first time, it's PENDING.
    
    if resp.status_code == 403:
        print("Device is pending approval as expected.")
        
    # Note: To fully test, you would need to:
    # a) Login as admin
    # b) Approve the device test-device-001
    # c) Login again
    
    print("\nNext Steps for Manual Testing:")
    print("1. Create a superuser: uv run manage.py createsuperuser")
    print("2. Login to Django Admin at /admin")
    print("3. Find the UserDevice for Pixel 7 and set status to APPROVED")
    print("4. Run this script again or call /firebase/login")

if __name__ == "__main__":
    test_auth_flow()
