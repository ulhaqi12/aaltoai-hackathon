import requests

# URL of the FastAPI endpoint
url = "http://localhost:8070/ask"

# Test payload
payload = {
    "question": "What are the total sales amounts by customer for our top 10 customers?"
}

# Make POST request
response = requests.post(url, json=payload)

# Check and print response
if response.status_code == 200:
    data = response.json()
    print("Response:")
    print("Answer:", data.get("answer"))
    print("SQL Query:", data.get("sql_query"))
else:
    print(f"Request failed with status {response.status_code}")
    print("Response body:", response.text)
