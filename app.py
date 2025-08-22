from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, phone, password, age, gender, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, password, age, gender, location))
        mysql.connection.commit()
        return {"success": True, "message": "Registration successful!"}
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
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM users WHERE email=%s OR phone=%s
        """, (username, username))
        user = cursor.fetchone()
        # print("Username from form:", username)
        # print("Password from form:", password)
        # print("User from DB:", user)
        # print("Password from DB:", user['password'] if user else None)
        if user and user['password'] == password:
            session['loggedin'] = True
            session['id'] = user['id']
            session['name'] = user['name']
            return {"success": True, "message": "Login successful!", "redirect": "/dashboard"}
        else:
            return {"success": False, "message": "Invalid credentials."}
    return render_template('login.html')

@app.route('/dashboard')
def chat():
    if 'loggedin' in session:
        return render_template('chat.html', username=session['name'])
    return redirect(url_for('login'))

@app.route('/login.html')
def login_page():
    return render_template('login.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    encounter_id = data.get('encounter_id', 1)  # Use actual encounter_id if available
    locale = data.get('locale', 'en')
    text = data.get('text', '')

    # Save message to DB
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO messages (encounter_id, role, text)
        VALUES (%s, %s, %s)
    """, (encounter_id, 'user', text))
    mysql.connection.commit()

    # Run triage logic
    triage_result = run_triage(text)

    # Save triage to encounter (optional)
    cursor.execute("""
        UPDATE encounters SET risk_level=%s, disposition_text=%s WHERE id=%s
    """, (triage_result['triage_level'], triage_result['disposition'], encounter_id))
    mysql.connection.commit()

    # Respond with triage info
    return jsonify({
        "questions_next": triage_result['questions_next'],
        "patient_summary": triage_result['summary'],
        "triage_level": triage_result['triage_level'],
        "disposition": triage_result['disposition'],
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
