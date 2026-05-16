import os
import streamlit as st
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from utils import (
    get_transcript_from_youtube,
    transcribe_audio,
    generate_summary,
    generate_timestamps,
    generate_mindmap,
    ask_video_question,
    create_mindmap_html
)


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎬",
    layout="wide"
)


# --------------------------------------------------
# PDF GENERATOR
# --------------------------------------------------
def create_pdf(title, content):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    content = content.replace("\n", "<br/>")
    story.append(Paragraph(content, styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)

    return buffer


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

if "summary" not in st.session_state:
    st.session_state["summary"] = ""

if "timestamps" not in st.session_state:
    st.session_state["timestamps"] = ""

if "mindmap" not in st.session_state:
    st.session_state["mindmap"] = ""


# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🎬 YouTube Video Summarizer")
st.write("Paste a YouTube URL or upload an audio/video file to generate summary, timestamps, transcript, mind map, and chat with the video.")


# --------------------------------------------------
# INPUT SECTION
# --------------------------------------------------
st.subheader("1. Enter YouTube URL")

youtube_url = st.text_input("Paste YouTube video URL here")

analyze_button = st.button("Analyze Video")


# --------------------------------------------------
# YOUTUBE ANALYSIS
# --------------------------------------------------
if analyze_button:
    if not youtube_url.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()

    with st.spinner("Getting transcript from YouTube captions or audio..."):
        transcript = get_transcript_from_youtube(youtube_url)

    if not transcript:
        st.error(
            "Could not get transcript for this video. "
            "This can happen if captions are disabled or YouTube blocks server download. "
            "Please try another public YouTube video with captions, or upload an audio/video file below."
        )
        st.stop()

    st.session_state["transcript"] = transcript

    with st.spinner("Generating summary..."):
        st.session_state["summary"] = generate_summary(transcript)

    with st.spinner("Generating timestamps..."):
        st.session_state["timestamps"] = generate_timestamps(transcript)

    with st.spinner("Generating mind map..."):
        st.session_state["mindmap"] = generate_mindmap(transcript)

    st.success("Video analyzed successfully!")


# --------------------------------------------------
# FILE UPLOAD FALLBACK
# --------------------------------------------------
st.subheader("2. Or Upload Audio/Video File")

uploaded_file = st.file_uploader(
    "Upload audio/video file if YouTube blocks the video",
    type=["mp3", "wav", "m4a", "mp4", "webm"]
)

if uploaded_file is not None:
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Transcribing uploaded file..."):
        transcript = transcribe_audio(file_path)

    if transcript:
        st.session_state["transcript"] = transcript

        with st.spinner("Generating summary..."):
            st.session_state["summary"] = generate_summary(transcript)

        with st.spinner("Generating timestamps..."):
            st.session_state["timestamps"] = generate_timestamps(transcript)

        with st.spinner("Generating mind map..."):
            st.session_state["mindmap"] = generate_mindmap(transcript)

        st.success("Uploaded file analyzed successfully!")


# --------------------------------------------------
# OUTPUT SECTION
# --------------------------------------------------
if st.session_state["transcript"]:
    st.divider()
    st.subheader("Results")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Instant Summary",
            "Interactive Timestamps",
            "Mind Map",
            "Complete Transcript",
            "Ask AI"
        ]
    )

    # ----------------------------------------------
    # SUMMARY TAB
    # ----------------------------------------------
    with tab1:
        st.markdown(st.session_state["summary"])

        summary_pdf = create_pdf("YouTube Video Summary", st.session_state["summary"])

        st.download_button(
            label="Download Summary PDF",
            data=summary_pdf,
            file_name="summary.pdf",
            mime="application/pdf"
        )

    # ----------------------------------------------
    # TIMESTAMPS TAB
    # ----------------------------------------------
    with tab2:
        st.markdown(st.session_state["timestamps"])

        timestamps_pdf = create_pdf("Video Timestamps", st.session_state["timestamps"])

        st.download_button(
            label="Download Timestamps PDF",
            data=timestamps_pdf,
            file_name="timestamps.pdf",
            mime="application/pdf"
        )

    # ----------------------------------------------
    # MIND MAP TAB
    # ----------------------------------------------
    with tab3:
        st.markdown(st.session_state["mindmap"])

        mindmap_html = create_mindmap_html(st.session_state["mindmap"])

        if mindmap_html and os.path.exists(mindmap_html):
            with open(mindmap_html, "r", encoding="utf-8") as f:
                html_content = f.read()

            st.components.v1.html(html_content, height=650, scrolling=True)

            st.download_button(
                label="Download Interactive Mind Map HTML",
                data=html_content,
                file_name="mindmap.html",
                mime="text/html"
            )

        mindmap_pdf = create_pdf("Video Mind Map", st.session_state["mindmap"])

        st.download_button(
            label="Download Mind Map PDF",
            data=mindmap_pdf,
            file_name="mindmap.pdf",
            mime="application/pdf"
        )

    # ----------------------------------------------
    # TRANSCRIPT TAB
    # ----------------------------------------------
    with tab4:
        st.text_area(
            "Complete Transcript",
            st.session_state["transcript"],
            height=400
        )

        transcript_pdf = create_pdf("Complete Transcript", st.session_state["transcript"])

        st.download_button(
            label="Download Transcript PDF",
            data=transcript_pdf,
            file_name="transcript.pdf",
            mime="application/pdf"
        )

    # ----------------------------------------------
    # ASK AI TAB
    # ----------------------------------------------
    with tab5:
        question = st.text_input("Ask AI about this video", placeholder="Type your question and press Ask AI")

        if st.button("Ask AI"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("AI is answering..."):
                    answer = ask_video_question(
                        st.session_state["transcript"],
                        question
                    )

                st.markdown(answer)
