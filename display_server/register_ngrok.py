import requests
import json
import time
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import tkinter as tk
from tkinter import font

SHARED_KEY = b'\x9f\x1c=&\xa6\xdf}\x8b$\x1c4\x85]\xe2\xc1\xa3\xd2\xb7\xe4\xf9c\x19\x114\xf6`\xaa\x84l\nMp'
WIDTH = 30
DEVICE_ID = "00001"
NGROK_API_URL = "http://localhost:4040/api/tunnels"
GCP_SERVER_URL = "http://34.64.216.79/api/register_display"

def encrypt_data(data: dict) -> bytes:
    aesgcm = AESGCM(SHARED_KEY)
    nonce = os.urandom(12)
    json_data = json.dumps(data).encode('utf-8')
    encrypted = aesgcm.encrypt(nonce, json_data, None)
    return nonce + encrypted

def get_ngrok_url():
    response = requests.get(NGROK_API_URL)
    tunnels = response.json()['tunnels']
    public_url = tunnels[0]['public_url']
    return public_url

def calculate_chars_per_line():
    root = tk.Tk()
    root.withdraw()  # 창 안 띄우기
    display_font = font.Font(family='NanumGothicCoding', size=20)
    screen_width_px = root.winfo_screenwidth()
    char_width_px = display_font.measure("0")
    chars_per_line = screen_width_px // char_width_px
    root.destroy()
    return chars_per_line

def register_with_server(ngrok_url, chars_per_line):
    device_data = {
        "device_id": DEVICE_ID,
        "display_url": ngrok_url,
        "width": WIDTH,
        "chars_per_line": chars_per_line,
    }

    encrypted_data = encrypt_data(device_data)

    data = {
        "encrypted_data": encrypted_data.hex()
    }

    try:
        response = requests.post(GCP_SERVER_URL, json=data)
        if response.status_code == 200:
            print(f"✅ Successfully registered with URL: {ngrok_url}")
            return True
        else:
            print(f"❌ Failed to register: {response.status_code}\n{response.text}")
    except Exception as e:
        print(f"❌ Exception during registration: {e}")

    return False

def main():
    time.sleep(5)
    chars_per_line = calculate_chars_per_line()

    while True:
        try:
            ngrok_url = get_ngrok_url()
            success = register_with_server(ngrok_url, chars_per_line)
            if success:
                break
        except Exception as e:
            print(f"❌ Error during ngrok URL fetch or registration: {e}")
        time.sleep(10)

if __name__ == "__main__":
    main()
