import requests
import webbrowser
import time

# API endpoint
url = "http://localhost:8074/pipeline"

# List of 20 intent queries
intents = [
    "What are the total sales amounts by customer for our top 10 customers?",
    "Which products have the highest total sales volume?",
    "Show total sales by country.",
    "List the top 5 customers by number of orders.",
    "Which employees have handled the most orders?",
    "What are the top 10 selling products by revenue?",
    "List all discontinued products and their categories.",
    "Show average order value by customer.",
    "Which suppliers provide the most products?",
    "Show number of orders shipped by each shipper.",
    "Which cities have the highest number of customers?",
    "What is the average time between order and shipping?",
    "List the top 5 product categories by sales.",
    "Find all customers who haven’t ordered in the last year.",
    "Which employees report to each manager?",
    "Show customer count by region.",
    "List orders with a discount greater than 20%.",
    "Show total freight costs per shipping company.",
    "Which territories have the most employees assigned?",
    "Show total sales by employee and month."
]

# Send each query to the API
for idx, intent in enumerate(intents, 1):
    print(f"▶️ Sending intent {idx}: {intent}")
    payload = {
        "intent": intent,
        "model": "gpt-4o-mini"
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            html_content = data["html_report"]
            filename = f"report_{idx:02d}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"✅ Report {idx} saved to {filename}")
            webbrowser.open(filename)
            time.sleep(1)  # Delay to avoid too many tabs at once
        else:
            print(f"❌ Report {idx} generation failed:", data)
    else:
        print(f"❌ Request {idx} failed with status {response.status_code}")
        print(response.text)