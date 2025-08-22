from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import MySQLdb.cursors
from datetime import datetime

app = Flask(__name__)
app.config.from_pyfile('config.py')

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# ------------------ ROUTES ------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------ REGISTER ------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        location = request.form.get('location')

        # Hash password
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO users (name, email, phone, password, age, gender, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, phone, hashed_pw, age, gender, location))
        mysql.connection.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

from datetime import datetime

# ------------------ API: Stateful Chat ------------------
@app.route('/api/chat', methods=['POST'])
def api_chat():
    if 'loggedin' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    encounter_id = data.get('encounter_id')
    message = data.get('message')
    user_id = session['id']

    # Save message
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO messages (encounter_id, role, text, ts)
        VALUES (%s, %s, %s, %s)
    """, (encounter_id, 'user', message, datetime.now()))
    mysql.connection.commit()

    # Dummy bot response (expand with symptom collection logic)
    bot_reply = "Thank you for sharing. Can you tell me more about your symptoms?"

    cursor.execute("""
        INSERT INTO messages (encounter_id, role, text, ts)
        VALUES (%s, %s, %s, %s)
    """, (encounter_id, 'assistant', bot_reply, datetime.now()))
    mysql.connection.commit()

    return jsonify({"response": bot_reply})

# ------------------ API: Triage ------------------
@app.route('/api/triage', methods=['POST'])
def api_triage():
    data = request.json
    symptoms = data.get('symptoms', [])
    # Load red-flag rules from JSON (implement actual logic)
    # For demo, if "chest pain" in symptoms, mark as emergency
    risk_level = "routine"
    disposition = "You can manage at home. Watch for worsening symptoms."
    disclaimer = "This is not medical advice. Please consult a doctor if unsure."

    if "chest pain" in [s.lower() for s in symptoms]:
        risk_level = "emergency"
        disposition = "Go to the ER immediately!"

    return jsonify({
        "risk_level": risk_level,
        "disposition": disposition,
        "disclaimer": disclaimer
    })

# ------------------ API: Transcribe (Whisper) ------------------
@app.route('/api/transcribe', methods=['POST'])
def api_transcribe():
    # Accept audio file, return dummy text (replace with Whisper integration)
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    # For demo, just return a static string
    return jsonify({"text": "Transcribed text goes here."})

# ------------------ API: Mock ABHA Create/Link ------------------
@app.route('/api/abdm/mock/create', methods=['POST'])
def api_abdm_mock_create():
    # Return mock ABHA number
    return jsonify({"abha_number": "ABHA1234567890"})

@app.route('/api/abdm/mock/link', methods=['POST'])
def api_abdm_mock_link():
    # Return mock link status
    return jsonify({"status": "linked"})

# ------------------ API: Telemedicine Referral ------------------
@app.route('/api/telemedicine/referral', methods=['GET'])
def api_telemedicine_referral():
    # Return eSanjeevani portal link
    return jsonify({"url": "https://esanjeevani.mohfw.gov.in/"})

# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s OR phone=%s", (username, username))
        user = cursor.fetchone()
        if user and bcrypt.check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['id'] = user['id']
            session['name'] = user['name']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
            return render_template('login.html')
    return render_template('login.html')

# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('chat.html', username=session['name'])
    return redirect(url_for('login'))

# ------------------ CHAT API ------------------
@app.route('/chat', methods=['POST'])
def chat():
    if 'loggedin' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json.get('message')
    user_id = session['id']

    # Simple rule-based response for Phase 1
    if "fever" in user_message.lower():
        bot_reply = "It seems you might have a fever. Stay hydrated and rest. If symptoms persist, visit a doctor."
    elif "cough" in user_message.lower():
        bot_reply = "Cough detected. Drink warm fluids and monitor symptoms."
    else:
        bot_reply = "I am still learning. Can you describe your symptoms more clearly?"

    # Store chat log
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO chat_logs (user_id, message, response)
        VALUES (%s, %s, %s)
    """, (user_id, user_message, bot_reply))
    mysql.connection.commit()

    return jsonify({"response": bot_reply})

if __name__ == '__main__':
    app.run(debug=True)
