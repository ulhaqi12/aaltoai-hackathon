import requests
import webbrowser

# API endpoint
url = "http://localhost:8074/pipeline"

# Request payload
payload = {
    "intent": "What is the total count of orders placed each month in 1997?"
}

# Send POST request
response = requests.post(url, json=payload)

if response.status_code == 200:
    data = response.json()
    
    if data.get("success"):
        # Extract HTML report
        html_content = data["html_report"]
        filename = "report.html"
        
        # Save to HTML file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ Report saved to {filename}")
        # Automatically open in default web browser
        webbrowser.open(filename)
    else:
        print("❌ Report generation failed:", data)
else:
    print(f"❌ Request failed with status {response.status_code}")
    print(response.text)
