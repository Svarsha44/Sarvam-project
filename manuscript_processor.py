import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY not found in environment.")

client = SarvamAI(api_subscription_key=api_key)

SUPPORTED_LANGUAGES = {
    "en-IN": "English",
    "hi-IN": "Hindi",
    "sa-IN": "Sanskrit",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "bn-IN": "Bengali",
    "mr-IN": "Marathi",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
    "od-IN": "Odia",
    "ur-IN": "Urdu",
}

def extract_text_from_manuscript(image_path: str, content_type: str = "mixed", poll_timeout: int = 60) -> str:
    """
    Extracts text from an image or document of a historical manuscript using Sarvam Vision Doc AI.
    
    :param image_path: Path to the image file (PNG, JPG, or PDF).
    :param content_type: 'printed', 'handwritten', or 'mixed'.
    :param poll_timeout: Maximum wait time in seconds.
    :return: Extracted manuscript text/markdown.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Manuscript file not found at: {image_path}")

    suffix = path.suffix.lower()
    mime_type = "application/pdf" if suffix == ".pdf" else f"image/{suffix.replace('.', '')}"
    if mime_type == "image/jpg":
        mime_type = "image/jpeg"

    print(f"[Doc AI] Submitting manuscript '{path.name}' to Sarvam Document AI OCR...")

    with open(path, "rb") as f:
        job = client.doc_ai.parse(
            file=[(path.name, f, mime_type)],
            content_type=content_type,
        )

    job_id = job.job_id
    print(f"[Doc AI] Parse job created (ID: {job_id}). Waiting for completion...")

    start_time = time.time()
    while time.time() - start_time < poll_timeout:
        status_resp = client.doc_ai.get_status(job_id=job_id)
        state = getattr(status_resp, "status", None) or getattr(status_resp, "state", "processing")
        
        if str(state).lower() in ("completed", "done", "success"):
            print("[Doc AI] Extraction completed! Retrieving document package...")
            download_info = client.doc_ai.get_download_url(job_id=job_id)
            import httpx
            import io
            import zipfile
            import json
            import re

            r = httpx.get(download_info.url)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            extracted_blocks = []

            # Prefer metadata page json if present for structured blocks
            for name in sorted(z.namelist()):
                if "metadata" in name and name.endswith(".json"):
                    try:
                        pdata = json.loads(z.read(name).decode("utf-8"))
                        for block in pdata.get("blocks", []):
                            txt = block.get("text", "").strip()
                            if txt:
                                extracted_blocks.append(txt)
                    except Exception:
                        pass

            # Fallback to HTML text parsing if no metadata blocks
            if not extracted_blocks:
                for name in z.namelist():
                    if name.endswith(".html"):
                        html_doc = z.read(name).decode("utf-8", errors="replace")
                        text_only = re.sub(r"<style[\s\S]*?</style>", "", html_doc)
                        text_only = re.sub(r"<[^>]+>", " ", text_only)
                        extracted_blocks.append(re.sub(r"\s+", " ", text_only).strip())

            final_text = "\n\n".join(extracted_blocks).strip()
            print(f"[Doc AI] Extracted {len(final_text)} characters.")
            return final_text if final_text else "No legible text could be extracted from the document."
        elif str(state).lower() in ("failed", "error"):
            raise RuntimeError(f"Sarvam Doc AI job failed: {status_resp}")
        
        time.sleep(3)

    raise TimeoutError(f"Doc AI job {job_id} did not finish within {poll_timeout} seconds.")

def translate_manuscript_text(
    text: str,
    target_language_code: str = "en-IN",
    source_language_code: str = "auto",
) -> dict:
    """
    Translates historical manuscript text into the user's selected language using Sarvam Translate.
    """
    # 1. Identify source language if set to auto
    if not source_language_code or source_language_code == "auto":
        print("[Translate] Detecting language of manuscript text...")
        try:
            id_resp = client.text.identify_language(input=text[:250])
            detected = getattr(id_resp, "language_code", None)
            source_language_code = detected if detected else "hi-IN"
            print(f"[Translate] Detected language: {source_language_code}")
        except Exception as e:
            print(f"[Translate] Auto-detection fallback to hi-IN (Reason: {e})")
            source_language_code = "hi-IN"

    # If source is same as target, no translation needed
    if source_language_code == target_language_code:
        return {
            "original_text": text,
            "translated_text": text,
            "source_language": source_language_code,
            "target_language": target_language_code,
        }

    print(f"[Translate] Translating from {source_language_code} to {target_language_code} using sarvam-translate:v1...")
    resp = client.text.translate(
        input=text,
        source_language_code=source_language_code,
        target_language_code=target_language_code,
        model="sarvam-translate:v1",
        mode="formal",
    )

    return {
        "original_text": text,
        "translated_text": resp.translated_text,
        "source_language": source_language_code,
        "target_language": target_language_code,
    }

def analyze_manuscript_context(text: str) -> str:
    """
    Analyzes historical and philosophical context of the manuscript using Sarvam-105b conversational scholar.
    """
    print("[Agent] Consulting Heritage Scholar for cultural context and symbolism...")
    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert Indic epigrapher, archaeologist, and manuscript historian. "
                    "Analyze the provided historical or manuscript text in 2-3 concise, engaging sentences. "
                    "Explain its historical context, origin, and philosophical significance."
                ),
            },
            {
                "role": "user",
                "content": f"Historical manuscript text: \"{text}\"",
            },
        ],
        temperature=0.5,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()

def process_manuscript_pipeline(
    image_path: str = None,
    raw_text: str = None,
    source_language: str = "auto",
    target_language: str = "en-IN",
    generate_audio: bool = False,
    audio_output_path: str = "audio_outputs/manuscript_narration.mp3",
) -> dict:
    """
    Full End-to-End Manuscript Processing Pipeline:
    1. Extract text from image (if image provided) or use raw_text
    2. Translate to user's desired language
    3. Provide historical & cultural context via Sarvam AI
    4. (Optional) Synthesize audio narration via Bulbul TTS
    """
    if image_path:
        extracted = extract_text_from_manuscript(image_path)
    elif raw_text:
        extracted = raw_text.strip()
    else:
        raise ValueError("Either image_path or raw_text must be provided.")

    # Translate
    trans_result = translate_manuscript_text(
        text=extracted,
        target_language_code=target_language,
        source_language_code=source_language,
    )

    # Cultural context
    context_note = analyze_manuscript_context(extracted)

    result = {
        "original_text": extracted,
        "translated_text": trans_result["translated_text"],
        "source_language": trans_result["source_language"],
        "target_language": trans_result["target_language"],
        "historical_context": context_note,
        "audio_path": None,
    }

    # Optional Voice Narration
    if generate_audio:
        from story_narrator import generate_voice_narration, STORYTELLER_VOICES
        speaker = STORYTELLER_VOICES.get(target_language, {}).get("documentary") or STORYTELLER_VOICES.get(target_language, {}).get("story", "shubh_en_narration")
        audio_file = generate_voice_narration(
            text=trans_result["translated_text"],
            output_path=audio_output_path,
            language_code=target_language,
            speaker=speaker,
        )
        result["audio_path"] = audio_file

    return result

if __name__ == "__main__":
    # Test with a classic historical manuscript excerpt (Sanskrit inscription)
    sample_inscription = "सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः । सर्वे भद्राणि पश्यन्तु मा कश्चिद्दुःखभाग्भवेत् ॥"
    
    print("=== Testing Manuscript Translation & Historical Analysis ===")
    output = process_manuscript_pipeline(
        raw_text=sample_inscription,
        source_language="sa-IN",
        target_language="en-IN",
        generate_audio=True,
        audio_output_path="audio_outputs/shanti_mantra.mp3",
    )

    print("\n--- RESULTS ---")
    print(f"Original Text: {output['original_text']}")
    print(f"Detected Source: {output['source_language']}")
    print(f"Translated Text ({output['target_language']}): {output['translated_text']}")
    print(f"Historical Context:\n{output['historical_context']}")
    if output["audio_path"]:
        print(f"Audio Narration: {output['audio_path']}")
