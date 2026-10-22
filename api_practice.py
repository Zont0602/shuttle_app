import requests

url = "https://jsonplaceholder.typicode.com/todos"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    for task in data:
        if not task["completed"] :
            print(task["title"])


except requests.exceptions.RequestException:
    print("API 請求失敗")
print("Git practice")

print("Testing feature branch")