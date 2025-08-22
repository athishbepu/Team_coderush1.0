def ollama_response(prompt, model="mistral"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["response"]
    else:
        print("Ollama error:", response.text)
        return "Sorry, the assistant is unavailable."
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import json
import re

app = Flask(__name__)
app.config.from_pyfile('config.py')

mysql = MySQL(app)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Accept both form and JSON data for flexibility
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            phone = data.get('phone')
            password = data.get('password')
            age = data.get('age')
            gender = data.get('gender')
            location = data.get('location')
        else:
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            age = request.form.get('age')
            gender = request.form.get('gender')
            location = request.form.get('location')
        if not password:
            return {"success": False, "message": "Password cannot be empty."}
        try:
            cursor = mysql.connection.cursor()
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (name, email, phone, password, age, gender, location)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, email, phone, hashed_password, age, gender, location))
            mysql.connection.commit()
            return {"success": True, "message": "Registration successful!"}
        except Exception as e:
            return {"success": False, "message": f"Registration failed: {str(e)}"}
    return render_template('register.html')

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            # print(username, password)
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            # print(username, password)
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email=%s OR phone=%s", (username, username))
            user = cursor.fetchone()
            if user:
                desc = cursor.description
                user_dict = {desc[i][0]: user[i] for i in range(len(user))}
                if check_password_hash(user_dict['password'], password):
                    session['loggedin'] = True
                    session['id'] = user_dict['id']
                    session['name'] = user_dict['name']
                    return {"success": True, "message": "Login successful!", "redirect": "/dashboard"}
            return {"success": False, "message": "Invalid credentials."}
        except Exception as e:
            return {"success": False, "message": f"Login failed: {str(e)}"}
    return render_template('login.html')

@app.route('/dashboard')
def chat():
    if 'loggedin' in session:
        return render_template('chat.html', username=session['name'])
    return redirect(url_for('login'))

@app.route('/login.html')
def login_page():
    return render_template('login.html')

def extract_symptoms(text):
    # Simple example: extract keywords from red flag patterns
    with open('rules/red_flags.json', 'r') as f:
        rules = json.load(f)
    found = []
    text_lower = text.lower()
    for rule in rules:
        for pattern in rule['pattern']:
            if pattern in text_lower:
                found.append(pattern)
    return found

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    encounter_id = data.get('encounter_id')
    locale = data.get('locale', 'en')
    text = data.get('text', '')

    # Save message to DB
    cursor = mysql.connection.cursor()
    cursor.execute(
        "INSERT INTO messages (encounter_id, role, text) VALUES (%s, %s, %s)",
        (encounter_id, 'user', text)
    )
    mysql.connection.commit()

    # Run triage logic
    triage_result = run_triage(text)

    # Save triage to encounter (optional)
    cursor.execute("""
        UPDATE encounters SET risk_level=%s, disposition_text=%s WHERE id=%s
    """, (triage_result['triage_level'], triage_result['disposition'], encounter_id))
    mysql.connection.commit()

    # Extract and save symptoms
    symptoms = extract_symptoms(text)
    for symptom in symptoms:
        cursor.execute(
            "INSERT INTO symptoms (encounter_id, name, present) VALUES (%s, %s, %s)",
            (encounter_id, symptom, 1)
        )
    mysql.connection.commit()

    # Prepare prompt for AI model
    prompt = f"You are a virtual doctor assistant.if any other language than enlish reply in english only \nChat history: {text}\nTriage: {triage_result['disposition']}\nPlease provide a helpful, safe, and context-aware response."
    ai_reply = ollama_response(prompt, model="mistral")

    # Respond with triage info and AI reply
    return jsonify({
        "questions_next": triage_result['questions_next'],
        "patient_summary": triage_result['summary'],
        "triage_level": triage_result['triage_level'],
        "disposition": ai_reply,
        "watchouts": triage_result['watchouts'],
        "telemedicine": {
            "label": "Connect to eSanjeevani",
            "url": "https://esanjeevani.mohfw.gov.in/"
        }
    })

@app.route('/api/telemedicine/referral', methods=['GET'])
def api_telemedicine_referral():
    return {"url": "https://esanjeevani.mohfw.gov.in/"}

@app.route('/api/abdm/mock/link', methods=['POST'])
def api_abdm_mock_link():
    data = request.get_json()
    abha_number = data.get('abha_number')
    # Save abha_number to encounter if needed
    return {"status": "linked (sandbox)"}

@app.route('/api/start_encounter', methods=['POST'])
def start_encounter():
    user_id = session.get('id')
    locale = request.json.get('locale', 'en')
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO encounters (user_id, locale) VALUES (%s, %s)", (user_id, locale))
    mysql.connection.commit()
    encounter_id = cursor.lastrowid
    return jsonify({"encounter_id": encounter_id})

def run_triage(text):
    with open('rules/red_flags.json', 'r') as f:
        rules = json.load(f)
    text_lower = text.lower()
    for rule in rules:
        for pattern in rule['pattern']:
            if pattern in text_lower:
                return {
                    "triage_level": rule['triage'],
                    "disposition": rule.get('message', 'Please seek immediate care.'),
                    "questions_next": [],
                    "summary": "Red flag detected: " + pattern,
                    "watchouts": [rule.get('message', '')]
                }
    # No red flag detected
    return {
        "triage_level": "routine",
        "disposition": "Continue answering questions.",
        "questions_next": ["How long have you had these symptoms?", "Any fever?"],
        "summary": "No red flags detected.",
        "watchouts": []
    }


if __name__ == '__main__':
    app.run(debug=True)

import requests

def ollama_response(prompt, model="mistral"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data["response"]
    else:
        print("Ollama error:", response.text)
        return "Sorry, the assistant is unavailable."

# Example usage:
print(ollama_response("What is the meaning of life?", model="mistral"))
