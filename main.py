import streamlit as st
import streamlit.components.v1 as components
import json
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from utils import (
    download_audio,
    transcribe_audio,
    generate_summary,
    generate_timestamps,
    generate_mindmap,
    chat_with_video,
    create_mindmap_html
)

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Helper Function: Convert Mind Map to PDF
# --------------------------------------------------
def flatten_mindmap(data, level=0):
    """
    Converts nested dictionary/list mindmap data into readable text lines.
    """
    lines = []
    indent = "    " * level

    if isinstance(data, dict):
        for key, value in data.items():
            lines.append(f"{indent}• {key}")
            lines.extend(flatten_mindmap(value, level + 1))

    elif isinstance(data, list):
        for item in data:
            lines.extend(flatten_mindmap(item, level))

    else:
        lines.append(f"{indent}- {data}")

    return lines


def create_mindmap_pdf(mindmap_data):
    """
    Creates a PDF file in memory from mindmap JSON/dictionary data.
    This PDF is a text version of the mind map.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal_style = styles["BodyText"]

    story = []

    story.append(Paragraph("YouTube Video Mind Map", title_style))
    story.append(Spacer(1, 18))

    lines = flatten_mindmap(mindmap_data)

    if not lines:
        story.append(Paragraph("No mind map data available.", normal_style))
    else:
        for line in lines:
            safe_line = (
                line.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            story.append(Paragraph(safe_line, normal_style))
            story.append(Spacer(1, 6))

    doc.build(story)

    buffer.seek(0)
    return buffer


# --------------------------------------------------
# Custom CSS
# --------------------------------------------------
st.markdown(
    """
    <style>
    /* Full App Background */
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0f172a 45%, #111827 100%);
        color: #f8fafc;
    }

    /* Hide Streamlit default items */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    /* Hide "Press Enter to apply" text */
    div[data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }

    /* Main container */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Header Section */
    .hero-section {
        text-align: center;
        padding: 20px 10px 35px 10px;
    }

    .youtube-logo {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 82px !important;
        height: 58px !important;
        background: #ff0000 !important;
        background-color: #ff0000 !important;
        border-radius: 18px !important;
        box-shadow: 0 12px 30px rgba(239, 68, 68, 0.45) !important;
        margin-bottom: 18px !important;
    }

    .youtube-play {
        width: 0 !important;
        height: 0 !important;
        border-top: 13px solid transparent !important;
        border-bottom: 13px solid transparent !important;
        border-left: 22px solid #ffffff !important;
        margin-left: 5px !important;
    }

    .hero-title {
        font-size: 50px;
        font-weight: 900;
        color: #ffffff;
        margin-bottom: 10px;
        letter-spacing: -1px;
    }

    .hero-title span {
        color: #ef4444;
    }

    .hero-subtitle {
        font-size: 18px;
        color: #cbd5e1;
        max-width: 850px;
        margin: auto;
        line-height: 1.6;
    }

    /* Main Glass Card */
    .main-card {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 22px 50px rgba(0, 0, 0, 0.38);
        backdrop-filter: blur(14px);
        margin-bottom: 28px;
    }

    /* Feature Cards */
    .feature-card {
        background: rgba(255, 255, 255, 0.075);
        border: 1px solid rgba(255, 255, 255, 0.13);
        border-radius: 20px;
        padding: 22px 16px;
        text-align: center;
        min-height: 145px;
        box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
        transition: all 0.3s ease;
    }

    .feature-card:hover {
        transform: translateY(-6px);
        background: rgba(255, 255, 255, 0.11);
        border-color: rgba(56, 189, 248, 0.5);
    }

    .feature-icon {
        font-size: 34px;
        margin-bottom: 10px;
    }

    .feature-title {
        font-size: 18px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 8px;
    }

    .feature-text {
        font-size: 14px;
        color: #cbd5e1;
        line-height: 1.5;
    }

    /* Result Card */
    .result-card {
        background: rgba(15, 23, 42, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 20px;
        padding: 26px;
        margin-top: 18px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.30);
    }

    /* Note Box */
    .note-box {
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.20), rgba(245, 158, 11, 0.12));
        border-left: 6px solid #fbbf24;
        padding: 16px 20px;
        border-radius: 14px;
        color: #fde68a;
        font-size: 15px;
        line-height: 1.6;
        margin-top: 12px;
        margin-bottom: 22px;
    }

    /* Success Box */
    .success-box {
        background: rgba(34, 197, 94, 0.16);
        border-left: 6px solid #22c55e;
        padding: 16px 20px;
        border-radius: 14px;
        color: #bbf7d0;
        font-size: 15px;
        margin-top: 18px;
        line-height: 1.6;
    }

    /* Text Input */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.96);
        color: #111827;
        border-radius: 14px;
        border: 2px solid #38bdf8;
        padding: 14px;
        font-size: 16px;
    }

    .stTextInput > label {
        color: #e2e8f0 !important;
        font-weight: 700;
    }

    /* Text Area */
    .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.96);
        color: #111827;
        border-radius: 14px;
        border: 2px solid #38bdf8;
        font-size: 15px;
        padding: 14px;
    }

    .stTextArea label {
        color: #e2e8f0 !important;
        font-weight: 700;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 15px;
        height: 3.2rem;
        font-weight: 800;
        font-size: 16px;
        background: linear-gradient(135deg, #ef4444, #dc2626, #2563eb);
        color: white;
        border: none;
        box-shadow: 0 12px 26px rgba(239, 68, 68, 0.35);
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 34px rgba(37, 99, 235, 0.45);
        color: white;
    }

    /* Download Buttons */
    .stDownloadButton > button {
        width: 100%;
        border-radius: 15px;
        height: 3rem;
        font-weight: 800;
        font-size: 15px;
        background: linear-gradient(135deg, #16a34a, #22c55e);
        color: white;
        border: none;
        box-shadow: 0 10px 22px rgba(34, 197, 94, 0.30);
        transition: all 0.3s ease;
        margin-top: 15px;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 30px rgba(34, 197, 94, 0.40);
        color: white;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 13px 20px;
        color: #e2e8f0;
        font-weight: 800;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ef4444, #2563eb);
        color: white;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617, #0f172a);
        border-right: 1px solid rgba(255, 255, 255, 0.10);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #f8fafc !important;
    }

    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }

    p, li, span, div {
        color: inherit;
    }

    a {
        color: #38bdf8 !important;
        text-decoration: none;
        font-weight: 700;
    }

    a:hover {
        text-decoration: underline;
    }

    .section-heading {
        font-size: 26px;
        font-weight: 850;
        margin-bottom: 14px;
        color: #ffffff;
    }

    .muted-text {
        color: #94a3b8;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Header / Hero Section
# --------------------------------------------------
st.markdown(
    """
    <div class="hero-section">
        <div class="youtube-logo">
            <div class="youtube-play"></div>
        </div>
        <div class="hero-title">YouTube Video <span>Summarizer</span></div>
        <div class="hero-subtitle">
            Paste a YouTube video URL and get instant summary, clickable timestamps,
            interactive mind map, complete transcript, and AI chat support.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# Session State
# --------------------------------------------------
default_values = {
    "video_url": "",
    "transcript": "",
    "segments": [],
    "summary": "",
    "timestamps": "",
    "mindmap": {},
    "chat_history": [],
    "analysis_done": False
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --------------------------------------------------
# Feature Cards
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Fast Summary</div>
            <div class="feature-text">Quickly understand the main points of the video.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">⏱️</div>
            <div class="feature-title">Smart Timestamps</div>
            <div class="feature-text">Open important video moments with clickable links.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">Mind Map</div>
            <div class="feature-text">Visualize video topics in an interactive structure.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">AI Chat</div>
            <div class="feature-text">Ask questions directly from the video transcript.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------
# YouTube URL Input Section
# --------------------------------------------------
st.markdown('<div class="main-card">', unsafe_allow_html=True)

st.markdown(
    '<div class="section-heading">🔗 Paste YouTube Video Link</div>',
    unsafe_allow_html=True
)

youtube_url = st.text_input(
    "Enter YouTube Video URL",
    value=st.session_state.video_url,
    placeholder="Paste YouTube URL here..."
)

st.markdown(
    """
    <div class="note-box">
        <b>Important Note:</b><br>
        Since this is a basic model for project/demo purpose, kindly paste a YouTube video link of around
        <b>1 to 2 minutes</b> to get the output in approximately <b>30 seconds</b>.
    </div>
    """,
    unsafe_allow_html=True
)

analyze_clicked = st.button("▶️ Analyze Video")

st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# Analyze Video Logic
# --------------------------------------------------
if analyze_clicked:
    if not youtube_url.strip():
        st.warning("Please enter a YouTube video URL.")
    else:
        try:
            st.session_state.video_url = youtube_url
            st.session_state.analysis_done = False
            st.session_state.chat_history = []

            with st.status("Analyzing video...", expanded=True) as status:

                st.write("📥 Downloading audio...")
                audio_path = download_audio(youtube_url)

                st.write("🎧 Transcribing audio...")
                transcript, segments = transcribe_audio(audio_path)

                st.session_state.transcript = transcript
                st.session_state.segments = segments

                st.write("📝 Generating structured summary...")
                st.session_state.summary = generate_summary(transcript)

                st.write("⏱️ Generating interactive timestamps...")
                st.session_state.timestamps = generate_timestamps(segments)

                st.write("🧠 Generating mind map...")
                st.session_state.mindmap = generate_mindmap(transcript)

                st.session_state.analysis_done = True

                status.update(
                    label="Video analyzed successfully!",
                    state="complete",
                    expanded=False
                )

            st.markdown(
                """
                <div class="success-box">
                    ✅ Analysis completed successfully. Select each tab below to view the output separately.
                </div>
                """,
                unsafe_allow_html=True
            )

        except Exception as e:
            st.session_state.analysis_done = False
            st.error(f"Error: {e}")

# --------------------------------------------------
# Sidebar AI Chat
# --------------------------------------------------
st.sidebar.title("💬 Interactive AI Chat")
st.sidebar.markdown("Ask questions based on the analyzed video transcript.")

if st.session_state.analysis_done and st.session_state.transcript:
    st.sidebar.success("Video is ready for chat.")

    st.sidebar.markdown("### 🤖 Ask AI About This Video")
    st.sidebar.caption("Type your question below, then click the Ask AI button.")

    user_question = st.sidebar.text_input(
        "Your Question",
        placeholder="Type your question and click Ask AI"
    )

    if st.sidebar.button("🚀 Ask AI"):
        if user_question.strip():
            with st.sidebar.spinner("Generating answer..."):
                answer = chat_with_video(
                    st.session_state.transcript,
                    user_question
                )

            st.session_state.chat_history.append(
                {
                    "question": user_question,
                    "answer": answer
                }
            )

            st.sidebar.success("Answer generated.")
        else:
            st.sidebar.warning("Please enter a question.")

    if st.session_state.chat_history:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Chat History")

        for chat in reversed(st.session_state.chat_history):
            st.sidebar.markdown(f"**You:** {chat['question']}")
            st.sidebar.markdown(f"**AI:** {chat['answer']}")
            st.sidebar.markdown("---")

else:
    st.sidebar.info(
        "Analyze a video first. Chat will be available immediately after analysis."
    )

# --------------------------------------------------
# Results Section
# --------------------------------------------------
if st.session_state.analysis_done and st.session_state.transcript:

    st.markdown("---")
    st.header("📊 Video Analysis Results")

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📝 Instant Summary",
            "⏱️ Interactive Timestamps",
            "🧠 Mind Map",
            "📄 Complete Transcript"
        ]
    )

    # -----------------------------
    # Tab 1: Summary
    # -----------------------------
    with tab1:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.subheader("📝 Instant Summary")

        st.markdown(st.session_state.summary)

        st.download_button(
            label="⬇️ Download Summary",
            data=st.session_state.summary,
            file_name="youtube_summary.txt",
            mime="text/plain"
        )

        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------
    # Tab 2: Timestamps
    # -----------------------------
    with tab2:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.subheader("⏱️ Interactive Timestamps")

        if st.session_state.timestamps:
            timestamp_lines = st.session_state.timestamps.split("\n")

            for line in timestamp_lines:
                if line.strip():
                    try:
                        time_part = line.split("-")[0]
                        time_part = (
                            time_part
                            .replace("•", "")
                            .replace("-", "")
                            .strip()
                        )

                        minutes, seconds = time_part.split(":")
                        total_seconds = int(minutes) * 60 + int(seconds)

                        if "?" in st.session_state.video_url:
                            timestamp_link = (
                                f"{st.session_state.video_url}&t={total_seconds}s"
                            )
                        else:
                            timestamp_link = (
                                f"{st.session_state.video_url}?t={total_seconds}s"
                            )

                        st.markdown(f"🔹 [{line}]({timestamp_link})")

                    except Exception:
                        st.markdown(f"🔹 {line}")

            st.download_button(
                label="⬇️ Download Timestamps",
                data=st.session_state.timestamps,
                file_name="youtube_timestamps.txt",
                mime="text/plain"
            )

        else:
            st.info("No timestamps generated.")

        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------
    # Tab 3: Mind Map
    # -----------------------------
    with tab3:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.subheader("🧠 Interactive Mind Map")

        if st.session_state.mindmap:
            try:
                html_file = create_mindmap_html(st.session_state.mindmap)

                with open(html_file, "r", encoding="utf-8") as file:
                    html_content = file.read()

                components.html(
                    html_content,
                    height=650,
                    scrolling=True
                )

                mindmap_json = json.dumps(
                    st.session_state.mindmap,
                    indent=4,
                    ensure_ascii=False
                )

                mindmap_pdf = create_mindmap_pdf(st.session_state.mindmap)

                col_pdf, col_html, col_json = st.columns(3)

                with col_pdf:
                    st.download_button(
                        label="⬇️ Download Text PDF",
                        data=mindmap_pdf,
                        file_name="youtube_mindmap_text.pdf",
                        mime="application/pdf"
                    )

                with col_html:
                    st.download_button(
                        label="⬇️ Download Diagram HTML",
                        data=html_content,
                        file_name="youtube_mindmap_diagram.html",
                        mime="text/html"
                    )

                with col_json:
                    st.download_button(
                        label="⬇️ Download JSON",
                        data=mindmap_json,
                        file_name="youtube_mindmap.json",
                        mime="application/json"
                    )

                with st.expander("View Mind Map JSON"):
                    st.json(st.session_state.mindmap)

            except Exception as e:
                st.error(f"Mind map error: {e}")
                st.json(st.session_state.mindmap)
        else:
            st.info("No mind map generated.")

        st.markdown('</div>', unsafe_allow_html=True)

    # -----------------------------
    # Tab 4: Transcript
    # -----------------------------
    with tab4:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.subheader("📄 Complete Transcript")

        st.text_area(
            "Full Video Transcript",
            st.session_state.transcript,
            height=500
        )

        st.download_button(
            label="⬇️ Download Transcript",
            data=st.session_state.transcript,
            file_name="youtube_transcript.txt",
            mime="text/plain"
        )

        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Enter a YouTube URL and click Analyze Video to start.")
