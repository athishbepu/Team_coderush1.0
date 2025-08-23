# Virtual Doctor Assistant

A hackathon-ready, AI-powered medical chatbot and health analytics platform designed to provide personalized health advice, triage, and voice-driven interactions in local languages.

## Features
- Secure login and registration
- Personalized dashboard with last analysis and recent chat
- Health analytics: BP, heart rate, blood sugar, cholesterol, activity, diet
- Persistent storage of user health data and chat history (MySQL)
- AI chatbot (Mistral LLM) for medical Q&A and advice
- Voice interaction via Whisper AI (supports local languages)
- Basic triage and health advice
- Responsive UI (Bootstrap, custom CSS)
- Logout functionality

## Technologies Used
- Flask (Python)
- MySQL
- Bootstrap & Custom CSS
- JavaScript
- Mistral (open-source LLM)
- Whisper AI (open-source)

## How It Works
1. User logs in or registers.
2. User enters health metrics and symptoms via text or voice.
3. AI chatbot collects information, analyzes data, and provides advice.
4. Health analytics and chat history are stored and shown on the dashboard.
5. User can log out securely.

## Setup Instructions
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up MySQL database and update `config.py` with your credentials.
4. Run the Flask app:
   ```bash
   python app.py
   ```
5. Access the app at `http://localhost:5000`

## Future Enhancements
- Integration with telemedicine portals for live doctor consultations
- Advanced analytics and visualization
- Support for more local languages

## License
This project uses open-source technologies and is intended for educational and demo purposes.
