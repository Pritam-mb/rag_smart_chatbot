import requests

BASE_URL = "http://127.0.0.1:8000/chat"

print("🤖 Arogya Sahayak Terminal Chat\nType 'exit' to quit.\n")

while True:
    user = input("You: ")

    if user.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break

    payload = {
        "message": user,
        "lat": None,
        "lon": None
    }

    try:
        res = requests.post(BASE_URL, json=payload)
        reply = res.json().get("reply") or res.json()
        print("\nBot:", reply, "\n")
    except Exception as e:
        print("Error:", e)
