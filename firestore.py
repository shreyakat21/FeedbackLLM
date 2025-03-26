import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firestore():
    cred = credentials.Certificate(r'C:\Users\Shreya Katiyar\Desktop\Feedback LLM\feedback-llm-firebase-adminsdk-fbsvc-83f477aa53.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db