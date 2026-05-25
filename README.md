# 🎥 YouTube Video Summarizer

An AI-powered YouTube Video Summarizer that extracts audio from YouTube videos, converts speech into text, and generates concise, easy-to-read summaries using LLMs.

---

## 🚀 Project Flow

1. User enters a YouTube video URL
2. Audio is downloaded from the video
3. Speech is converted into text using Whisper
4. Transcript is processed by an LLM
5. AI generates:

   * Instant Summary
   * Key Insights
   * Interactive Timestamps
   * Mind Map
   * Complete Transcript
6. Results are displayed in a clean Streamlit UI

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **Backend:** Python
* **Speech-to-Text:** Faster Whisper / Whisper
* **LLM:** Groq API / OpenAI API
* **Video Processing:** yt-dlp
* **Visualization:** Plotly / Mind Map Libraries
* **Environment Management:** Python Virtual Environment (.venv)

---

## ✨ Features

* 📌 AI-generated video summaries
* 🧠 Mind map generation
* ⏱️ Interactive timestamps
* 📄 Full transcript extraction
* 💬 AI chat with video content
* 🎨 Clean and interactive UI

---

## ▶️ Run Locally

```bash
# Clone repository
git clone https://github.com/rohankshinde92/youtube-video-summarizer.git

# Move into project folder
cd youtube-video-summarizer

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app.py
```

---

## 📷 Example Workflow

```text
YouTube URL → Audio Extraction → Transcription → LLM Processing → AI Summary Output
```

---

## 📌 Future Improvements

* Multi-language support
* PDF export for summaries & mind maps
* User authentication
* Cloud deployment
* Real-time video analysis

---

## 👨‍💻 Author

Developed by **Rohan** 🚀
