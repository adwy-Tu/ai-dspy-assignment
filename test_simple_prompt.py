import requests
import json

def test_model():
    url = "http://localhost:11434/api/generate"
    
    schema = """
    Tables:
    - Products (ProductID, ProductName, CategoryID, UnitPrice, UnitsInStock)
    - Categories (CategoryID, CategoryName)
    """
    
    prompt = f"""You are a SQLite expert.
    
    Schema:
    {schema}
    
    Question: What is the return window for unopened Beverages?
    
    Return ONLY a JSON object: {{"sql": "SELECT ...", "answer": "..."}}
    """
    
    payload = {
        "model": "phi3.5:3.8b-mini-instruct-q4_K_M",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    }
    
    print("Sending request...")
    try:
        response = requests.post(url, json=payload)
        print("Status:", response.status_code)
        print("Response:", response.json()['response'])
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_model()
