import requests

while True:
    msg = input("你：")
    if msg.lower() in ["exit", "quit"]:
        break

    print("")
    res = requests.post("http://localhost:5000/chat", json={"message": msg})
    print("小牢旺：", res.json().get("response", res.json().get("error")))
    print("")
