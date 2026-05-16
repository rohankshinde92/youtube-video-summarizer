import os
import json
import yt_dlp
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from groq import Groq

load_dotenv()

# Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Faster Whisper model
# You can use: tiny, base, small, medium
model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)


def download_audio(youtube_url):
    """
    Downloads audio from YouTube video.
    Returns audio file path.
    """

    os.makedirs("downloads", exist_ok=True)

    output_template = "downloads/audio.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])

    audio_path = "downloads/audio.mp3"

    if not os.path.exists(audio_path):
        raise FileNotFoundError("Audio file was not created. Check FFmpeg installation.")

    return audio_path


def transcribe_audio(audio_path):
    """
    Transcribes audio using Faster Whisper.
    Returns:
    - full transcript
    - timestamped segments
    """

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True
    )

    transcript = ""
    timestamped_segments = []

    for segment in segments:
        start = round(segment.start, 2)
        end = round(segment.end, 2)
        text = segment.text.strip()

        transcript += text + " "

        timestamped_segments.append(
            {
                "start": start,
                "end": end,
                "text": text
            }
        )

    return transcript.strip(), timestamped_segments


def seconds_to_timestamp(seconds):
    """
    Converts seconds to YouTube timestamp format.
    Example: 75 -> 01:15
    """

    seconds = int(seconds)
    minutes = seconds // 60
    sec = seconds % 60

    return f"{minutes:02d}:{sec:02d}"


def generate_summary(transcript):
    """
    Generates structured summary from transcript.
    """

    prompt = f"""
You are an expert YouTube video summarizer.

Analyze the transcript and generate a clear structured summary.

Return the answer in this format:

## Key Topics
- topic 1
- topic 2

## Core Takeaways
- takeaway 1
- takeaway 2

## Main Themes
- theme 1
- theme 2

## Short Summary
Write a simple useful summary in 5-8 lines.

Transcript:
{transcript}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You summarize video transcripts into structured notes."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def generate_timestamps(timestamped_segments):
    """
    Generates important clickable timestamp points.
    """

    combined_text = ""

    for segment in timestamped_segments:
        time_text = seconds_to_timestamp(segment["start"])
        combined_text += f"[{time_text}] {segment['text']}\n"

    prompt = f"""
You are analyzing a YouTube transcript with timestamps.

Create important video timeline points.

Return only this format:

- 00:00 - Introduction
- 01:25 - Main concept explained
- 03:40 - Example or demo
- 06:15 - Final conclusion

Timestamped Transcript:
{combined_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You create useful video navigation timestamps."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


def generate_mindmap(transcript):
    """
    Generates mind map structure in JSON.
    """

    prompt = f"""
Create a hierarchical mind map from this video transcript.

Return valid JSON only.

Use this format:

{{
  "title": "Main Video Topic",
  "children": [
    {{
      "title": "Main Idea 1",
      "children": [
        {{"title": "Sub point 1"}},
        {{"title": "Sub point 2"}}
      ]
    }},
    {{
      "title": "Main Idea 2",
      "children": [
        {{"title": "Sub point 1"}},
        {{"title": "Sub point 2"}}
      ]
    }}
  ]
}}

Transcript:
{transcript}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You generate valid JSON mind maps from transcripts."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    result = response.choices[0].message.content

    try:
        return json.loads(result)
    except Exception:
        return {
            "title": "Video Mind Map",
            "children": [
                {
                    "title": "Could not parse mind map JSON",
                    "children": [
                        {"title": result}
                    ]
                }
            ]
        }


def chat_with_video(transcript, user_question):
    """
    Answers user question using transcript context.
    """

    prompt = f"""
You are an AI assistant that answers questions only from the video transcript.

If the answer is not available in the transcript, say:
"The video transcript does not contain enough information to answer this."

Transcript:
{transcript}

User Question:
{user_question}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You answer questions based only on the provided video transcript."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


from pyvis.network import Network


def create_mindmap_html(mindmap_data, output_file="mindmap.html"):
    """
    Creates interactive mind map HTML using PyVis.
    """

    net = Network(
        height="600px",
        width="100%",
        bgcolor="#ffffff",
        font_color="black",
        directed=True
    )

    def add_nodes_edges(node, parent=None):
        title = node.get("title", "Untitled")

        net.add_node(title, label=title)

        if parent:
            net.add_edge(parent, title)

        for child in node.get("children", []):
            add_nodes_edges(child, title)

    add_nodes_edges(mindmap_data)

    net.repulsion(
        node_distance=180,
        central_gravity=0.2,
        spring_length=200,
        spring_strength=0.05
    )

    net.save_graph(output_file)

    return output_file
