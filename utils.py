import os
import re
import json
import yt_dlp
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from faster_whisper import WhisperModel
from youtube_transcript_api import YouTubeTranscriptApi
from pyvis.network import Network

load_dotenv()

# --------------------------------------------------
# API KEY SETUP
# --------------------------------------------------
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Add it in Streamlit Cloud Secrets or local .env file."
    )

client = Groq(api_key=GROQ_API_KEY)


# --------------------------------------------------
# WHISPER MODEL
# --------------------------------------------------
@st.cache_resource
def load_whisper_model():
    return WhisperModel("base", device="cpu", compute_type="int8")


model = load_whisper_model()


# --------------------------------------------------
# YOUTUBE VIDEO ID EXTRACTOR
# --------------------------------------------------
def extract_video_id(url):
    patterns = [
        r"(?:v=)([^&]+)",
        r"youtu\.be/([^?&]+)",
        r"shorts/([^?&]+)",
        r"embed/([^?&]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


# --------------------------------------------------
# GET YOUTUBE CAPTIONS FIRST
# --------------------------------------------------
def get_youtube_captions(url):
    """
    First try to get captions/transcript directly.
    This avoids YouTube download blocking on Streamlit Cloud.
    """
    try:
        video_id = extract_video_id(url)

        if not video_id:
            return None

        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=["en", "en-US", "en-GB", "hi"]
        )

        transcript = " ".join([item["text"] for item in transcript_list])
        return transcript.strip()

    except Exception:
        return None


# --------------------------------------------------
# DOWNLOAD AUDIO FALLBACK
# --------------------------------------------------
def download_audio(url):
    """
    Fallback only.
    This can fail on Streamlit Cloud because YouTube blocks cloud IPs.
    """
    os.makedirs("downloads", exist_ok=True)

    output_path = "downloads/audio.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "no_warnings": False,

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },

        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        audio_file = "downloads/audio.mp3"

        if os.path.exists(audio_file):
            return audio_file

        files = os.listdir("downloads")
        audio_files = [
            f for f in files
            if f.endswith((".mp3", ".m4a", ".webm", ".opus", ".wav"))
        ]

        if audio_files:
            return os.path.join("downloads", audio_files[0])

        return None

    except Exception:
        st.warning(
            "YouTube blocked audio download on Streamlit Cloud. "
            "This usually happens because YouTube detected the server as a bot."
        )
        return None


# --------------------------------------------------
# TRANSCRIBE AUDIO FILE
# --------------------------------------------------
def transcribe_audio(audio_path):
    try:
        segments, info = model.transcribe(audio_path)

        transcript = ""
        for segment in segments:
            transcript += segment.text + " "

        return transcript.strip()

    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return None


# --------------------------------------------------
# SMART TRANSCRIPT FUNCTION
# --------------------------------------------------
def get_transcript_from_youtube(url):
    """
    Main function:
    1. Try YouTube captions first
    2. If captions fail, try yt-dlp audio download
    3. If download works, transcribe with Whisper
    4. If both fail, return None
    """
    transcript = get_youtube_captions(url)

    if transcript:
        return transcript

    audio_path = download_audio(url)

    if not audio_path:
        return None

    transcript = transcribe_audio(audio_path)

    if not transcript:
        return None

    return transcript


# --------------------------------------------------
# GROQ RESPONSE HELPER
# --------------------------------------------------
def ask_groq(prompt, system_message="You are a helpful assistant.", temperature=0.3):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
    )

    return response.choices[0].message.content


# --------------------------------------------------
# GENERATE SUMMARY
# --------------------------------------------------
def generate_summary(transcript):
    prompt = f"""
Summarize the following YouTube video transcript in a simple and useful way.

Include:
1. Short Summary
2. Key Points
3. Important Takeaways
4. Actionable Learning

Transcript:
{transcript}
"""

    return ask_groq(
        prompt,
        system_message="You are a helpful YouTube video summarizer.",
        temperature=0.3
    )


# --------------------------------------------------
# GENERATE TIMESTAMPS
# --------------------------------------------------
def generate_timestamps(transcript):
    prompt = f"""
Create useful timestamp-style sections from this transcript.

If exact timestamps are not available, create logical video sections like:
00:00 - Introduction
02:00 - Main Topic
05:00 - Key Explanation

Transcript:
{transcript}
"""

    return ask_groq(
        prompt,
        system_message="You create useful video timestamp sections.",
        temperature=0.3
    )


# --------------------------------------------------
# GENERATE TEXT MIND MAP
# --------------------------------------------------
def generate_mindmap(transcript):
    prompt = f"""
Create a clear text-based mind map from this YouTube transcript.

Format:
Main Topic
- Branch 1
  - Sub point
  - Sub point
- Branch 2
  - Sub point
  - Sub point

Transcript:
{transcript}
"""

    return ask_groq(
        prompt,
        system_message="You create clean mind maps from transcripts.",
        temperature=0.3
    )


# --------------------------------------------------
# CHAT WITH VIDEO
# --------------------------------------------------
def ask_video_question(transcript, question):
    prompt = f"""
Answer the user's question using only this video transcript.

If the answer is not available in the transcript, say:
"The video transcript does not contain enough information to answer this."

Transcript:
{transcript}

Question:
{question}
"""

    return ask_groq(
        prompt,
        system_message="You answer questions based on video transcripts.",
        temperature=0.2
    )


# --------------------------------------------------
# CREATE INTERACTIVE MIND MAP HTML
# --------------------------------------------------
def create_mindmap_html(mindmap_text, output_file="mindmap.html"):
    """
    Creates an interactive mind map HTML using PyVis.
    Works with text-based mindmap output.
    """
    try:
        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="#000000",
            directed=True
        )

        lines = [line.rstrip() for line in mindmap_text.split("\n") if line.strip()]

        if not lines:
            return None

        main_topic = lines[0].replace("#", "").replace("-", "").strip()
        net.add_node(main_topic, label=main_topic, color="#ffcc00", size=30)

        parent_stack = [(0, main_topic)]

        for line in lines[1:]:
            stripped = line.strip()
            clean_text = stripped.replace("-", "").replace("*", "").strip()

            if not clean_text:
                continue

            indent = len(line) - len(line.lstrip())

            while parent_stack and parent_stack[-1][0] >= indent:
                parent_stack.pop()

            parent = parent_stack[-1][1] if parent_stack else main_topic

            node_id = clean_text + str(indent) + str(len(parent_stack))

            net.add_node(node_id, label=clean_text, color="#87CEEB", size=18)
            net.add_edge(parent, node_id)

            parent_stack.append((indent, node_id))

        net.write_html(output_file)
        return output_file

    except Exception as e:
        st.error(f"Mind map HTML creation failed: {e}")
        return None
