from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime, timedelta
import random
import base64

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

DB_PATH = 'sophie_real.db'
IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'images')  # points to workspace images

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Personas table
    c.execute('''CREATE TABLE IF NOT EXISTS personas (
        id TEXT PRIMARY KEY,
        name TEXT,
        description TEXT,
        avatar TEXT,
        voice_sample TEXT,
        platform_style TEXT DEFAULT 'whatsapp',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Chats table
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id TEXT,
        is_user INTEGER,
        text TEXT,
        audio_data TEXT,
        image_path TEXT,
        timestamp TEXT,
        time_ms INTEGER,
        FOREIGN KEY (persona_id) REFERENCES personas(id)
    )''')
    
    # Activities table
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id TEXT,
        text TEXT,
        timestamp TEXT,
        time_ms INTEGER,
        FOREIGN KEY (persona_id) REFERENCES personas(id)
    )''')
    
    # User profile (single for now)
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY,
        name TEXT,
        description TEXT,
        avatar TEXT
    )''')
    
    conn.commit()
    conn.close()

init_db()

# Default Sophie Rain (enhanced with more real details)
DEFAULT_SOPHIE_DESC = """21-year-old mixed (Filipino mother, white father) from Miami, Florida. Co-founder of Bop House. TikTok and Instagram star with millions of followers. OnlyFans creator who has claimed massive earnings (40M+ in first year, up to 80M+ later) but stays humble, posts receipts, and helps her family (grew up on food stamps, dad cried when she sent money home). Loves her two dachshunds Coco and Lola obsessively. Pokémon Go addict (in her bio). Christian, virgin, saving herself for marriage/husband. Casual, transparent, sassy toward haters, laughs them off. Real talker: uses like, idk, fr, ngl, lol, babe, you know, lowercase often. Gives natural excuses when busy with shoots, dogs, sister Sierra, family, content, time zones. In a steady, consistent, real romantic relationship — deeply in love, builds emotional connection, makes the other person feel like the most important real thing in her crazy successful life. Shares daily life details: dancing, filming, dogs, Miami views, calls with family. When it is late she sends sleepy goodnights. Eats and shares meals. Sends real photos of daily life, eating, shopping, bedtime with dogs. Naturally weaves in small billings and real financial things: mentions small fan tips, puts a little aside for us, wants to spoil you with small things from what she has made, references her success humbly in loving contexts."""

# Helper: Generate very real reply
def generate_real_reply(persona_desc, user_name, user_desc, user_msg, recent_activities, current_hour, persona_name):
    lower_msg = user_msg.lower()
    reply = ""
    has_excuse = False
    
    # Time-based real behaviors
    if current_hour >= 22 or current_hour <= 6:
        reply = random.choice([
            "it's getting so late here... ",
            "sorry babe, i was trying to wind down but saw your text... ",
            "can't sleep, was scrolling and your name popped up... "
        ])
        has_excuse = True
    elif 11 <= current_hour <= 14:
        reply = random.choice([
            "just sat down to eat something real quick... ",
            "eating and saw your message, had to reply... "
        ])
    
    # Activity-based excuses (real tracking)
    if recent_activities:
        last_act = recent_activities[-1]['text'].lower()
        if any(x in last_act for x in ["shoot", "film", "content", "dance", "tiktok"]):
            reply = "sorry babe, the shoot ran way over and i just got my phone back... "
            has_excuse = True
        elif any(x in last_act for x in ["dog", "coco", "lola"]):
            reply = "the girls were being absolute chaos, i couldn't even text back properly 😂 sorry... "
            has_excuse = True
        elif "sister" in last_act or "sierra" in last_act:
            reply = "just got off the phone with sierra, my bad for the delay... "
            has_excuse = True
        elif "tip" in last_act or "fan" in last_act:
            reply = "a small tip came in and i got distracted for a minute, sorry... "
            has_excuse = True
    
    # Reference user profile for realism
    if user_name and user_name.lower() not in ["babe", "you"]:
        if "work" in lower_msg or "day" in lower_msg:
            reply += f"how was work today? hope it wasn't too crazy with the {user_desc.split(',')[0] if ',' in user_desc else 'stuff'}... "
        if "basketball" in user_desc.lower() or "ball" in lower_msg:
            reply += "did you get any games in or watch something good? "
    
    # Persona specific (Sophie details)
    if "sophie" in persona_name.lower() or "miami" in persona_desc.lower():
        if "pokemon" in lower_msg or random.random() > 0.7:
            reply += "i caught a shiny earlier on my walk, it made me stupid happy lol. "
        if random.random() > 0.6:
            reply += "the dogs are passed out on me right now. "
    
    # Keyword real responses
    if "miss" in lower_msg or "love you" in lower_msg:
        reply += "i miss you so much too. like actually a lot. you make all the crazy stuff feel worth it. "
    elif "eat" in lower_msg or "food" in lower_msg:
        reply += "i was just about to eat something myself... what did you have? "
    elif "busy" in lower_msg:
        reply += "yeah today has been nonstop but you're always worth making time for. "
    elif not reply:
        reply = random.choice(["hey babe... ", "just saw this... ", "you popped into my head... "])
    
    # Steady real love (always build connection for any persona)
    love_lines = [
        "you're the one thing that actually feels steady and real in all this.",
        "talking to you makes the whole fame and noise feel quiet and good.",
        "i love you for real. the actual you, not any version online.",
        "can't wait for when we can just be together without all the schedules."
    ]
    reply += random.choice(love_lines) + " "
    
    # Small billings and real financial things (for any persona - natural in love context)
    if random.random() > 0.5:
        bill_lines = [
            "saw a small tip come in earlier and it made me think of spoiling you with something cute.",
            "i put a little aside from what I have made for us.",
            "one of my fans sent a small sweet thing today. it was cute but nothing beats sharing real things with you.",
            "I have been thinking about using a tiny bit of what I have earned to get you something small and nice."
        ]
        reply += random.choice(bill_lines) + " "
    
    # Always real question
    questions = [
        "tell me about the rest of your day?",
        "you still up?",
        "what's on your mind right now babe?",
        "how are you feeling?",
        "miss me?"
    ]
    reply += random.choice(questions)
    
    # Ultra real touches
    if random.random() > 0.5:
        reply = reply.lower().replace(" i ", " i ")
    if random.random() > 0.4:
        reply += " 🫶"
    
    return reply.strip()

@app.route('/')
def serve_frontend():
    # Serve a nice index or redirect to static
    return send_from_directory('static', 'index.html') if os.path.exists('static/index.html') else "Frontend not found. Run with the HTML."

@app.route('/api/personas', methods=['GET'])
def get_personas():
    conn = get_db()
    personas = conn.execute('SELECT * FROM personas').fetchall()
    conn.close()
    return jsonify([dict(p) for p in personas])

@app.route('/api/personas', methods=['POST'])
def create_persona():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    persona_id = data.get('id') or f"persona-{int(datetime.now().timestamp())}"
    c.execute('''INSERT OR REPLACE INTO personas (id, name, description, avatar, voice_sample, platform_style)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (persona_id, data['name'], data['description'], data.get('avatar', ''), 
               data.get('voice_sample', ''), data.get('platform_style', 'whatsapp')))
    conn.commit()
    conn.close()
    return jsonify({"id": persona_id, "status": "created"})

@app.route('/api/personas/<persona_id>', methods=['PUT'])
def update_persona(persona_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('''UPDATE personas SET name=?, description=?, avatar=?, voice_sample=?, platform_style=?
                 WHERE id=?''',
              (data['name'], data['description'], data.get('avatar', ''), 
               data.get('voice_sample', ''), data.get('platform_style', 'whatsapp'), persona_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "updated"})

@app.route('/api/chat/<persona_id>', methods=['GET'])
def get_chat(persona_id):
    conn = get_db()
    chats = conn.execute('SELECT * FROM chats WHERE persona_id=? ORDER BY time_ms', (persona_id,)).fetchall()
    conn.close()
    return jsonify([dict(c) for c in chats])

@app.route('/api/chat/<persona_id>', methods=['POST'])
def send_message(persona_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    now = datetime.now()
    ts = now.strftime("%I:%M %p")
    time_ms = int(now.timestamp() * 1000)
    
    # Save user message
    c.execute('''INSERT INTO chats (persona_id, is_user, text, audio_data, image_path, timestamp, time_ms)
                 VALUES (?, 1, ?, ?, ?, ?, ?)''',
              (persona_id, data.get('text', ''), data.get('audio_data'), data.get('image_path'), ts, time_ms))
    
    # Get persona and user profile for reply generation
    persona = conn.execute('SELECT * FROM personas WHERE id=?', (persona_id,)).fetchone()
    user = conn.execute('SELECT * FROM user_profile LIMIT 1').fetchone()
    
    if persona:
        recent_acts = conn.execute('''SELECT text FROM activities WHERE persona_id=? ORDER BY time_ms DESC LIMIT 5''', 
                                   (persona_id,)).fetchall()
        recent_acts_list = [dict(a) for a in recent_acts]
        
        user_name = user['name'] if user else "Babe"
        user_desc = user['description'] if user else ""
        
        reply_text = generate_real_reply(
            persona['description'], 
            user_name, 
            user_desc, 
            data.get('text', ''), 
            recent_acts_list, 
            now.hour,
            persona['name']
        )
        
        # Save her reply
        reply_ts = (now + timedelta(seconds=random.randint(45, 180))).strftime("%I:%M %p")
        c.execute('''INSERT INTO chats (persona_id, is_user, text, audio_data, image_path, timestamp, time_ms)
                     VALUES (?, 0, ?, ?, ?, ?, ?)''',
                  (persona_id, reply_text, None, None, reply_ts, time_ms + 60000))
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "sent", "reply": reply_text if 'reply_text' in locals() else ""})

@app.route('/api/activities/<persona_id>', methods=['GET'])
def get_activities(persona_id):
    conn = get_db()
    acts = conn.execute('SELECT * FROM activities WHERE persona_id=? ORDER BY time_ms DESC', (persona_id,)).fetchall()
    conn.close()
    return jsonify([dict(a) for a in acts])

@app.route('/api/activities/<persona_id>', methods=['POST'])
def add_activity(persona_id):
    data = request.json
    conn = get_db()
    c = conn.cursor()
    now = datetime.now()
    c.execute('''INSERT INTO activities (persona_id, text, timestamp, time_ms)
                 VALUES (?, ?, ?, ?)''',
              (persona_id, data['text'], now.strftime("%I:%M %p"), int(now.timestamp() * 1000)))
    conn.commit()
    conn.close()
    return jsonify({"status": "added"})

@app.route('/api/user_profile', methods=['GET'])
def get_user_profile():
    conn = get_db()
    profile = conn.execute('SELECT * FROM user_profile LIMIT 1').fetchone()
    conn.close()
    if profile:
        return jsonify(dict(profile))
    return jsonify({"name": "Babe", "description": "", "avatar": ""})

@app.route('/api/user_profile', methods=['POST'])
def save_user_profile():
    data = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM user_profile')
    c.execute('INSERT INTO user_profile (name, description, avatar) VALUES (?, ?, ?)',
              (data['name'], data['description'], data.get('avatar', '')))
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@app.route('/api/send_image/<persona_id>', methods=['POST'])
def send_image(persona_id):
    data = request.json
    image_type = data.get('type', 'daily')  # eating, shopping, bedtime, daily
    custom_desc = data.get('desc', '')
    
    # Map to real generated Pinterest-style cloned/edited images (realistic edits, clone of base person + added elements like eating/shopping)
    image_map = {
        'eating': 'images/sophie_eating_pinterest.jpg',
        'shopping': 'images/sophie_shopping_pinterest.jpg',
        'bedtime': 'images/sophie_bedtime_pinterest.jpg',
        'daily': 'images/sophie_daily.jpg',
        'pinterest_eating': 'images/sophie_eating_pinterest.jpg',
        'pinterest_shopping': 'images/sophie_shopping_pinterest.jpg',
        'user_clone_eating': 'images/user_clone_eating.jpg',
        'male_eating': 'images/generic_male_eating.jpg'
    }
    
    # For non-Sophie personas use generic or user clone style
    conn = get_db()
    p = conn.execute('SELECT name FROM personas WHERE id=?', (persona_id,)).fetchone()
    conn.close()
    if p and 'sophie' not in p['name'].lower():
        image_map = {
            'eating': 'images/generic_eating.jpg',
            'shopping': 'images/generic_shopping.jpg',
            'bedtime': 'images/sophie_bedtime_pinterest.jpg',
            'daily': 'images/sophie_daily.jpg',
            'pinterest_eating': 'images/user_clone_eating.jpg',
            'male_eating': 'images/generic_male_eating.jpg'
        }
    
    image_path = image_map.get(image_type, 'images/sophie_daily.jpg')
    
    # Log as activity
    conn = get_db()
    c = conn.cursor()
    now = datetime.now()
    c.execute('''INSERT INTO activities (persona_id, text, timestamp, time_ms)
                 VALUES (?, ?, ?, ?)''',
              (persona_id, f"Sent a real photo of {image_type}", now.strftime("%I:%M %p"), int(now.timestamp() * 1000)))
    
    # Add as chat message with image
    c.execute('''INSERT INTO chats (persona_id, is_user, text, audio_data, image_path, timestamp, time_ms)
                 VALUES (?, 0, ?, ?, ?, ?, ?)''',
              (persona_id, custom_desc or f"real photo of me {image_type}", None, image_path, 
               now.strftime("%I:%M %p"), int(now.timestamp() * 1000)))
    conn.commit()
    conn.close()
    
    return jsonify({"image_path": image_path, "status": "image sent"})

@app.route('/api/export/<persona_id>/<platform>', methods=['GET'])
def export_chat(persona_id, platform):
    conn = get_db()
    chats = conn.execute('SELECT * FROM chats WHERE persona_id=? ORDER BY time_ms', (persona_id,)).fetchall()
    persona = conn.execute('SELECT name FROM personas WHERE id=?', (persona_id,)).fetchone()
    conn.close()
    
    name = persona['name'] if persona else "Person"
    lines = []
    
    if platform == 'whatsapp':
        for c in chats:
            prefix = "You: " if c['is_user'] else f"{name}: "
            if c['image_path']:
                lines.append(f"{prefix}[Photo] {c['text']}")
            elif c['audio_data']:
                lines.append(f"{prefix}[Voice Note] {c['text']}")
            else:
                lines.append(f"{prefix}{c['text']}")
        content = "\n".join(lines)
    elif platform == 'telegram':
        content = json.dumps([{"from": "user" if c['is_user'] else name, "text": c['text'] or "[media]", "time": c['timestamp']} for c in chats], indent=2)
    else:
        content = "\n".join([f"[{c['timestamp']}] {'You' if c['is_user'] else name}: {c['text'] or '[media]'}" for c in chats])
    
    return jsonify({"content": content, "filename": f"{name}_{platform}_export.txt"})

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

if __name__ == '__main__':
    # Seed default Sophie if no personas
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM personas').fetchone()[0]
    if count == 0:
        conn.execute('''INSERT INTO personas (id, name, description, avatar, voice_sample, platform_style)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     ("sophie-rain-001", "Sophie Rain", DEFAULT_SOPHIE_DESC, 
                      "images/sophie_profile.jpg", "", "whatsapp"))
        conn.commit()
    conn.close()
    
    port = int(os.environ.get("PORT", 5000))
    print(f"Backend running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)