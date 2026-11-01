import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.play import save

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment configuration
load_dotenv()

api_key = os.getenv("SARVAM_API_KEY")
if not api_key:
    raise ValueError("SARVAM_API_KEY is missing from environment. Please check your .env file.")

client = SarvamAI(api_subscription_key=api_key)

# Curated storyteller voices for historical narration and audio tours
STORYTELLER_VOICES = {
    "en-IN": {
        "documentary": "girish_en_documentary",
        "audiobook": "shubh_en_audiobook",
        "story": "chandrika_en_stories",
        "dramatic": "sarang_en_narration",
    },
    "hi-IN": {
        "dramatic": "shubh_hi_stories_dramatic",
        "documentary": "anand_hi_documentary",
        "story": "roopa_hi_narration",
        "devotional": "girish_hi_devotional",
    },
    "ta-IN": {
        "narration": "gokul_ta_narration",
        "expressive": "vijay_ta_narration",
    },
    "te-IN": {
        "narration": "kavitha_te_narration",
        "expressive": "tarun_te_narration",
    },
    "bn-IN": {
        "suspense": "bimal_bn_suspense",
        "conversational": "roopa_bn_conversational",
    },
    "mr-IN": {
        "story": "rupali_mr_stories",
        "narration": "mrunal_mr_narration",
    },
}

def generate_voice_narration(
    text: str,
    output_path: str = "audio_outputs/heritage_story.mp3",
    language_code: str = "en-IN",
    speaker: str = "girish_en_documentary",
    pace: float = 1.0,
) -> str:
    """
    Converts historical storytelling text into natural spoken narration using Sarvam Bulbul TTS.
    
    :param text: The story or guided tour excerpt to narrate.
    :param output_path: Destination path for the generated MP3 file.
    :param language_code: Indic language code (e.g. en-IN, hi-IN, ta-IN, te-IN, bn-IN, mr-IN).
    :param speaker: Sarvam speaker persona optimized for narration/stories.
    :param pace: Speed of narration (default: 1.0).
    :return: Absolute path to the generated audio file.
    """
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    print(f"Synthesizing audio narration using Sarvam Bulbul (speaker: {speaker}, lang: {language_code})...")

    response = client.text_to_speech.convert(
        text=text,
        language_code=language_code,
        model="bulbul:v4-flash",
        speaker=speaker,
        pace=pace,
        output_audio_codec="mp3",
    )

    save(response, str(dest))
    print(f"Audio story successfully saved to: {dest.resolve()}")
    return str(dest.resolve())

def create_interactive_audio_tour(
    topic: str,
    language_code: str = "en-IN",
    style: str = "documentary",
    output_path: str = "audio_outputs/generated_tour.mp3",
) -> dict:
    """
    End-to-End Pipeline:
    1. Heritage Chat Agent drafts an immersive, accurate tour narration.
    2. Bulbul TTS synthesizes the narrative into an audio tour MP3.
    """
    speaker = STORYTELLER_VOICES.get(language_code, {}).get(style, "girish_en_documentary")

    language_names = {
        "en-IN": "English",
        "hi-IN": "Hindi (in Devanagari script)",
        "ta-IN": "Tamil",
        "te-IN": "Telugu",
        "bn-IN": "Bengali",
        "mr-IN": "Marathi",
    }
    target_lang_str = language_names.get(language_code, "English")

    system_instruction = (
        "You are a master museum docent and heritage storyteller. "
        f"Draft a captivating, immersive audio guide narrative (3-4 sentences max) in {target_lang_str}. "
        "Write naturally for spoken delivery without markdown formatting, bullet points, or asterisks. "
        f"Ensure the output text is completely written in {target_lang_str}."
    )

    prompt = f"Historical Topic or Artifact: '{topic}'. Create the spoken guided tour narrative."

    print(f"\n[1/2] Heritage Agent crafting narration for: '{topic}'...")
    chat_response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=250,
    )
    story_script = chat_response.choices[0].message.content.strip()
    print(f"Generated Script:\n\"{story_script}\"")

    print(f"\n[2/2] Voicing script with Bulbul TTS ({speaker})...")
    audio_file = generate_voice_narration(
        text=story_script,
        output_path=output_path,
        language_code=language_code,
        speaker=speaker,
    )

    return {
        "topic": topic,
        "script": story_script,
        "audio_path": audio_file,
        "speaker": speaker,
        "language_code": language_code,
    }

if __name__ == "__main__":
    print("=== Testing End-to-End Heritage Audio Guide Pipeline ===")
    
    # 1. English Documentary Audio Guide: Konark Sun Temple
    result_en = create_interactive_audio_tour(
        topic="The Great Sun Temple of Konark and its celestial chariot wheels",
        language_code="en-IN",
        style="documentary",
        output_path="audio_outputs/konark_sun_temple_tour.mp3",
    )

    # 2. Hindi Story Narration: Nalanda University
    result_hi = create_interactive_audio_tour(
        topic="प्राचीन नालंदा विश्वविद्यालय और इसका पुस्तकालय धर्मगंज",
        language_code="hi-IN",
        style="dramatic",
        output_path="audio_outputs/nalanda_university_hi.mp3",
    )

    print("\nAll audio tours generated successfully!")
