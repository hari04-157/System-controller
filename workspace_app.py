import sys
import ollama
import os
import psutil
import json
import uuid
import time
from datetime import datetime
from flask import Flask, render_template, request, Response, stream_with_context, jsonify
import PyPDF2
import docx
from duckduckgo_search import DDGS

app = Flask(__name__)

# Determine Workspace Type
WORKSPACE_TYPE = sys.argv[1] if len(sys.argv) > 1 else "code"
HISTORY_FILE = f"{WORKSPACE_TYPE}_sessions.json"

def get_system_prompt():
    base = "You are a helpful AI."
    if WORKSPACE_TYPE == "defence":
        base = "You are a specialized Indian Defence AI Tutor. Focus strictly on military current affairs, strategic news, and CDS exam prep."
    elif WORKSPACE_TYPE == "code":
        base = "You are an expert software engineer. Provide highly optimized code. Focus on Python, ML algorithms, and web development."
    
    return base + r" CRITICAL: You must output mathematical formulas using LaTeX syntax. Always wrap inline math in $...$ and block math in $$...$$. Do not use standard text for formulas."

def load_all_sessions():
    """Robustly loads the JSON file, handling errors if file is corrupt or missing."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_all_sessions(sessions):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f)

@app.route('/')
def home():
    return render_template('index.html', workspace=WORKSPACE_TYPE.title())

# --- SESSION MANAGEMENT ROUTES ---

@app.route('/sessions', methods=['GET'])
def get_sessions():
    data = load_all_sessions()
    session_list = []
    for sid, sdata in data.items():
        session_list.append({
            'id': sid,
            'title': sdata.get('title', 'New Chat'),
            'timestamp': sdata.get('timestamp', 0)
        })
    # Sort: Newest first
    session_list.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify({'sessions': session_list})

@app.route('/load_session/<session_id>', methods=['GET'])
def load_session(session_id):
    data = load_all_sessions()
    return jsonify(data.get(session_id, {'messages': []}))

@app.route('/new_session', methods=['POST'])
def new_session():
    data = load_all_sessions()
    session_id = str(uuid.uuid4())
    timestamp = time.time()
    
    # Create the new session entry
    data[session_id] = {
        'title': f"New Chat {datetime.now().strftime('%H:%M')}",
        'timestamp': timestamp,
        'messages': []
    }
    save_all_sessions(data)
    return jsonify({'id': session_id, 'title': data[session_id]['title']})

@app.route('/save_message', methods=['POST'])
def save_message():
    session_id = request.json.get('session_id')
    role = request.json.get('role')
    content = request.json.get('content')
    
    if not session_id: return jsonify({'error': 'No ID'})
    
    data = load_all_sessions()
    if session_id not in data:
        data[session_id] = {'title': 'New Chat', 'timestamp': time.time(), 'messages': []}
    
    data[session_id]['messages'].append({'role': role, 'content': content})
    
    # Auto-Rename chat based on first user message
    if role == 'user' and len(data[session_id]['messages']) <= 2:
        # Take first 30 chars of the message as title
        new_title = content[:30] + "..." if len(content) > 30 else content
        data[session_id]['title'] = new_title
        
    save_all_sessions(data)
    return jsonify({'status': 'success'})

@app.route('/delete_session', methods=['POST'])
def delete_session():
    """Allows deleting a specific chat from the sidebar."""
    session_id = request.json.get('session_id')
    data = load_all_sessions()
    if session_id in data:
        del data[session_id]
        save_all_sessions(data)
    return jsonify({'status': 'success'})

# --- CHAT GENERATION ---
@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message')
    history = request.json.get('history', [])
    
    messages = [{'role': 'system', 'content': get_system_prompt()}]
    messages.extend(history)
    messages.append({'role': 'user', 'content': user_msg})

    def generate():
        try:
            stream = ollama.chat(model='llama3', messages=messages, stream=True)
            for chunk in stream:
                yield chunk['message']['content']
        except Exception as e:
            yield f"Error: {str(e)}"

    return Response(stream_with_context(generate()), mimetype='text/plain')

# --- TOOLS (Hardware, Search, Upload) ---
@app.route('/vitals', methods=['GET'])
def get_vitals():
    return jsonify({'cpu': psutil.cpu_percent(interval=None), 'ram': psutil.virtual_memory().percent})

@app.route('/search', methods=['POST'])
def web_search():
    query = request.json.get('query')
    try:
        results = DDGS().text(query, max_results=3)
        context = "\n".join([f"Title: {r['title']}\nSnippet: {r['body']}" for r in results])
        return jsonify({'context': context})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: 
        return jsonify({'error': 'No file'}), 400
        
    file = request.files['file']
    text = ""
    filename = file.filename.lower()
    
    try:
        # 1. Read the first 4 bytes to check for PDF Signature (%PDF)
        header = file.read(4)
        file.seek(0) # CRITICAL: Reset cursor to start after peeking!
        
        # 2. Smart Detection (Header OR Extension)
        if header == b'%PDF' or filename.endswith('.pdf'):
            try:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n"
            except:
                text = "[System: This PDF contains scanned images or is unreadable.]"

        # 3. Word Documents
        elif filename.endswith(('.doc', '.docx')):
            try:
                doc = docx.Document(file)
                for para in doc.paragraphs: text += para.text + "\n"
            except:
                text = "[System: Could not read Word document.]"
                
        # 4. Fallback for Code/Text files (Python, HTML, TXT, JSON)
        else:
            text = file.read().decode('utf-8', errors='ignore')
            
    except Exception as e:
        return jsonify({'error': f"Processing failed: {str(e)}"}), 500

    return jsonify({'text': text.strip(), 'filename': file.filename})

if __name__ == '__main__':
    app.run(port=5050, debug=False)