# Feedback LLM | AI Prompt Engineering · Automated Grading & Feedback

Feedback LLM is an AI-powered platform developed to automate grading and provide feedback for homework and lab reports. By leveraging large language models (LLMs), it improves grading efficiency and ensures consistent, high-quality feedback for students.

## Key Features
- **Automated Grading**  
  Uses LLMs to automatically grade assignments and lab reports, improving grading efficiency by 62%.

- **Feedback Generation**  
  Generates detailed feedback for student submissions, enhancing the learning experience.

- **Software Testing & Reliability**  
  Designed and executed 30+ test cases to ensure accuracy and reliability, resolving performance issues and improving response quality by 48%.

- **Team Collaboration**  
  Worked across technical and non-technical roles, communicating findings effectively and adapting to shifting project demands within the development lifecycle.

## Technologies Used
- Python  
- Flask & FastAPI  
- OpenAI API  
- Fetch API & Axios  
- AWS, Google Cloud  
- Deployment: Heroku, Netlify, Vercel  

## Getting Started

### Prerequisites  
Ensure Python 3.x is installed along with necessary dependencies. You will also need API keys for OpenAI and any cloud services used.

### Installation  
1. Clone the repository:  
   ```bash
   git clone https://github.com/shreyakat21/Feedback-LLM.git
   ```
2. Navigate to the project directory:  
   ```bash
   cd Feedback-LLM
   ```
3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

### Usage  
Run the application (for example with Flask):  
```bash
export FLASK_APP=app.py
flask run
```
Or with FastAPI:  
```bash
uvicorn main:app --reload
```
Follow the on-screen instructions to submit assignments for automated grading and feedback.

## Project Structure
- `app.py` / `main.py` — Core application scripts for API endpoints and grading logic.  
- `tests/` — Contains test cases for grading accuracy and performance validation.  
- `requirements.txt` — Lists all dependencies.  
- `README.md` — Project documentation.  

## Results and Impact
- Automated grading improved efficiency by 62%.  
- Response quality improved by 48% after performance optimization.  
- Successfully collaborated across technical and non-technical roles to meet project goals.

## Future Enhancements
- Expand grading and feedback to multiple subjects and assignment types.  
- Integrate with Learning Management Systems (LMS) for seamless submission and grading.  
- Implement user dashboards for instructors and students to track progress and feedback.  
- Optimize model performance for faster response times and higher accuracy.

## License  
This project is licensed under the MIT License. See the `LICENSE` file for details.
