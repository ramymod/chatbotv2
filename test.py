import requests

url = "http://127.0.0.1:5000/chat"

while True:
    msg = input("You (Arabic): ")
    if msg.lower() == 'exit': break

    response = requests.post(url, json={"user_id": "ramy_1", "message": msg})
    print("Bot:", response.json().get('reply'))