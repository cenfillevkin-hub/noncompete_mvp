import requests

data = {
    "narrative": "Franchisee agreed not to compete within 30 miles",
    "criteria": {"ancillary": "Yes", "consideration": "Yes", "territory": "Yes"}
}

response = requests.post("http://127.0.0.1:8000/compare", json=data)
print(response.json())
