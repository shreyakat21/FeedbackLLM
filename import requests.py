import requests

url = "http://localhost:5000/analyze_lab_report"
data = {
    "student_name": "John Doe",
    "lab_report": "Experiment on Fish...",
    "rubric": "Rubric details..."
}

response = requests.post(url, json=data)
print(response.json())