import firebase_admin
from firebase_admin import credentials, firestore

def initialize_firestore():
    # Use raw string to avoid backslash escaping issues
    cred = credentials.Certificate(r'C:\Users\Shreya Katiyar\Desktop\Feedback LLM\feedback-llm-firebase-adminsdk-fbsvc-d237b90db0.json') 
    
    # Initialize the Firebase Admin SDK
    firebase_admin.initialize_app(cred)
    
    # Get Firestore client
    db = firestore.client()
    
    return db
