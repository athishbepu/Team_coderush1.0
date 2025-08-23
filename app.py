from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import json
import re
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
app = Flask(__name__)
app.config.from_pyfile('config.py')

mysql = MySQL(app)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------ CONTACT ------------------
@app.route('/contact')
def contact():
    return render_template('contact.html')
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
            cursor.execute("""
                INSERT INTO users (name, email, phone, password, age, gender, location)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (name, email, phone, password, age, gender, location))
            mysql.connection.commit()
            return {"success": True, "message": "Registration successful!"}
        except Exception as e:
            return {"success": False, "message": f"Registration failed: {str(e)}"}
    return render_template('register.html')

            
# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Accept both form and JSON POST, but always return HTML
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            print("1", username, password)
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            print(username, password)

        try:
            print("DEBUG: Attempting login with:", username)
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM users WHERE email=%s OR phone=%s", (username, username))
            user = cursor.fetchone()
            print(type(user))
            print("DEBUG: Query executed. Result:", user)
            if user and hasattr(user, 'values') and user.values():
                print("user value",user.values())
                columns = [col[0] for col in cursor.description]
                user_dict = dict(zip(columns, user.values()))
                print("user dict:", user_dict)
                print("DB password:", user_dict['password'])
                print("Entered password:", password)
                print(user_dict['password'] == password)
                if user_dict['password'] == password:
                    print("User authenticated successfully.")
                    session['loggedin'] = True
                    session['id'] = user_dict['id']
                    session['name'] = user_dict['name']
                    flash("Login successful!", "success")
                    return redirect(url_for('chat'))
                else:
                    print("Password mismatch.")
                    flash("Invalid username or password.", "danger")
                    return render_template('login.html')
            else:
                print("User not found.")
                flash("Invalid username or password.", "danger")
                return render_template('login.html')
        except Exception as e:
            print("Exception during login:", e)
            flash("Login failed. Please try again.", "danger")
            return render_template('login.html')
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

import requests
# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
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

# ------------------ ANALYSE ------------------
@app.route('/analyse', methods=['GET', 'POST'])
def analyse():
    if request.method == 'POST':
        data = request.get_json()
        age = int(data.get('age', 0))
        weight = float(data.get('weight', 0))
        height = float(data.get('height', 0))
        symptoms = data.get('symptoms', '')
        habits = data.get('habits', '')
        bp_systolic = int(data.get('bp_systolic', 0))
        bp_diastolic = int(data.get('bp_diastolic', 0))
        heart_rate = int(data.get('heart_rate', 0))
        blood_sugar = float(data.get('blood_sugar', 0))
        cholesterol = float(data.get('cholesterol', 0))
        activity_level = data.get('activity_level', '')
        diet_type = data.get('diet_type', '')
        text = symptoms  # Use symptoms as chat history text
        triage_result = run_triage(text)
        # Example analytics: BMI
        bmi = round(weight / ((height/100)**2), 2) if height > 0 else 0
        if bmi < 18.5:
            bmi_status = 'Underweight'
        elif bmi < 25:
            bmi_status = 'Normal'
        elif bmi < 30:
            bmi_status = 'Overweight'
        else:
            bmi_status = 'Obese'
        # Example risk score (simple logic)
        risk_score = 0
        if 'smoking' in habits.lower():
            risk_score += 2
        if 'exercise' not in habits.lower():
            risk_score += 1
        if age > 50:
            risk_score += 1
        if 'fever' in symptoms.lower():
            risk_score += 1

        # Hypertension analysis
        hypertension = 'Normal'
        if bp_systolic >= 140 or bp_diastolic >= 90:
            hypertension = 'High'
        elif bp_systolic >= 120 or bp_diastolic >= 80:
            hypertension = 'Elevated'

        # Diabetes analysis
        diabetes = 'Normal'
        if blood_sugar >= 126:
            diabetes = 'Diabetes'
        elif blood_sugar >= 100:
            diabetes = 'Prediabetes'

        # Cholesterol analysis
        cholesterol_status = 'Normal'
        if cholesterol >= 240:
            cholesterol_status = 'High'
        elif cholesterol >= 200:
            cholesterol_status = 'Borderline High'
        user_id = session.get('id')
        cursor = mysql.connection.cursor()
        # Store in MySQL
        cursor.execute('''
            INSERT INTO analyse_data (
                user_id, age, weight, height, symptoms, habits, bmi, bmi_status, risk_score,
                bp_systolic, bp_diastolic, heart_rate, blood_sugar, cholesterol, activity_level, diet_type,
                hypertension, diabetes, cholesterol_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user_id, age, weight, height, symptoms, habits, bmi, bmi_status, risk_score,
            bp_systolic, bp_diastolic, heart_rate, blood_sugar, cholesterol, activity_level, diet_type,
            hypertension, diabetes, cholesterol_status
        ))
        mysql.connection.commit()
        return jsonify({
            'bmi': bmi,
            'bmi_status': bmi_status,
            'risk_score': risk_score,
            'weight': weight,
            'age': age,
            'height': height,
            'bp_systolic': bp_systolic,
            'bp_diastolic': bp_diastolic,
            'heart_rate': heart_rate,
            'blood_sugar': blood_sugar,
            'cholesterol': cholesterol,
            'activity_level': activity_level,
            'diet_type': diet_type,
            'hypertension': hypertension,
            'diabetes': diabetes,
            'cholesterol_status': cholesterol_status,
            'symptoms': symptoms,
            'habits': habits
        })
    return render_template('analyse.html')


if __name__ == '__main__':
    app.run(debug=True)


