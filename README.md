# 🏛️ ITIHASA — Indic Heritage Storyteller & Manuscript Studio
Powered by **Sarvam AI** (`sarvam-105b-conversations`, `sarvam-translate:v1`, `bulbul:v4-flash`, and `doc_ai`).

---

## 🌟 Key Features

1. **📜 Manuscript Studio (Vision OCR & Multilingual Translation)**
   - Upload manuscript images (PNG, JPG, PDF) or choose from iconic historical inscriptions.
   - Text extraction powered by **Sarvam Document AI OCR**.
   - Multilingual translation across **22+ Indic languages** (Sanskrit, Hindi, Tamil, Telugu, Bengali, Marathi, etc.) using `sarvam-translate:v1`.
   - Cultural, philosophical, and epigraphic commentary provided by **Sarvam-105b**.
   - Spoken audio voiceover powered by **Bulbul TTS**.

2. **🎙️ Audio Guided Tours & Storytelling**
   - Enter any historical landmark, temple, or mythological legend.
   - Generates an immersive museum docent script using `sarvam-105b`.
   - Synthesizes broadcast-quality audio narration using **Bulbul v4-flash** in multiple regional Indic voices and styles (Documentary, Dramatic Tales, Audiobooks).

3. **🤖 Interactive Heritage Scholar Agent**
   - Real-time conversational agent specialized in Indic history, archaeology, and folklore.
   - Suggests 3 interactive follow-up topics after each response for guided deep exploration.

4. **🏛️ Heritage Library**
   - Pre-curated collection of ancient inscriptions, Vedic verses, Sangam poetry, and temple architecture with 1-click deciphering and audio tour generation.

---

## 🚀 Quickstart (Run Locally)

1. Clone or navigate to the project directory:
   ```bash
   cd c:\Users\varsh\OneDrive\Desktop\Sarvam
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure your `.env` contains:
   ```env
   SARVAM_API_KEY=your_key_here
   ```

4. Launch the application:
   ```bash
   python app.py
   ```
   Open **http://localhost:5000** in your web browser.

---

## ☁️ Deploy to Vercel

1. Push this repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Itihasa Heritage Storyteller"
   git branch -M main
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. In the [Vercel Dashboard](https://vercel.com/):
   - Click **Add New Project** and import your repository.
   - Under **Environment Variables**, add:
     - `SARVAM_API_KEY`: `your_sarvam_api_key`
   - Click **Deploy**! (Vercel automatically detects [`vercel.json`](file:///c:/Users/varsh/OneDrive/Desktop/Sarvam/vercel.json) and configures the Python serverless function).
