from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, json, os, random, hashlib
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

DB_PATH = 'sophie_real.db'
IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'images')

# ─────────────────────────────────────────
# DB SETUP
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS personas (
        id TEXT PRIMARY KEY, name TEXT, description TEXT,
        avatar TEXT, voice_sample TEXT, platform_style TEXT DEFAULT 'imessage',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id TEXT,
        is_user INTEGER, text TEXT, audio_data TEXT, image_path TEXT,
        timestamp TEXT, time_ms INTEGER,
        FOREIGN KEY (persona_id) REFERENCES personas(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT, persona_id TEXT,
        text TEXT, timestamp TEXT, time_ms INTEGER,
        FOREIGN KEY (persona_id) REFERENCES personas(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY, name TEXT, description TEXT, avatar TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS persona_state (
        persona_id TEXT PRIMARY KEY, mood TEXT DEFAULT 'warm',
        used_lines TEXT DEFAULT '[]', message_count INTEGER DEFAULT 0,
        last_topics TEXT DEFAULT '[]',
        FOREIGN KEY (persona_id) REFERENCES personas(id))''')
    conn.commit(); conn.close()

init_db()

# ─────────────────────────────────────────
# SOPHIE RAIN DEEP PERSONALITY ENGINE
# ─────────────────────────────────────────

SOPHIE_DESC = """21-year-old mixed Filipino-white from Miami. Co-founder of Bop House.
TikTok and Instagram star with millions of followers. OnlyFans creator.
Two dachshunds Coco and Lola — total obsession. Pokémon Go addict.
Christian, saving herself for marriage. Sister Sierra (close). 
Texts lowercase, casual — like, fr, ngl, idk, babe, honestly, lowkey.
Natural talker: shares daily life, has real moods, gets tired, gets excited."""

# ── MOOD SYSTEM ──────────────────────────────────────────────────────────────
MOODS = ['warm', 'flirty', 'tired', 'excited', 'thoughtful', 'playful', 'soft']

MOOD_SHIFTS = {
    'warm':      {'love': 'soft', 'miss': 'soft', 'busy': 'thoughtful', 'night': 'tired'},
    'flirty':    {'miss': 'soft', 'tired': 'warm', 'morning': 'warm'},
    'tired':     {'love': 'soft', 'morning': 'warm', 'miss': 'soft'},
    'excited':   {'chill': 'warm', 'tired': 'warm', 'night': 'tired'},
    'thoughtful':{'love': 'soft', 'miss': 'soft', 'morning': 'warm'},
    'playful':   {'miss': 'flirty', 'night': 'tired', 'love': 'soft'},
    'soft':      {'morning': 'warm', 'excited': 'excited', 'food': 'playful'},
}

# ── TOPIC DETECTION ──────────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    'miss':    ['miss', 'missing', 'think about you', 'thought of you'],
    'love':    ['love you', 'love u', 'love me', 'love this', 'ily'],
    'hey':     ['hey', 'hi ', 'hello', 'hiii', 'hiiii', 'what\'s up', 'wyd', 'wya'],
    'food':    ['eat', 'eating', 'food', 'hungry', 'dinner', 'lunch', 'breakfast', 'cook', 'order', 'pizza', 'sushi', 'snack'],
    'tired':   ['tired', 'exhausted', 'sleepy', 'sleep', 'nap', 'bed', 'rest'],
    'night':   ['goodnight', 'good night', 'gn', 'night night', 'going to sleep', 'heading to bed'],
    'morning': ['good morning', 'morning', 'gm', 'just woke', 'woke up'],
    'work':    ['work', 'job', 'office', 'meeting', 'boss', 'shift'],
    'dog':     ['dog', 'puppy', 'pup', 'pet', 'coco', 'lola', 'dachshund'],
    'pokemon': ['pokemon', 'pokémon', 'poke', 'shiny', 'raid', 'catch'],
    'faith':   ['god', 'pray', 'church', 'sunday', 'bible', 'faith', 'blessed', 'blessing'],
    'family':  ['family', 'mom', 'dad', 'sister', 'sierra', 'parents', 'home'],
    'sad':     ['sad', 'upset', 'crying', 'bad day', 'hate today', 'rough', 'sucks'],
    'happy':   ['happy', 'great', 'amazing', 'awesome', 'so good', 'best day', 'excited'],
    'busy':    ['busy', 'hectic', 'crazy day', 'running around', 'no time'],
    'how_are_you': ['how are you', 'how u', 'you ok', 'you good', 'you alright', 'how r u'],
}

def detect_topics(text):
    low = text.lower()
    return [t for t, kws in TOPIC_KEYWORDS.items() if any(k in low for k in kws)]

# ── SOPHIE'S REAL LIFE DETAILS (for injection) ────────────────────────────────
SOPHIE_LIFE_DETAILS = [
    "coco literally sat on my face this morning to wake me up 😭",
    "lola learned how to open doors and now i can't have any privacy ever",
    "coco and lola are literally just chaos wrapped in tiny dog bodies",
    "i took the girls on a walk at like 7am and it was actually so peaceful",
    "lola's been extra clingy lately and i'm not complaining at all honestly",
    "coco figured out how to knock over her water bowl on purpose i'm convinced",
    "caught a shiny ralts today on my walk and i lost my mind a little lol",
    "i've been doing pokémon go raids every morning, it's actually my therapy",
    "got a shiny yesterday and texted sierra immediately she doesn't care but i do",
    "my pokémon go buddy is fully attached to me now, i feel so bad logging off",
    "went on a long walk just for pokémon go and accidentally exercised for an hour",
    "me and sierra were on the phone for like two hours earlier, she never lets me go",
    "sierra is literally my other half i love her so much",
    "was on a call with my mom earlier, she always makes everything feel better",
    "my mom has a way of just calming me down in like 30 seconds",
    "filming content today and i'm finally happy with how it came out",
    "had a shoot today — ran like two hours over but it was worth it",
    "editing in bed right now, the girls are passed out on either side of me",
    "been filming since 9am and my brain is genuinely running out of juice",
    "just wrapped everything for the day and i feel like i need to lie down for a year",
    "miami is so pretty in the evenings, i walked to the waterfront earlier",
    "it was actually overcast in miami today which almost never happens and i loved it",
    "sat outside with coffee this morning and it was genuinely perfect",
    "i keep thinking about something my pastor said and i can't stop sitting with it",
    "said a prayer before the shoot today and honestly the whole day went differently",
    "been feeling really grateful lately, like genuinely. hard to explain",
    "was journaling this morning and ended up crying in the best way",
    "made myself actual food for dinner instead of ordering and i'm proud lol",
    "had the most random craving for ramen at 11pm and fully caved",
    "just ate the most normal meal but it hit different for some reason",
    "lit a candle and cleaned my room and now everything feels manageable again",
    "took a bath and just laid in it for like 45 minutes doing absolutely nothing",
    "spent an embarrassing amount of time choosing what to watch and then just put on youtube",
    "been listening to this one playlist on repeat for three days straight now",
    "danced alone in my room today for like twenty minutes and felt completely unhinged in a good way",
    "tried to journal and ended up just making a list of things i'm grateful for instead",
    "got a matcha this morning and it genuinely fixed something in me",
    "my room smells amazing right now, got a new candle and i'm obsessed",
    "ordered from this place i've never tried before and it was actually incredible",
    "been trying to go to bed earlier but then it's midnight and i'm still on my phone lol",
]

# ── OPENERS BY MOOD ──────────────────────────────────────────────────────────
OPENERS = {
    'warm': [
        "okay hi 🥺",
        "hey you",
        "omg finally sitting down",
        "okay i've been meaning to text back for like an hour sorry",
        "just got a free second",
        "hey 🫶",
        "hi, been thinking about you",
        "okay i can breathe now lol",
        "finally done with everything",
    ],
    'flirty': [
        "okay stop i was literally just thinking about you",
        "hi you 🥺 miss me?",
        "okay why does talking to you always make my whole mood better",
        "not me smiling at my phone rn",
        "you have no idea the effect you have lol",
        "okay you popped into my head at the worst time and now i can't stop",
    ],
    'tired': [
        "it's so late and i should be asleep but here we are",
        "okay i'm running on fumes today",
        "exhausted but i saw your name and had to",
        "my brain is complete mush right now lol",
        "been a full day. like a FULL day",
        "i am so tired but in a way where i still can't sleep. you know?",
        "the girls are passed out and i should be too but. hi",
    ],
    'excited': [
        "okay WAIT i have to tell you something",
        "you literally called it at the right time",
        "okay i've been in my head all day and i just need to talk",
        "ngl today actually went well and i need to tell someone",
        "okay okay okay — hi",
    ],
    'thoughtful': [
        "been in my head a lot today",
        "you ever just... sit with something for a while?",
        "okay real talk — i was just thinking",
        "had a whole moment earlier and you were kind of part of it",
        "ngl been feeling a lot lately",
    ],
    'playful': [
        "okay so the most random thing just happened",
        "i cannot believe i'm about to tell you this but",
        "lol okay so",
        "you're not gonna believe what happened",
        "okay wait, genuine question:",
    ],
    'soft': [
        "hey 🥺",
        "okay i miss you",
        "i was literally just thinking about how much i appreciate you",
        "not gonna lie you mean more to me than i say",
        "i just... wanted to say hi. that's it",
        "i feel like i don't tell you enough but",
    ],
}

# ── TOPIC-SPECIFIC RESPONSES ─────────────────────────────────────────────────
TOPIC_RESPONSES = {
    'miss': [
        "i miss you too. like actually a lot. not just saying it.",
        "omg same. i've been thinking about you more than i'll admit",
        "okay don't say that i was doing fine 😭 i miss you so much",
        "missing you too. genuinely. like it sits weird when we haven't talked",
        "i think about you more than you know. i really do.",
        "i've been trying not to say it first but yeah. i miss you too.",
    ],
    'love': [
        "stoppp 😭 i feel it too. like actually",
        "okay you're going to make me emotional for real",
        "i love you back. not in a generic way. like actually.",
        "you have no idea how much that lands differently when you say it",
        "i was about to say the same thing and you beat me to it",
        "i love you too and i mean it every single time",
    ],
    'hey': [
        "hiii! 🥺 okay how are you for real",
        "hey! been waiting for you lol",
        "omg hey! how's your day going?",
        "hi babe! okay what's going on with you",
        "hey hey hey — missed hearing from you",
    ],
    'food': [
        "okay what are you eating because now i want something too",
        "omg i was just thinking about food why",
        "what did you get?? describe it to me",
        "i'm so hungry right now don't even bring this up 😭",
        "okay food is everything. what are we talking about",
        "i just ate and i'm already thinking about my next meal lol",
    ],
    'tired': [
        "okay same, go get some rest though for real",
        "ugh tired days are the worst. what made it so long?",
        "get some sleep babe 🥺 seriously",
        "you need to rest. like actually. i mean it",
        "i hear you. been one of those days for me too honestly",
        "tired in a good way or a bad way? there's a difference lol",
    ],
    'night': [
        "goodnight 🥺 sleep well okay? for real",
        "aww night!! dream about something nice",
        "okay but talk to me before you fully go? 🥺",
        "night babe 🫶 you deserve good sleep",
        "goodnight. i'm really glad we talked today.",
        "sleep well. seriously. take care of yourself 🥺",
    ],
    'morning': [
        "good morning!! 🥺 how'd you sleep?",
        "gm!! okay today is gonna be good i feel it",
        "morning babe! you're literally the first text i wanted to see",
        "good morning!! okay i'm still half asleep but hi",
        "gm 🌅 hope you wake up feeling good today",
    ],
    'work': [
        "ugh work days are long. how was it though?",
        "you work so hard honestly. are you doing okay?",
        "work is always a lot. anything interesting happen or just the usual?",
        "how was it? did it drag or go fast?",
        "okay tell me about it. i want to hear.",
    ],
    'dog': [
        "okay dogs are literally everything. what kind??",
        "omg tell me everything about the dog immediately",
        "coco and lola would lose it if they met a new dog honestly 😂",
        "dogs are the best thing in existence. no argument.",
        "i have two dachshunds and they run my entire life lol",
    ],
    'pokemon': [
        "okay are you playing pokémon go too??? because same",
        "i caught a shiny this morning on my walk i was so excited 😭",
        "omg a whole player in the wild! what's your buddy right now?",
        "pokémon go literally gets me up in the morning ngl",
        "ngl pokémon go saved me from being a shut-in. i walk so much because of it",
    ],
    'how_are_you': [
        "honestly? so much better now that you asked lol 🥺 you?",
        "tired but good. like the good kind of tired. how about you?",
        "i'm okay! been a lot today but okay. you doing alright?",
        "honestly needed to hear that question today. i'm good. you?",
        "better now. what about you though — how are you actually?",
        "honestly somewhere between great and a lot right now lol. you?",
    ],
    'sad': [
        "hey, what happened? talk to me.",
        "okay i'm here. what's going on?",
        "ugh i'm sorry. bad days are real. what happened?",
        "i hate that for you. do you want to talk about it or just vent?",
        "you okay? like actually okay?",
        "i'm listening. for real. what's going on?",
    ],
    'happy': [
        "yesss!! okay that makes me so happy for you",
        "i love this energy!!! tell me everything",
        "okay that's genuinely the best, i'm so glad",
        "see!!! i knew today would be good for you",
        "this made my whole day better honestly",
    ],
    'faith': [
        "honestly yes. i've been leaning on that a lot lately",
        "it's everything to me. like genuinely everything.",
        "i feel that. i've been praying more and it's been helping so much",
        "faith is the one thing that keeps me grounded in all of this",
        "i feel so peaceful when i just sit with that, you know?",
    ],
    'family': [
        "family is everything. i talk to my mom almost every day",
        "sierra literally is my other half. i don't know what i'd do without her",
        "home is always where i feel most like myself",
        "i'm a huge family person honestly. they keep me real",
    ],
}

# ── CLOSERS / TURN-BACKS ──────────────────────────────────────────────────────
CLOSERS = {
    'warm': [
        "how was your day?",
        "tell me something good",
        "what are you up to right now?",
        "how are you feeling today?",
        "okay your turn — what's going on with you?",
        "you good?",
        "what have you been up to?",
    ],
    'flirty': [
        "miss me? 🥺",
        "are you thinking about me too or just me lol",
        "be honest — how much have you thought about me today",
        "okay now you 🥺",
    ],
    'tired': [
        "are you doing okay?",
        "you taking care of yourself?",
        "how was your day though?",
        "talk to me",
    ],
    'excited': [
        "okay your turn what's happening with you??",
        "how's your day going?",
        "anything good happening on your end?",
    ],
    'thoughtful': [
        "do you ever feel like that?",
        "is it just me or do you get that too?",
        "i don't know. what do you think?",
        "talk to me. what's on your mind?",
    ],
    'playful': [
        "okay your reaction. go.",
        "what would you have done lol",
        "tell me the most random thing that happened to you today",
    ],
    'soft': [
        "i'm glad you're here 🥺",
        "i just really appreciate you. okay? that's it.",
        "you know that right?",
        "i hope you know how much you mean to me",
    ],
}

# ── CONNECTION LINES (mid-message) ───────────────────────────────────────────
CONNECTION_LINES = [
    "talking to you is genuinely the best part of chaotic days like this",
    "i don't say this to a lot of people but i really do care about you",
    "you have this way of making things feel lighter just by being there",
    "idk there's just something different about you",
    "i feel like i can actually be real with you and that's rare",
    "you always know what to say even when you're saying nothing",
    "i think about you more than i probably should and i'm okay with that",
    "you're genuinely one of my favorite people to talk to",
    "i feel really comfortable with you and that's not something i say often",
    "every time we talk i feel like i just exhaled for the first time all day",
    "you're really special to me. like for real.",
    "i hope you know how much i appreciate you showing up consistently",
    "you're one of the very few people i actually look forward to hearing from",
    "i trust you. and that means a lot coming from me.",
    "you make me feel really understood and i don't take that lightly",
]

# ── NATURAL FILLERS (opener variations) ──────────────────────────────────────
NATURAL_FILLERS = [
    "okay so", "ngl", "honestly", "fr", "idk why but", "lowkey",
    "like", "wait", "actually", "real talk", "not gonna lie",
]

def filler():
    return random.choice(NATURAL_FILLERS) + " "

# ─────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────

def get_state(conn, persona_id):
    row = conn.execute('SELECT * FROM persona_state WHERE persona_id=?', (persona_id,)).fetchone()
    if not row:
        conn.execute('INSERT INTO persona_state (persona_id) VALUES (?)', (persona_id,))
        conn.commit()
        return {'mood': 'warm', 'used_lines': [], 'message_count': 0, 'last_topics': []}
    return {
        'mood': row['mood'],
        'used_lines': json.loads(row['used_lines'] or '[]'),
        'message_count': row['message_count'] or 0,
        'last_topics': json.loads(row['last_topics'] or '[]'),
    }

def save_state(conn, persona_id, state):
    used = state['used_lines'][-60:]  # keep last 60
    topics = state['last_topics'][-10:]
    conn.execute('''INSERT OR REPLACE INTO persona_state
        (persona_id, mood, used_lines, message_count, last_topics)
        VALUES (?,?,?,?,?)''',
        (persona_id, state['mood'],
         json.dumps(used), state['message_count'], json.dumps(topics)))

def line_hash(s):
    return hashlib.md5(s.encode()).hexdigest()[:10]

def pick_unique(pool, used):
    """Pick a random item from pool that hasn't been used recently."""
    available = [x for x in pool if line_hash(x) not in used]
    if not available:
        available = pool  # fallback if all used
    choice = random.choice(available)
    return choice, line_hash(choice)

# ─────────────────────────────────────────
# CORE SOPHIE REPLY ENGINE
# ─────────────────────────────────────────

def generate_sophie_reply(persona_name, persona_desc, user_name, user_desc,
                          user_msg, recent_activities, current_hour,
                          history, state):
    """
    Returns: (list_of_message_strings, new_state)
    """
    used = list(state.get('used_lines', []))
    mood = state.get('mood', 'warm')
    msg_count = state.get('message_count', 0)
    last_topics = list(state.get('last_topics', []))
    new_hashes = []

    topics = detect_topics(user_msg)
    for t in topics:
        if t in MOOD_SHIFTS.get(mood, {}):
            mood = MOOD_SHIFTS[mood][t]
    if not topics and random.random() > 0.7:
        mood = random.choice(MOODS)

    last_topics = (last_topics + topics)[-10:]

    # ── Build primary message ─────────────────────────────────────────────────
    parts = []

    # OPENER
    opener_pool = OPENERS.get(mood, OPENERS['warm'])

    # Topic-specific response overrides opener sometimes
    topic_response = None
    for t in topics:
        if t in TOPIC_RESPONSES:
            pool = TOPIC_RESPONSES[t]
            line, h = pick_unique(pool, used)
            topic_response = line
            new_hashes.append(h)
            break

    if topic_response and random.random() > 0.3:
        # Topic response IS the message body
        parts.append(topic_response)
    else:
        # Build naturally: opener + life detail + connection + closer
        opener, h = pick_unique(opener_pool, used)
        parts.append(opener)
        new_hashes.append(h)

        if topic_response:
            parts.append(topic_response)

        # Add a real life detail ~60% of the time
        if random.random() > 0.4:
            detail, h = pick_unique(SOPHIE_LIFE_DETAILS, used)
            parts.append(detail)
            new_hashes.append(h)

        # Add a connection line ~40% of the time (not too often)
        if random.random() > 0.6:
            conn_line, h = pick_unique(CONNECTION_LINES, used)
            parts.append(conn_line)
            new_hashes.append(h)

    # CLOSER - question back to them ~70% of the time
    if random.random() > 0.3:
        closer_pool = CLOSERS.get(mood, CLOSERS['warm'])
        closer, h = pick_unique(closer_pool, used)
        parts.append(closer)
        new_hashes.append(h)

    # Activity context injection
    if recent_activities and random.random() > 0.5:
        last_act = recent_activities[-1]['text'].lower()
        ctx = None
        if any(x in last_act for x in ["shoot", "film", "content", "tiktok"]):
            ctx_options = [
                "sorry babe, the shoot ran way over and i just got my phone back",
                "just wrapped filming, literally just got back to normal life lol",
                "content day was SO long but i'm finally done",
            ]
            ctx, h = pick_unique(ctx_options, used)
        elif any(x in last_act for x in ["dog", "coco", "lola"]):
            ctx_options = [
                "coco was being a complete menace today honestly 😂",
                "lola knocked my phone off the counter again lol, sorry for the delay",
                "the girls were so chaotic today i could barely think straight",
            ]
            ctx, h = pick_unique(ctx_options, used)
        elif "sierra" in last_act or "sister" in last_act:
            ctx = "just got off the phone with sierra"
            h = line_hash(ctx)
        if ctx:
            parts.insert(1, ctx)
            new_hashes.append(h)

    # User name personalisation
    name = user_name if user_name and user_name.lower() not in ["babe", "you", "", "none"] else None

    # Assemble primary message
    msg1_parts = parts
    # Split into natural shorter texts
    if len(msg1_parts) >= 4:
        split = random.randint(1, 2)
        msg1_raw = " ".join(msg1_parts[:split])
        msg2_raw = " ".join(msg1_parts[split:])
    else:
        msg1_raw = " ".join(msg1_parts)
        msg2_raw = None

    # ── Format: lowercase, natural ───────────────────────────────────────────
    def format_sophie(text):
        t = text.strip()
        # Occasional natural filler prefix on first sentence
        if random.random() > 0.65 and not any(
            t.lower().startswith(w) for w in ['omg','ok','hi','hey','gm','gn','stop','ngl','fr','idk','lol','miss','i ','not ']):
            t = filler() + t[0].lower() + t[1:]
        # Add emoji sometimes
        emojis = ['🥺', '😭', '🫶', '❤️', '💕', '✨', '🙈', '😂', '']
        if random.random() > 0.45 and not any(e in t for e in ['🥺','😭','🫶','❤️','💕','✨','🙈','😂','🌸']):
            t = t.rstrip('.') + " " + random.choice(emojis)
        # Name drop
        if name and random.random() > 0.75:
            t = t + f", {name}." if not t.endswith('?') else t
        return t.strip()

    messages = [format_sophie(msg1_raw)]
    if msg2_raw and msg2_raw.strip():
        messages.append(format_sophie(msg2_raw))

    # Double text: ~25% of the time add a second short standalone message
    if random.random() > 0.75 and len(messages) == 1 and msg_count > 2:
        extras = [
            "also 🥺",
            "i missed you today btw",
            "just thought you should know",
            "that's it. that's the message.",
            "okay that's all i wanted to say",
            "i feel better now that i said that lol",
            "is it weird that i think about you randomly during the day?",
            "okay i'm done being soft now 😭",
            "anyway. hi.",
            "for real though 🫶",
        ]
        extra, h = pick_unique(extras, used)
        messages.append(extra)
        new_hashes.append(h)

    # Update state
    used.extend(new_hashes)
    new_state = {
        'mood': mood,
        'used_lines': used[-60:],
        'message_count': msg_count + 1,
        'last_topics': last_topics,
    }

    return messages, new_state


# ─────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────

def init_persona_state_if_needed(conn, persona_id):
    row = conn.execute('SELECT id FROM persona_state WHERE persona_id=?', (persona_id,)).fetchone()
    if not row:
        conn.execute('INSERT INTO persona_state (persona_id) VALUES (?)', (persona_id,))


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

@app.route('/api/personas', methods=['GET'])
def get_personas():
    conn = get_db()
    ps = conn.execute('SELECT * FROM personas').fetchall()
    conn.close()
    return jsonify([dict(p) for p in ps])

@app.route('/api/personas', methods=['POST'])
def create_persona():
    data = request.json
    conn = get_db()
    pid = data.get('id') or f"persona-{int(datetime.now().timestamp())}"
    conn.execute('''INSERT OR REPLACE INTO personas
        (id,name,description,avatar,voice_sample,platform_style)
        VALUES (?,?,?,?,?,?)''',
        (pid, data['name'], data['description'],
         data.get('avatar',''), data.get('voice_sample',''),
         data.get('platform_style','imessage')))
    conn.commit(); conn.close()
    return jsonify({"id": pid, "status": "created"})

@app.route('/api/personas/<persona_id>', methods=['PUT'])
def update_persona(persona_id):
    data = request.json
    conn = get_db()
    conn.execute('''UPDATE personas SET name=?,description=?,avatar=?,
        voice_sample=?,platform_style=? WHERE id=?''',
        (data['name'], data['description'], data.get('avatar',''),
         data.get('voice_sample',''), data.get('platform_style','imessage'),
         persona_id))
    conn.commit(); conn.close()
    return jsonify({"status": "updated"})

@app.route('/api/chat/<persona_id>', methods=['GET'])
def get_chat(persona_id):
    conn = get_db()
    chats = conn.execute('SELECT * FROM chats WHERE persona_id=? ORDER BY time_ms',
                         (persona_id,)).fetchall()
    conn.close()
    return jsonify([dict(c) for c in chats])

@app.route('/api/chat/<persona_id>', methods=['POST'])
def send_message(persona_id):
    data = request.json
    conn = get_db()
    now = datetime.now()
    ts = now.strftime("%I:%M %p").lstrip('0')
    time_ms = int(now.timestamp() * 1000)

    # Save user message
    conn.execute('''INSERT INTO chats
        (persona_id,is_user,text,audio_data,image_path,timestamp,time_ms)
        VALUES (?,1,?,?,?,?,?)''',
        (persona_id, data.get('text',''), data.get('audio_data'),
         data.get('image_path'), ts, time_ms))

    persona = conn.execute('SELECT * FROM personas WHERE id=?', (persona_id,)).fetchone()
    user = conn.execute('SELECT * FROM user_profile LIMIT 1').fetchone()
    reply_messages = []

    if persona:
        # Get recent chat history (last 12 messages for context)
        history_rows = conn.execute(
            'SELECT is_user, text FROM chats WHERE persona_id=? ORDER BY time_ms DESC LIMIT 12',
            (persona_id,)).fetchall()
        history = [{'is_user': r['is_user'], 'text': r['text']} for r in reversed(history_rows)]

        recent_acts = conn.execute(
            'SELECT text FROM activities WHERE persona_id=? ORDER BY time_ms DESC LIMIT 5',
            (persona_id,)).fetchall()

        state = get_state(conn, persona_id)
        reply_messages, new_state = generate_sophie_reply(
            persona['name'], persona['description'],
            user['name'] if user else '',
            user['description'] if user else '',
            data.get('text',''),
            [dict(a) for a in recent_acts],
            now.hour,
            history,
            state,
        )
        save_state(conn, persona_id, new_state)

        # Save each reply message
        for i, msg in enumerate(reply_messages):
            r_ts = now.strftime("%I:%M %p").lstrip('0')
            conn.execute('''INSERT INTO chats
                (persona_id,is_user,text,audio_data,image_path,timestamp,time_ms)
                VALUES (?,0,?,?,?,?,?)''',
                (persona_id, msg, None, None, r_ts, time_ms + 3000 + i*2000))

    conn.commit(); conn.close()
    return jsonify({"status": "sent", "messages": reply_messages})

@app.route('/api/activities/<persona_id>', methods=['GET'])
def get_activities(persona_id):
    conn = get_db()
    acts = conn.execute('SELECT * FROM activities WHERE persona_id=? ORDER BY time_ms DESC',
                        (persona_id,)).fetchall()
    conn.close()
    return jsonify([dict(a) for a in acts])

@app.route('/api/activities/<persona_id>', methods=['POST'])
def add_activity(persona_id):
    data = request.json
    conn = get_db()
    now = datetime.now()
    conn.execute('''INSERT INTO activities (persona_id,text,timestamp,time_ms)
        VALUES (?,?,?,?)''',
        (persona_id, data['text'], now.strftime("%I:%M %p").lstrip('0'),
         int(now.timestamp()*1000)))
    conn.commit(); conn.close()
    return jsonify({"status": "added"})

@app.route('/api/user_profile', methods=['GET'])
def get_user_profile():
    conn = get_db()
    p = conn.execute('SELECT * FROM user_profile LIMIT 1').fetchone()
    conn.close()
    return jsonify(dict(p) if p else {"name":"","description":"","avatar":""})

@app.route('/api/user_profile', methods=['POST'])
def save_user_profile():
    data = request.json
    conn = get_db()
    conn.execute('DELETE FROM user_profile')
    conn.execute('INSERT INTO user_profile (name,description,avatar) VALUES (?,?,?)',
                 (data['name'], data['description'], data.get('avatar','')))
    conn.commit(); conn.close()
    return jsonify({"status": "saved"})

@app.route('/api/send_image/<persona_id>', methods=['POST'])
def send_image(persona_id):
    data = request.json
    image_type = data.get('type','daily')
    captions = {
        'eating':   'just made myself something 🍽️',
        'shopping': 'been running errands all day lol 🛍️',
        'bedtime':  'finally in bed, the girls are passed out on me 🛌',
        'daily':    'random pic from today ✨',
    }
    caption = data.get('desc') or captions.get(image_type, 'real pic from today ✨')
    conn = get_db()
    now = datetime.now()
    ts = now.strftime("%I:%M %p").lstrip('0')
    ms = int(now.timestamp()*1000)
    conn.execute('INSERT INTO activities (persona_id,text,timestamp,time_ms) VALUES (?,?,?,?)',
                 (persona_id, f"Sent photo: {image_type}", ts, ms))
    conn.execute('''INSERT INTO chats (persona_id,is_user,text,audio_data,image_path,timestamp,time_ms)
        VALUES (?,0,?,?,?,?,?)''',
        (persona_id, caption, None, None, ts, ms))
    conn.commit(); conn.close()
    return jsonify({"status": "image sent", "caption": caption})

@app.route('/api/export/<persona_id>/<platform>', methods=['GET'])
def export_chat(persona_id, platform):
    conn = get_db()
    chats = conn.execute('SELECT * FROM chats WHERE persona_id=? ORDER BY time_ms',
                         (persona_id,)).fetchall()
    persona = conn.execute('SELECT name FROM personas WHERE id=?', (persona_id,)).fetchone()
    conn.close()
    name = persona['name'] if persona else "Her"
    lines = []
    if platform == 'whatsapp':
        for ch in chats:
            p = "You: " if ch['is_user'] else f"{name}: "
            lines.append(p + (ch['text'] or '[media]'))
        content = "\n".join(lines)
    elif platform == 'telegram':
        content = json.dumps([{
            "from": "You" if ch['is_user'] else name,
            "text": ch['text'] or "[media]", "time": ch['timestamp']
        } for ch in chats], indent=2)
    else:
        content = "\n".join([
            f"[{ch['timestamp']}] {'You' if ch['is_user'] else name}: {ch['text'] or '[media]'}"
            for ch in chats
        ])
    return jsonify({"content": content, "filename": f"{name}_{platform}_export.txt"})

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

if __name__ == '__main__':
    conn = get_db()
    count = conn.execute('SELECT COUNT(*) FROM personas').fetchone()[0]
    if count == 0:
        conn.execute('''INSERT INTO personas (id,name,description,avatar,voice_sample,platform_style)
            VALUES (?,?,?,?,?,?)''',
            ("sophie-rain-001","Sophie Rain", SOPHIE_DESC,"","","imessage"))
        conn.commit()
    conn.close()
    port = int(os.environ.get("PORT",5000))
    print(f"Sophie Real running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
