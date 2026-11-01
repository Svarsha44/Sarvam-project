import os
import sys
import tempfile
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from dotenv import load_dotenv

# Ensure console supports UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from manuscript_processor import (
    process_manuscript_pipeline,
    SUPPORTED_LANGUAGES,
)
from story_narrator import (
    create_interactive_audio_tour,
    generate_voice_narration,
    STORYTELLER_VOICES,
)
from sarvamai import SarvamAI

app = Flask(__name__)

# Use /tmp on Vercel Serverless (read-only filesystem workaround)
TEMP_DIR = tempfile.gettempdir()
app.config["UPLOAD_FOLDER"] = os.path.join(TEMP_DIR, "sarvam_uploads")
app.config["AUDIO_FOLDER"] = os.path.join(TEMP_DIR, "sarvam_audio_outputs")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["AUDIO_FOLDER"], exist_ok=True)

# Curated Heritage Library Data
HERITAGE_LIBRARY = [
    {
        "id": "ashoka_sarnath",
        "title": "Lion Capital & Ashoka Pillar",
        "era": "Mauryan Empire (c. 250 BCE)",
        "region": "Sarnath, Uttar Pradesh",
        "category": "Inscriptions & Architecture",
        "excerpt": "देवानंपिये पियदसि राजा हेवं आहा। सवथ विजितेसु धम्मविजयो मुखमतो।",
        "description": "Carved from a single monolith of polished Chunar sandstone, representing universal peace and righteous governance (Dhamma).",
        "source_lang": "hi-IN",
    },
    {
        "id": "shanti_mantra",
        "title": "Shanti Mantra (Taittiriya Upanishad)",
        "era": "Late Vedic Era (c. 6th Century BCE)",
        "region": "Ancient Indo-Gangetic Plains",
        "category": "Sacred Manuscripts",
        "excerpt": "सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः । सर्वे भद्राणि पश्यन्तु मा कश्चिद्दुःखभाग्भवेत् ॥",
        "description": "A universal benediction for harmony, health, and liberation for all living beings.",
        "source_lang": "sa-IN",
    },
    {
        "id": "thirukkural",
        "title": "Thirukkural – In Praise of Truth",
        "era": "Sangam Era (c. 300 BCE – 100 CE)",
        "region": "Tamilakam (Modern Tamil Nadu)",
        "category": "Literature & Ethics",
        "excerpt": "வாய்மை எனப்படுவது யாதெனின் யாதொன்றும் தீமை இலாத சொலல்.",
        "description": "The immortal ethical treatise by Thiruvalluvar defining truth as speech that causes harmless good to all.",
        "source_lang": "ta-IN",
    },
    {
        "id": "konark_sun",
        "title": "Sun Temple of Konark",
        "era": "Eastern Ganga Dynasty (c. 1250 CE)",
        "region": "Konark, Odisha",
        "category": "Monuments & Astronomy",
        "excerpt": "कलिङ्ग वास्तुशिल्पस्य अद्भुतं दर्शनम्। द्वादश रथचक्राणि कालस्य सूचकाः।",
        "description": "A colossal cosmic stone chariot carrying the Sun God Surya, whose wheels function as precision sundials.",
        "source_lang": "sa-IN",
    },
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Itihasa | Sarvam AI Heritage Storyteller</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0D0F12;
            --bg-card: #151921;
            --bg-card-hover: #1c222d;
            --gold: #E5A93C;
            --gold-light: #F4CE75;
            --gold-dim: rgba(229, 169, 60, 0.15);
            --text-main: #F3F4F6;
            --text-dim: #9CA3AF;
            --border: #262D3D;
            --accent-glow: rgba(229, 169, 60, 0.25);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--bg-primary);
            color: var(--text-main);
            min-height: 100vh;
        }

        header {
            background: linear-gradient(180deg, rgba(229,169,60,0.08) 0%, rgba(13,15,18,0) 100%);
            border-bottom: 1px solid var(--border);
            padding: 24px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-icon {
            font-size: 30px;
            color: var(--gold);
        }

        .brand-title {
            font-family: 'Cinzel', serif;
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: var(--gold-light);
        }

        .brand-sub {
            font-size: 13px;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            background: rgba(21, 25, 33, 0.8);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid var(--border);
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-dim);
            font-size: 14px;
            font-weight: 600;
            padding: 10px 18px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.25s ease;
        }

        .tab-btn.active, .tab-btn:hover {
            color: var(--gold-light);
            background: var(--gold-dim);
            border: 1px solid rgba(229,169,60,0.3);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 36px 24px;
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 14px;
        }

        .card-title {
            font-family: 'Cinzel', serif;
            font-size: 20px;
            color: var(--gold-light);
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }

        @media (max-width: 850px) {
            .grid-2 { grid-template-columns: 1fr; }
        }

        label {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-dim);
            margin-bottom: 8px;
            display: block;
        }

        input[type="text"], select, textarea {
            width: 100%;
            background: #090B0E;
            border: 1px solid var(--border);
            border-radius: 10px;
            color: #fff;
            padding: 12px 16px;
            font-size: 14px;
            outline: none;
            transition: border 0.2s;
            margin-bottom: 16px;
            font-family: inherit;
        }

        input[type="text"]:focus, select:focus, textarea:focus {
            border-color: var(--gold);
        }

        .btn-gold {
            background: linear-gradient(135deg, #E5A93C 0%, #C4861F 100%);
            color: #000;
            font-weight: 700;
            border: none;
            padding: 14px 28px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 15px;
            letter-spacing: 0.5px;
            transition: transform 0.15s, box-shadow 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-gold:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(229,169,60,0.4);
        }

        .result-box {
            background: #090B0E;
            border: 1px solid rgba(229, 169, 60, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }

        .result-title {
            color: var(--gold);
            font-weight: 700;
            font-size: 15px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .result-text {
            color: var(--text-main);
            font-size: 15px;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .library-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }

        .library-item {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.2s, border-color 0.2s;
        }

        .library-item:hover {
            transform: translateY(-4px);
            border-color: var(--gold);
        }

        .badge {
            display: inline-block;
            background: var(--gold-dim);
            color: var(--gold-light);
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 20px;
            margin-bottom: 12px;
            border: 1px solid rgba(229,169,60,0.3);
        }

        .chat-container {
            height: 480px;
            display: flex;
            flex-direction: column;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            background: #090B0E;
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 16px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .chat-bubble {
            max-width: 80%;
            padding: 14px 18px;
            border-radius: 14px;
            font-size: 14.5px;
            line-height: 1.55;
        }

        .bubble-user {
            align-self: flex-end;
            background: #252D3D;
            color: #fff;
            border-bottom-right-radius: 4px;
        }

        .bubble-agent {
            align-self: flex-start;
            background: #181D26;
            border: 1px solid rgba(229, 169, 60, 0.25);
            color: var(--text-main);
            border-bottom-left-radius: 4px;
        }

        .suggestions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 10px;
        }

        .suggestion-chip {
            background: var(--gold-dim);
            color: var(--gold-light);
            border: 1px solid rgba(229,169,60,0.3);
            border-radius: 16px;
            padding: 6px 14px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.15s;
        }

        .suggestion-chip:hover {
            background: var(--gold);
            color: #000;
        }

        audio {
            width: 100%;
            margin-top: 14px;
            border-radius: 8px;
        }

        .spinner {
            display: none;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0,0,0,0.3);
            border-top-color: #000;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>

    <header>
        <div class="brand">
            <div class="brand-icon">🏛️</div>
            <div>
                <div class="brand-title">ITIHASA</div>
                <div class="brand-sub">Sarvam AI Indic Heritage Storyteller</div>
            </div>
        </div>
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('manuscripts')">📜 Manuscript Studio</button>
            <button class="tab-btn" onclick="switchTab('audio_tours')">🎙️ Audio Guided Tours</button>
            <button class="tab-btn" onclick="switchTab('agent')">🤖 Heritage Scholar Chat</button>
            <button class="tab-btn" onclick="switchTab('library')">🏛️ Heritage Library</button>
        </div>
    </header>

    <div class="container">

        <!-- TAB 1: MANUSCRIPT STUDIO -->
        <div id="tab-manuscripts" class="tab-content active">
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span style="font-size:24px;">📸</span>
                        <div class="card-title">Upload & Decipher Manuscript</div>
                    </div>
                    <form id="manuscriptForm" enctype="multipart/form-data">
                        <label>1. Select Manuscript Image or Document (PNG, JPG, PDF)</label>
                        <input type="file" id="manuscriptFile" accept="image/*,.pdf" style="margin-bottom:16px;">

                        <label>Or Choose A Sample Historic Inscription</label>
                        <select id="sampleSelect" onchange="loadSampleInscription()">
                            <option value="">-- Choose Sample --</option>
                            <option value="shanti">Taittiriya Upanishad Shanti Mantra (Sanskrit)</option>
                            <option value="ashoka">Emperor Ashoka Major Rock Edict (Prakrit/Sanskrit)</option>
                            <option value="thirukkural">Thiruvalluvar Thirukkural Verse (Tamil)</option>
                        </select>

                        <label>Manuscript Text (Extracted or Entered)</label>
                        <textarea id="manuscriptText" rows="4" placeholder="Upload an image to auto-extract with Sarvam Doc AI OCR, or type/paste historical text directly..."></textarea>

                        <label>Source Language</label>
                        <select id="sourceLang">
                            <option value="auto">Auto Detect Language</option>
                            <option value="sa-IN">Sanskrit (sa-IN)</option>
                            <option value="hi-IN">Hindi (hi-IN)</option>
                            <option value="ta-IN">Tamil (ta-IN)</option>
                            <option value="te-IN">Telugu (te-IN)</option>
                            <option value="bn-IN">Bengali (bn-IN)</option>
                            <option value="mr-IN">Marathi (mr-IN)</option>
                        </select>

                        <label>Target Language for Translation & Voiceover</label>
                        <select id="targetLang">
                            <option value="en-IN">English (en-IN)</option>
                            <option value="hi-IN">Hindi (hi-IN)</option>
                            <option value="sa-IN">Sanskrit (sa-IN)</option>
                            <option value="ta-IN">Tamil (ta-IN)</option>
                            <option value="te-IN">Telugu (te-IN)</option>
                            <option value="bn-IN">Bengali (bn-IN)</option>
                            <option value="mr-IN">Marathi (mr-IN)</option>
                        </select>

                        <button type="button" class="btn-gold" onclick="processManuscript()">
                            <span class="spinner" id="manuscriptSpinner"></span>
                            <span>Decipher, Translate & Narrate</span>
                        </button>
                    </form>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span style="font-size:24px;">✨</span>
                        <div class="card-title">Deciphered Insights & Voiceover</div>
                    </div>
                    <div id="manuscriptOutputPlaceholder" style="color:var(--text-dim); text-align:center; padding:60px 20px;">
                        Upload a manuscript or select a sample to extract text, translate, and listen to the voiceover.
                    </div>
                    <div id="manuscriptResults" style="display:none;">
                        <div class="result-box">
                            <div class="result-title">📖 Extracted Manuscript Text</div>
                            <div class="result-text" id="outExtracted"></div>
                        </div>
                        <div class="result-box">
                            <div class="result-title">🌐 Sarvam Translation (<span id="outLangLabel"></span>)</div>
                            <div class="result-text" id="outTranslated"></div>
                        </div>
                        <div class="result-box">
                            <div class="result-title">🏛️ Historical & Philosophical Context</div>
                            <div class="result-text" id="outContext"></div>
                        </div>
                        <div class="result-box" id="audioBox" style="display:none;">
                            <div class="result-title">🔊 Listen to Bulbul Voice Narration</div>
                            <audio id="manuscriptAudio" controls></audio>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: AUDIO GUIDED TOURS -->
        <div id="tab-audio_tours" class="tab-content">
            <div class="grid-2">
                <div class="card">
                    <div class="card-header">
                        <span style="font-size:24px;">🎙️</span>
                        <div class="card-title">Generate Audio Story / Guided Tour</div>
                    </div>
                    <label>Historical Landmark, Artifact or Mythological Legend</label>
                    <input type="text" id="tourTopic" placeholder="e.g. The Great Sun Temple of Konark and its celestial chariot wheels">

                    <label>Storytelling Style</label>
                    <select id="tourStyle">
                        <option value="documentary">Museum Docent / Documentary (Girish)</option>
                        <option value="dramatic">Dramatic Folklore & Legends (Shubh / Sarang)</option>
                        <option value="audiobook">Audiobook Narration</option>
                    </select>

                    <label>Narration Language</label>
                    <select id="tourLang">
                        <option value="en-IN">English (en-IN)</option>
                        <option value="hi-IN">Hindi (hi-IN)</option>
                        <option value="ta-IN">Tamil (ta-IN)</option>
                        <option value="te-IN">Telugu (te-IN)</option>
                        <option value="bn-IN">Bengali (bn-IN)</option>
                        <option value="mr-IN">Marathi (mr-IN)</option>
                    </select>

                    <button class="btn-gold" onclick="generateTour()">
                        <span class="spinner" id="tourSpinner"></span>
                        <span>Produce Audio Guide</span>
                    </button>

                    <div style="margin-top:20px;">
                        <label>Quick Suggestions</label>
                        <div class="suggestions">
                            <span class="suggestion-chip" onclick="setTourTopic('Ashoka Pillar at Sarnath and the Lion Capital')">Sarnath Pillar</span>
                            <span class="suggestion-chip" onclick="setTourTopic('The ancient ruins and library of Nalanda University')">Nalanda Library</span>
                            <span class="suggestion-chip" onclick="setTourTopic('The celestial stone chariot of Konark Sun Temple')">Konark Sun Temple</span>
                            <span class="suggestion-chip" onclick="setTourTopic('Brihadeeswarar Temple of Thanjavur and its granite vimana')">Thanjavur Temple</span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <span style="font-size:24px;">🎧</span>
                        <div class="card-title">Story Player & Script</div>
                    </div>
                    <div id="tourPlaceholder" style="color:var(--text-dim); text-align:center; padding:60px 20px;">
                        Enter a topic to generate an immersive audio guide produced by Sarvam AI.
                    </div>
                    <div id="tourResults" style="display:none;">
                        <div class="result-box">
                            <div class="result-title">📜 Docent Narration Script</div>
                            <div class="result-text" id="tourScript"></div>
                        </div>
                        <div class="result-box">
                            <div class="result-title">🔊 Sarvam Bulbul Audio Guide</div>
                            <audio id="tourAudio" controls></audio>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 3: AGENT CHAT -->
        <div id="tab-agent" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <span style="font-size:24px;">🤖</span>
                    <div class="card-title">Interactive Indic Heritage Scholar (Sarvam-105b)</div>
                </div>
                <div class="chat-container">
                    <div class="chat-messages" id="chatMessages">
                        <div class="chat-bubble bubble-agent">
                            Namaste! I am your Indic heritage and archaeology scholar. Ask me anything about ancient manuscripts, archaeological mysteries, temple architecture, or mythology facts. What would you like to explore today?
                        </div>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <input type="text" id="chatInput" placeholder="Ask about an ancient king, manuscript, or architectural mystery..." onkeydown="if(event.key==='Enter') sendChatMessage()">
                        <button class="btn-gold" style="padding:12px 24px;" onclick="sendChatMessage()">Send</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 4: HERITAGE LIBRARY -->
        <div id="tab-library" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <span style="font-size:24px;">🏛️</span>
                    <div class="card-title">Curated Historical Archive & Artifacts</div>
                </div>
                <div class="library-grid">
                    {% for item in library %}
                    <div class="library-item">
                        <div>
                            <span class="badge">{{ item.category }}</span>
                            <h3 style="font-family:'Cinzel', serif; color:var(--gold-light); margin-bottom:6px;">{{ item.title }}</h3>
                            <div style="font-size:12px; color:var(--text-dim); margin-bottom:10px;">{{ item.era }} • {{ item.region }}</div>
                            <div style="background:#090B0E; padding:10px; border-radius:8px; font-size:13px; margin-bottom:10px; color:var(--gold);">
                                {{ item.excerpt }}
                            </div>
                            <p style="font-size:13px; color:var(--text-dim); line-height:1.45;">{{ item.description }}</p>
                        </div>
                        <div style="margin-top:16px; display:flex; gap:8px;">
                            <button class="btn-gold" style="padding:8px 14px; font-size:12px;" onclick="loadLibraryItem('{{ item.excerpt }}', '{{ item.source_lang }}')">Decipher In Studio</button>
                            <button class="btn-gold" style="padding:8px 14px; font-size:12px; background:#262D3D; color:#fff;" onclick="loadTourFromLibrary('{{ item.title }}')">Audio Tour</button>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

    </div>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabId).classList.add('active');
            event.target.classList.add('active');
        }

        const SAMPLES = {
            shanti: "सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः । सर्वे भद्राणि पश्यन्तु मा कश्चिद्दुःखभाग्भवेत् ॥",
            ashoka: "देवानंपिये पियदसि राजा हेवं आहा। सवथ विजितेसु धम्मविजयो मुखमतो।",
            thirukkural: "வாய்மை எனப்படுவது யாதெனின் யாதொன்றும் தீமை இலாத சொலல்."
        };

        function loadSampleInscription() {
            const key = document.getElementById('sampleSelect').value;
            if (key && SAMPLES[key]) {
                document.getElementById('manuscriptText').value = SAMPLES[key];
                if (key === 'shanti') document.getElementById('sourceLang').value = 'sa-IN';
                if (key === 'ashoka') document.getElementById('sourceLang').value = 'hi-IN';
                if (key === 'thirukkural') document.getElementById('sourceLang').value = 'ta-IN';
            }
        }

        async function processManuscript() {
            const spinner = document.getElementById('manuscriptSpinner');
            const fileInput = document.getElementById('manuscriptFile');
            const text = document.getElementById('manuscriptText').value.trim();
            const sourceLang = document.getElementById('sourceLang').value;
            const targetLang = document.getElementById('targetLang').value;

            if (!fileInput.files.length && !text) {
                alert('Please upload an image/document or enter manuscript text.');
                return;
            }

            spinner.style.display = 'inline-block';
            const formData = new FormData();
            if (fileInput.files.length) {
                formData.append('file', fileInput.files[0]);
            }
            formData.append('raw_text', text);
            formData.append('source_language', sourceLang);
            formData.append('target_language', targetLang);

            try {
                const res = await fetch('/api/process_manuscript', { method: 'POST', body: formData });
                const data = await res.json();
                spinner.style.display = 'none';

                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }

                document.getElementById('manuscriptOutputPlaceholder').style.display = 'none';
                document.getElementById('manuscriptResults').style.display = 'block';
                document.getElementById('outExtracted').innerText = data.original_text;
                document.getElementById('outTranslated').innerText = data.translated_text;
                document.getElementById('outLangLabel').innerText = data.target_language;
                document.getElementById('outContext').innerText = data.historical_context;

                if (data.audio_url) {
                    document.getElementById('audioBox').style.display = 'block';
                    const audio = document.getElementById('manuscriptAudio');
                    audio.src = data.audio_url;
                    audio.load();
                }
            } catch (err) {
                spinner.style.display = 'none';
                alert('Request failed: ' + err.message);
            }
        }

        function setTourTopic(topic) {
            document.getElementById('tourTopic').value = topic;
        }

        async function generateTour() {
            const spinner = document.getElementById('tourSpinner');
            const topic = document.getElementById('tourTopic').value.trim();
            const style = document.getElementById('tourStyle').value;
            const lang = document.getElementById('tourLang').value;

            if (!topic) {
                alert('Please enter a tour topic.');
                return;
            }

            spinner.style.display = 'inline-block';
            try {
                const res = await fetch('/api/generate_tour', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic, style, language_code: lang })
                });
                const data = await res.json();
                spinner.style.display = 'none';

                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }

                document.getElementById('tourPlaceholder').style.display = 'none';
                document.getElementById('tourResults').style.display = 'block';
                document.getElementById('tourScript').innerText = data.script;

                const audio = document.getElementById('tourAudio');
                audio.src = data.audio_url;
                audio.load();
                audio.play();
            } catch (err) {
                spinner.style.display = 'none';
                alert('Failed to generate tour: ' + err.message);
            }
        }

        async function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;

            const chat = document.getElementById('chatMessages');
            
            // Add user message
            const userBubble = document.createElement('div');
            userBubble.className = 'chat-bubble bubble-user';
            userBubble.innerText = message;
            chat.appendChild(userBubble);
            input.value = '';
            chat.scrollTop = chat.scrollHeight;

            // Loading indicator
            const agentBubble = document.createElement('div');
            agentBubble.className = 'chat-bubble bubble-agent';
            agentBubble.innerText = 'Consulting historical archives...';
            chat.appendChild(agentBubble);
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                const data = await res.json();
                
                agentBubble.innerHTML = data.reply.replace(/\\n/g, '<br>');
                
                // Add suggestion chips
                if (data.suggestions && data.suggestions.length) {
                    const chipsDiv = document.createElement('div');
                    chipsDiv.className = 'suggestions';
                    data.suggestions.forEach(s => {
                        const chip = document.createElement('span');
                        chip.className = 'suggestion-chip';
                        chip.innerText = '✦ ' + s;
                        chip.onclick = () => {
                            document.getElementById('chatInput').value = s;
                            sendChatMessage();
                        };
                        chipsDiv.appendChild(chip);
                    });
                    agentBubble.appendChild(chipsDiv);
                }
                chat.scrollTop = chat.scrollHeight;
            } catch (err) {
                agentBubble.innerText = 'Error querying scholar: ' + err.message;
            }
        }

        function loadLibraryItem(text, srcLang) {
            document.getElementById('manuscriptText').value = text;
            if (srcLang) document.getElementById('sourceLang').value = srcLang;
            switchTab('manuscripts');
        }

        function loadTourFromLibrary(title) {
            document.getElementById('tourTopic').value = title;
            switchTab('audio_tours');
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, library=HERITAGE_LIBRARY)

@app.route("/audio_outputs/<filename>")
def serve_audio(filename):
    return send_from_directory(app.config["AUDIO_FOLDER"], filename)

@app.route("/api/process_manuscript", methods=["POST"])
def api_process_manuscript():
    try:
        raw_text = request.form.get("raw_text")
        source_lang = request.form.get("source_language", "auto")
        target_lang = request.form.get("target_language", "en-IN")
        image_path = None

        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            saved_path = os.path.join(app.config["UPLOAD_FOLDER"], f.filename)
            f.save(saved_path)
            image_path = saved_path

        audio_name = f"manuscript_{int(os.times().elapsed)}.mp3"
        audio_dest = os.path.join(app.config["AUDIO_FOLDER"], audio_name)

        result = process_manuscript_pipeline(
            image_path=image_path,
            raw_text=raw_text,
            source_language=source_lang,
            target_language=target_lang,
            generate_audio=True,
            audio_output_path=audio_dest,
        )

        return jsonify({
            "original_text": result["original_text"],
            "translated_text": result["translated_text"],
            "source_language": result["source_language"],
            "target_language": result["target_language"],
            "historical_context": result["historical_context"],
            "audio_url": f"/audio_outputs/{audio_name}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate_tour", methods=["POST"])
def api_generate_tour():
    try:
        data = request.json or {}
        topic = data.get("topic")
        style = data.get("style", "documentary")
        language_code = data.get("language_code", "en-IN")

        if not topic:
            return jsonify({"error": "Topic is required"}), 400

        audio_name = f"tour_{int(os.times().elapsed)}.mp3"
        audio_dest = os.path.join(app.config["AUDIO_FOLDER"], audio_name)

        result = create_interactive_audio_tour(
            topic=topic,
            language_code=language_code,
            style=style,
            output_path=audio_dest,
        )

        return jsonify({
            "topic": result["topic"],
            "script": result["script"],
            "audio_url": f"/audio_outputs/{audio_name}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def api_chat():
    try:
        data = request.json or {}
        message = data.get("message", "")
        if not message:
            return jsonify({"error": "Message is required"}), 400

        api_key = os.getenv("SARVAM_API_KEY")
        client = SarvamAI(api_subscription_key=api_key)

        prompt = (
            f"User Question: '{message}'\n\n"
            "Respond as a knowledgeable Indic heritage and mythology scholar in 2-3 engaging sentences. "
            "Then, on a new line starting with 'SUGGESTIONS:', list 3 short, intriguing related topics or questions separated by pipes (|)."
        )

        resp = client.chat.completions(
            model="sarvam-105b-conversations",
            messages=[
                {"role": "system", "content": "You are a master Indic historian, epigrapher, and mythology scholar."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=350,
        )

        content = resp.choices[0].message.content.strip()
        suggestions = []
        if "SUGGESTIONS:" in content:
            parts = content.split("SUGGESTIONS:")
            reply = parts[0].strip()
            raw_sugg = parts[1].strip()
            suggestions = [s.strip() for s in raw_sugg.split("|") if s.strip()]
        else:
            reply = content
            suggestions = ["Ashoka's Dhamma", "Nalanda's Lost Manuscripts", "Chola Maritime Expeditions"]

        return jsonify({
            "reply": reply,
            "suggestions": suggestions[:3],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting Itihasa Heritage App on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
