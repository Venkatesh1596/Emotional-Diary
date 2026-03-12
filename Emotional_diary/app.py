import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, redirect, url_for, session, flash, send_file, request, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import pickle
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64


# PDF imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

import re

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

from wordcloud import WordCloud

nltk.data.path.append("C:/Users/venkatesh/nltk_data")  # optional if needed

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words("english"))

app = Flask(__name__)
import os
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

# ---------- LOAD ML MODEL ----------
with open("emotion_model.pkl", "rb") as f:
    model = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# ---------- LOGIN REQUIRED DECORATOR ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    words = text.split()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return " ".join(words)

def detect_emotion(text):
    processed = preprocess_text(text)
    vector = vectorizer.transform([processed])
    prediction = model.predict(vector)[0]

    # Confidence
    probabilities = model.predict_proba(vector)[0]
    confidence = round(max(probabilities) * 100, 2)

    # Intensity (simple scaling)
    intensity = confidence

    return prediction, confidence, intensity 
    

def generate_suggestion(emotion):
    suggestions = {
        "Happy": "That's wonderful! Keep spreading positivity and cherish this feeling.",
        "Positive": "You seem to be doing well. Stay consistent and keep growing.",
        "Neutral": "Take some time to reflect and do something you enjoy today.",
        "Sad": "It’s okay to feel sad. Consider talking to someone you trust.",
        "Angry": "Try deep breathing exercises or take a short walk to calm down."
    }
    return suggestions.get(emotion, "Take care of yourself and stay mindful.")

def advanced_recommendation(emotions, counts, weekly_growth):
    if not emotions or not counts:
        return "Start journaling regularly to receive personalized insights."

    emotion_distribution = dict(zip(emotions, counts))
    total = sum(counts)

    dominant = max(emotion_distribution, key=emotion_distribution.get)
    negative = emotion_distribution.get("Sad", 0) + emotion_distribution.get("Angry", 0)
    negative_ratio = negative / total

    if negative_ratio > 0.6:
        return "You have a high negative emotion pattern. Try meditation, physical activity, or talk to someone trusted."
    
    if dominant == "Happy":
        return "You are doing great! Maintain your routines and keep journaling positivity."
    
    if dominant == "Neutral":
        return "Try exploring new activities to bring more excitement into your routine."
    
    if weekly_growth < 0:
        return "Your journaling activity decreased. Consistency improves emotional awareness."

    return "Maintain balance and continue reflecting daily."

from datetime import datetime, timedelta

def calculate_streak(user_id):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="emotional_diary"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT DATE(created_at) as entry_date 
        FROM diary 
        WHERE user_id = %s 
        GROUP BY DATE(created_at)
        ORDER BY entry_date DESC
    """, (user_id,))
    
    dates = cursor.fetchall()
    conn.close()

    if not dates:
        return 0, 0

    date_list = [row['entry_date'] for row in dates]

    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    today = datetime.today().date()

    for i in range(len(date_list)):
        if i == 0:
            if date_list[i] == today or date_list[i] == today - timedelta(days=1):
                current_streak = 1
                temp_streak = 1
        else:
            if date_list[i-1] - date_list[i] == timedelta(days=1):
                temp_streak += 1
                if i == current_streak:
                    current_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                temp_streak = 1

    longest_streak = max(longest_streak, temp_streak)

    return current_streak, longest_streak


# ---------- DATABASE CONNECTION ----------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="emotional_diary"
    )


# ---------- LOGIN ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash("Login Successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid Email or Password", "danger")

    return render_template('login.html')


# ---------- REGISTER ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email already exists!", "danger")
            cursor.close()
            db.close()
            return redirect(url_for('register'))

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, password)
        )
        db.commit()
        cursor.close()
        db.close()

        flash("Registration Successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="emotional_diary"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name, email FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("profile.html", user=user)


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        new_password = request.form["password"]
        hashed_password = generate_password_hash(new_password)

        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="emotional_diary"
        )
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET password=%s WHERE id=%s",
                       (hashed_password, session["user_id"]))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Password updated successfully!", "success")
        return redirect(url_for("profile"))

    return render_template("change_password.html")

# ---------- HOME ----------
@app.route('/home')
@login_required
def home():
    return render_template('home.html', name=session['user_name'])


# ---------- SAVE DIARY ----------
@app.route('/save_diary', methods=['POST'])
@login_required
def save_diary():
    title = request.form['title']
    content = request.form['content']

    # IMPORTANT: unpack both values
    emotion, confidence, intensity = detect_emotion(content)
    suggestion = generate_suggestion(emotion)

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
    """
    INSERT INTO diary 
    (user_id, title, content, emotion, suggestion, confidence, intensity) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """,
    (session['user_id'], title, content, emotion, suggestion, confidence, intensity)
)

    db.commit()
    cursor.close()
    db.close()

    flash("Diary Saved Successfully!", "success")
    return redirect(url_for('home'))


# ---------- EDIT DIARY ----------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_diary(id):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        emotion, confidence, intensity = detect_emotion(content)
        suggestion = generate_suggestion(emotion)

        cursor.execute(
            "UPDATE diary SET title=%s, content=%s, emotion=%s, suggestion=%s, confidence=%s, intensity=%s WHERE id=%s AND user_id=%s",
            (title, content, emotion, suggestion, confidence, intensity, id, session['user_id'])
        )
        db.commit()
        cursor.close()
        db.close()

        flash("Diary Updated!", "success")
        return redirect(url_for('history'))

    cursor.execute("SELECT * FROM diary WHERE id=%s AND user_id=%s",
                   (id, session['user_id']))
    diary = cursor.fetchone()
    cursor.close()
    db.close()

    return render_template('edit.html', diary=diary)


# ---------- DELETE DIARY ----------
@app.route('/delete/<int:id>')
@login_required
def delete_diary(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM diary WHERE id=%s AND user_id=%s",
                   (id, session['user_id']))
    db.commit()
    cursor.close()
    db.close()

    flash("Diary Deleted!", "danger")
    return redirect(url_for('history'))


def calculate_health_score(emotions):
    score = 50

    for e in emotions:
        if e == "Happy":
            score += 10
        elif e == "Neutral":
            score += 5
        elif e == "Fear":
            score -= 5
        elif e == "Sad":
            score -= 10
        elif e == "Angry":
            score -= 15

    score = max(0, min(score, 100))
    return score

# ---------- DASHBOARD ----------
@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cursor = db.cursor()

    # ---------- PIE CHART DATA ----------
    cursor.execute(
        "SELECT emotion, COUNT(*) FROM diary WHERE user_id=%s GROUP BY emotion",
        (session['user_id'],)
    )
    pie_data = cursor.fetchall()

    emotions = [row[0] for row in pie_data]
    counts = [row[1] for row in pie_data]

    # ---------- LINE CHART DATA ----------
    cursor.execute(
        "SELECT DATE(created_at), COUNT(*) FROM diary WHERE user_id=%s GROUP BY DATE(created_at) ORDER BY DATE(created_at)",
        (session['user_id'],)
    )
    line_data = cursor.fetchall()

    dates = [str(row[0]) for row in line_data]
    entry_counts = [row[1] for row in line_data]

    # ---------- HEATMAP (Last 30 Days) ----------
    cursor.execute("""
        SELECT DATE(created_at), COUNT(*) 
        FROM diary 
        WHERE user_id=%s 
        AND DATE(created_at) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY DATE(created_at)
    """, (session['user_id'],))
    heatmap_data = cursor.fetchall()

    heatmap_dict = {str(row[0]): row[1] for row in heatmap_data}

    # ---------- WEEKLY GROWTH ----------
    from datetime import datetime, timedelta

    today = datetime.today().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_last_week = start_of_week - timedelta(days=7)
    end_of_last_week = start_of_week - timedelta(days=1)

    # This Week
    cursor.execute("""
        SELECT COUNT(*) FROM diary 
        WHERE user_id=%s 
        AND DATE(created_at) >= %s
    """, (session['user_id'], start_of_week))
    this_week_count = cursor.fetchone()[0]

    # Last Week
    cursor.execute("""
        SELECT COUNT(*) FROM diary 
        WHERE user_id=%s 
        AND DATE(created_at) BETWEEN %s AND %s
    """, (session['user_id'], start_of_last_week, end_of_last_week))
    last_week_count = cursor.fetchone()[0]

    weekly_growth = this_week_count - last_week_count


# ---------- INTENSITY ANALYTICS ----------
    cursor.execute("""
    SELECT intensity 
    FROM diary 
    WHERE user_id=%s
    """, (session['user_id'],))

    intensity_data = cursor.fetchall()
    intensity_values = [row[0] for row in intensity_data if row[0] is not None]

    average_intensity = 0
    intensity_level = "Low"
    high_spike_count = 0

    if intensity_values:
        average_intensity = round(sum(intensity_values) / len(intensity_values), 2)

    # Detect high spikes (>80%)
        high_spike_count = len([i for i in intensity_values if i > 80])

        if average_intensity > 75:
            intensity_level = "High Emotional Intensity"
        elif average_intensity > 50:
            intensity_level = "Moderate Emotional Intensity"
        else:
            intensity_level = "Low Emotional Intensity"
    
    
    # ---------- MOOD TREND PREDICTION ----------
    trend_message = "Not enough data to determine trend."

    cursor.execute("""
SELECT emotion
FROM diary
WHERE user_id=%s
ORDER BY created_at DESC
LIMIT 14
    """, (session['user_id'],))

    recent_entries = cursor.fetchall()

    if len(recent_entries) >= 7:

        last_7 = [row[0] for row in recent_entries[:7]]
        prev_7 = [row[0] for row in recent_entries[7:14]]

        def negative_ratio(emotions):
            if not emotions:
                return 0
            negative = emotions.count("Sad") + emotions.count("Angry")
            return negative / len(emotions)

        last_ratio = negative_ratio(last_7)
        prev_ratio = negative_ratio(prev_7)

        if last_ratio < prev_ratio:
            trend_message = "📈 Your mood trend is Improving."
        elif last_ratio > prev_ratio:
            trend_message = "📉 Your mood trend is Declining."
        else:
            trend_message = "➖ Your mood is Stable."

    # ---------- STREAK CALCULATION ----------
    from datetime import datetime, timedelta

    cursor.execute("""
    SELECT DATE(created_at)
    FROM diary
    WHERE user_id=%s
    ORDER BY created_at DESC
    """, (session['user_id'],))

    streak_dates = cursor.fetchall()

    streak = 0
    if streak_dates:
        unique_dates = sorted(set([row[0] for row in streak_dates]), reverse=True)

        today = datetime.today().date()
        current_day = today

        for date in unique_dates:
            if date == current_day:
                streak += 1
                current_day = current_day - timedelta(days=1)
            else:
                break
    
    
    # ---------- BADGE SYSTEM ----------
    badges = []

# Total entries count
    cursor.execute("""
    SELECT COUNT(*) 
    FROM diary 
    WHERE user_id=%s
    """, (session['user_id'],))
    total_entries = cursor.fetchone()[0]

# Streak badge
    if streak >= 7:
        badges.append("🔥 7-Day Streak Master")

# Consistency badge
    if total_entries >= 30:
        badges.append("🥇 Consistency Star (30+ Entries)")

# Positive Thinker badge
    cursor.execute("""
    SELECT COUNT(*) 
    FROM diary 
    WHERE user_id=%s AND emotion='Happy'
    """, (session['user_id'],))
    happy_count = cursor.fetchone()[0]

    if happy_count >= 10:
        badges.append("🌈 Positive Thinker")

# Strong Mind badge (average intensity < 50)
    if average_intensity < 50 and total_entries >= 10:
        badges.append("💪 Strong Emotional Balance")

# Explorer badge (used 4+ different emotions)
    cursor.execute("""
    SELECT COUNT(DISTINCT emotion)
    FROM diary
    WHERE user_id=%s
""", (session['user_id'],))
    emotion_variety = cursor.fetchone()[0]

    if emotion_variety >= 4:
        badges.append("🎭 Emotion Explorer")

# If no badge
    if not badges:
        badges.append("Keep writing to unlock badges!")
    
    
    
    # Split into last 7 and previous 7
        last_7 = recent_entries[:7]
        prev_7 = recent_entries[7:14]

        last_7_emotions = [row[0] for row in last_7]
        prev_7_emotions = [row[0] for row in prev_7]

        def negative_ratio(emotions):
            if not emotions:
                return 0
            negative = emotions.count("Sad") + emotions.count("Angry")
            return negative / len(emotions)

        last_ratio = negative_ratio(last_7_emotions)
        prev_ratio = negative_ratio(prev_7_emotions)

        if last_ratio < prev_ratio:
            trend_message = "📈 Your mood trend is Improving."
        elif last_ratio > prev_ratio:
            trend_message = "📉 Your mood trend is Declining."
        else:
            trend_message = "➖ Your mood is Stable."
    
    
# ---------- ADVANCED EMOTION INSIGHTS ----------
    insight_message = "No sufficient data to generate insights."
    risk_alert = None
    stability_score = 0
    health_index = 100
    emotion_distribution = {}

    total_entries = sum(counts) if counts else 0

    if total_entries > 0:
        emotion_distribution = dict(zip(emotions, counts))

    # Dominant emotion
        dominant_emotion = max(emotion_distribution, key=emotion_distribution.get)

    # Stability Score (how balanced emotions are)
        unique_emotions = len(emotion_distribution)
        stability_score = round((unique_emotions / 4) * 100, 2)

        insight_message = f"Your dominant emotion is {dominant_emotion}."

    # Risk detection
        negative_emotions = (
        emotion_distribution.get("Sad", 0) +
        emotion_distribution.get("Angry", 0)
        )

        negative_ratio = negative_emotions / total_entries

        if negative_ratio > 0.6:
            risk_alert = "⚠️ High negative emotion trend detected. Consider self-care."
        elif negative_ratio > 0.4:
            risk_alert = "⚠️ Moderate negative emotional pattern observed."
        else:
            risk_alert = "😊 Emotional balance looks healthy."

    # Emotional Health Index
        health_index = round((1 - negative_ratio) * 100, 2)

    # Weekly growth insight
        if weekly_growth > 0:
            insight_message += "You are journaling more this week 📈."
        elif weekly_growth < 0:
            insight_message += "Your journaling decreased this week 📉."
        else:
            insight_message += "Your journaling remained consistent."
            
    personalized_tip = advanced_recommendation(emotions, counts, weekly_growth)        
    # ---------- STREAK ----------
    current_streak, longest_streak = calculate_streak(session['user_id'])

    # ---------- EMOTION TIMELINE ----------
    cursor.execute("""
SELECT DATE(created_at), emotion, COUNT(*)
FROM diary
WHERE user_id=%s
GROUP BY DATE(created_at), emotion
ORDER BY DATE(created_at)
    """, (session['user_id'],))

    timeline_data = cursor.fetchall()

    timeline = {}

    for date, emotion, count in timeline_data:
        date = str(date)

        if date not in timeline:
            timeline[date] = {
            "Happy":0,
            "Sad":0,
            "Angry":0,
            "Fear":0,
            "Neutral":0
        }

        timeline[date][emotion] = count

    timeline_dates = list(timeline.keys())
    happy_counts = [timeline[d]["Happy"] for d in timeline_dates]
    sad_counts = [timeline[d]["Sad"] for d in timeline_dates]
    angry_counts = [timeline[d]["Angry"] for d in timeline_dates]
    fear_counts = [timeline[d]["Fear"] for d in timeline_dates]
    neutral_counts = [timeline[d]["Neutral"] for d in timeline_dates]
    
    
    # Mental Health Score
    cursor.execute("""
SELECT emotion FROM diary WHERE user_id=%s
    """, (session['user_id'],))

    emotion_rows = cursor.fetchall()
    emotion_list = [row[0] for row in emotion_rows]

    health_score = calculate_health_score(emotion_list)
    
    
    cursor.execute("""
    SELECT content FROM diary WHERE user_id=%s
    """, (session['user_id'],))

    entries = cursor.fetchall()
    text = " ".join([row[0] for row in entries])
    
    
    from collections import Counter

    words = re.findall(r'\b\w+\b', text.lower())
    filtered = [w for w in words if w not in stop_words]

    top_words = Counter(filtered).most_common(3)

    wordcloud_img = None

    if text:
        wc = WordCloud(width=800, height=400, background_color="white").generate(text)

        plt.figure(figsize=(6,3))
        plt.imshow(wc)
        plt.axis("off")

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)

        wordcloud_img = base64.b64encode(img.getvalue()).decode()
    
    cursor.close()
    db.close()

    return render_template(
    'dashboard.html',
    emotions=emotions,
    counts=counts,
    dates=dates,
    entries=entry_counts,
    heatmap_dict=heatmap_dict,
    current_streak=current_streak,
    longest_streak=longest_streak,
    this_week=this_week_count,
    last_week=last_week_count,
    weekly_growth=weekly_growth,
    insight_message=insight_message,
    badges=badges,
    trend_message=trend_message,
    risk_alert=risk_alert,
    average_intensity=average_intensity,
    intensity_level=intensity_level,
    high_spike_count=high_spike_count,
    stability_score=stability_score,
    personalized_tip=personalized_tip,
    health_index=health_index,
    timeline_dates=timeline_dates,
    top_words=top_words,
    happy_counts=happy_counts,
    sad_counts=sad_counts,
    angry_counts=angry_counts,
    fear_counts=fear_counts,
    neutral_counts=neutral_counts,
    health_score=health_score,
    wordcloud_img=wordcloud_img
    

)
    


# ---------- AI CHATBOT ----------
from flask import jsonify
import os


@app.route('/chat', methods=['GET'])
@login_required
def chat_page():
    chat_history = session.get("chat_history", [])
    return render_template("chat.html", chat_history=chat_history)


@app.route("/chatbot", methods=["POST"])
def chatbot():

    data = request.get_json()
    user_message = data.get("message", "")

    # Detect emotion using your ML model
    emotion, confidence, intensity = detect_emotion(user_message)

    # Emotion based replies
    replies = {
        "Happy": "😊 I'm glad you're feeling happy! Keep enjoying the moment.",
        "Sad": "😔 I'm sorry you're feeling sad. Writing your thoughts can help release emotions.",
        "Angry": "😠 It seems you're feeling angry. Try taking deep breaths or a short walk.",
        "Fear": "😟 Feeling worried is normal. Try to focus on what you can control.",
        "Neutral": "🙂 Thanks for sharing. Tell me more about how your day is going.",
        "Positive": "🌟 That's great to hear! Keep focusing on the positive things."
    }

    reply = replies.get(emotion, "I'm here to listen. Tell me more about how you're feeling.")

    return jsonify({
        "reply": reply,
        "emotion": emotion,
        "confidence": confidence
    })



# ---------- HISTORY ----------
@app.route('/history')
@login_required
def history():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM diary WHERE user_id=%s ORDER BY created_at DESC",
        (session['user_id'],)
    )

    diaries = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template('history.html', diaries=diaries)


# ---------- DOWNLOAD MONTHLY REPORT ----------
@app.route('/download_report')
@login_required
def download_report():

    db = get_db()
    cursor = db.cursor()

    current_month = datetime.now().month
    current_year = datetime.now().year

    # Emotion distribution
    cursor.execute("""
        SELECT emotion, COUNT(*)
        FROM diary
        WHERE user_id=%s AND MONTH(created_at)=%s AND YEAR(created_at)=%s
        GROUP BY emotion
    """, (session['user_id'], current_month, current_year))

    emotion_data = cursor.fetchall()

    # Total entries
    cursor.execute("""
        SELECT COUNT(*)
        FROM diary
        WHERE user_id=%s AND MONTH(created_at)=%s AND YEAR(created_at)=%s
    """, (session['user_id'], current_month, current_year))

    total_entries = cursor.fetchone()[0]

    # Get all emotions for health score
    cursor.execute("""
        SELECT emotion
        FROM diary
        WHERE user_id=%s AND MONTH(created_at)=%s AND YEAR(created_at)=%s
    """, (session['user_id'], current_month, current_year))

    emotion_rows = cursor.fetchall()
    emotions = [row[0] for row in emotion_rows]

    health_score = calculate_health_score(emotions)

    # Dominant emotion
    dominant_emotion = "None"
    if emotion_data:
        dominant_emotion = max(emotion_data, key=lambda x: x[1])[0]

    cursor.close()
    db.close()

    # ---------- PDF GENERATION ----------
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Monthly Mental Wellness Report", styles['Title']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"User: {session['user_name']}", styles['Normal']))
    elements.append(Paragraph(f"Month: {datetime.now().strftime('%B %Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Total Diary Entries: {total_entries}", styles['Heading3']))
    elements.append(Paragraph(f"Dominant Emotion: {dominant_emotion}", styles['Heading3']))
    elements.append(Paragraph(f"Mental Health Score: {health_score}/100", styles['Heading3']))

    elements.append(Spacer(1, 20))

    # Emotion Table
    if emotion_data:

        table_data = [["Emotion", "Count"]]

        for row in emotion_data:
            table_data.append([row[0], str(row[1])])

        table = Table(table_data)

        elements.append(Paragraph("Emotion Distribution", styles['Heading2']))
        elements.append(Spacer(1,10))
        elements.append(table)

    else:
        elements.append(Paragraph("No diary entries this month.", styles['Normal']))

    elements.append(Spacer(1, 20))

    # AI Wellness Message
    suggestion = "Continue journaling regularly to improve emotional awareness."

    if dominant_emotion == "Happy":
        suggestion = "Great emotional balance this month. Keep maintaining positive routines."
    elif dominant_emotion == "Sad":
        suggestion = "Consider relaxation activities or talking with supportive people."
    elif dominant_emotion == "Angry":
        suggestion = "Practice breathing exercises and stress management techniques."

    elements.append(Paragraph("AI Wellness Insight", styles['Heading2']))
    elements.append(Paragraph(suggestion, styles['Normal']))

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="Mental_Wellness_Report.pdf",
        mimetype='application/pdf'
    )

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged Out Successfully!", "info")
    return redirect(url_for('login'))

@app.route("/emotion-data")
@login_required
def emotion_data():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT DATE(created_at) as entry_date, emotion
        FROM diary
        WHERE user_id = %s
    """, (session['user_id'],))

    rows = cursor.fetchall()

    events = []

    for row in rows:
        events.append({
            "title": row["emotion"],
            "start": str(row["entry_date"])
        })

    cursor.close()
    db.close()

    return jsonify(events)

if __name__ == '__main__':
    app.run(debug=True)

