# app.py
import streamlit as st
import base64
import io
import os # For environment variables
from llm_service import transcribe_audio_gemini, translate_text

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Nepali Audio Translator",
    page_icon="🔊",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- Global State for UI elements ---
# Storing API keys and URLs in Streamlit's session state
# Initialize default values from environment variables or Streamlit secrets
# For local development, you might set these in a .env file or directly.
# For deployed Streamlit apps, use Streamlit secrets.
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = st.secrets.get("GEMINI_API_KEY", "") # Fallback to empty string
if 'translation_model_provider' not in st.session_state:
    st.session_state.translation_model_provider = st.secrets.get("TRANSLATION_MODEL_PROVIDER", "Gemini")
if 'ollama_base_url' not in st.session_state:
    st.session_state.ollama_base_url = st.secrets.get("OLLAMA_BASE_URL", "http://localhost:11434")
if 'ollama_model_name' not in st.session_state:
    st.session_state.ollama_model_name = st.secrets.get("OLLAMA_MODEL_NAME", "llama2")
if 'vllm_base_url' not in st.session_state:
    st.session_state.vllm_base_url = st.secrets.get("VLLM_BASE_URL", "http://localhost:8000")

# --- Function to handle transcription and translation ---
def process_audio(audio_bytes, audio_mime_type):
    st.session_state.nepali_text = ""
    st.session_state.english_text = ""
    st.session_state.error = ""

    if not st.session_state.gemini_api_key:
        st.session_state.error = "Gemini API Key is required for audio transcription. Please set it in Settings."
        return

    try:
        # 1. Transcribe Nepali audio using Gemini (backend call)
        with st.spinner("Transcribing Nepali audio..."):
            nepali_text = transcribe_audio_gemini(
                audio_bytes=audio_bytes,
                mime_type=audio_mime_type,
                gemini_api_key=st.session_state.gemini_api_key
            )
        st.session_state.nepali_text = nepali_text

        # 2. Translate Nepali text to English (backend call based on selected provider)
        with st.spinner("Translating to English..."):
            english_text = translate_text(
                text_to_translate=nepali_text,
                target_language="English",
                model_provider=st.session_state.translation_model_provider,
                gemini_api_key=st.session_state.gemini_api_key, # Gemini key for Gemini translation if chosen
                ollama_base_url=st.session_state.ollama_base_url,
                ollama_model_name=st.session_state.ollama_model_name,
                vllm_base_url=st.session_state.vllm_base_url
            )
        st.session_state.english_text = english_text

    except Exception as e:
        st.session_state.error = f"An error occurred: {e}"

# --- Title and Description ---
st.title("🔊 Nepali Audio Translator")
st.markdown("Upload Nepali audio or record live to get transcription and English translation.")

# --- Settings Section (in sidebar for cleaner UI) ---
with st.sidebar:
    st.header("⚙️ Settings")

    # API Key for Gemini (for Transcription)
    st.subheader("API Keys & Endpoints")
    st.text_input(
        "Gemini API Key",
        type="password",
        value=st.session_state.gemini_api_key,
        key="gemini_api_key_input", # Unique key for this widget
        help="Required for audio transcription. Also used for Gemini translation.",
        on_change=lambda: st.session_state.__setitem__('gemini_api_key', st.session_state.gemini_api_key_input)
    )
    st.caption("Get your key from [Google AI Studio](https://aistudio.google.com/app/apikey)")

    # Translation Model Provider Selection
    st.subheader("Translation Model Provider")
    st.radio(
        "Select your preferred LLM for translation:",
        ("Gemini", "Ollama", "vLLM"),
        index=("Gemini", "Ollama", "vLLM").index(st.session_state.translation_model_provider),
        key="translation_model_provider_radio", # Unique key
        on_change=lambda: st.session_state.__setitem__('translation_model_provider', st.session_state.translation_model_provider_radio)
    )

    # Ollama Settings
    if st.session_state.translation_model_provider == "Ollama":
        st.subheader("Ollama Settings")
        st.text_input(
            "Ollama Base URL",
            value=st.session_state.ollama_base_url,
            key="ollama_base_url_input",
            help="e.g., http://localhost:11434",
            on_change=lambda: st.session_state.__setitem__('ollama_base_url', st.session_state.ollama_base_url_input)
        )
        st.text_input(
            "Ollama Model Name",
            value=st.session_state.ollama_model_name,
            key="ollama_model_name_input",
            help="e.g., llama2, gemma:2b",
            on_change=lambda: st.session_state.__setitem__('ollama_model_name', st.session_state.ollama_model_name_input)
        )
        st.caption("Ensure Ollama is running and the model is downloaded.")

    # vLLM Settings
    if st.session_state.translation_model_provider == "vLLM":
        st.subheader("vLLM Settings")
        st.text_input(
            "vLLM Base URL",
            value=st.session_state.vllm_base_url,
            key="vllm_base_url_input",
            help="e.g., http://localhost:8000",
            on_change=lambda: st.session_state.__setitem__('vllm_base_url', st.session_state.vllm_base_url_input)
        )
        st.caption("Ensure vLLM is running and accessible (typically serves OpenAI-compatible API).")

    # Save settings are automatically handled by st.session_state and on_change callbacks.
    # No explicit "Save Settings" button needed for simple inputs.

# --- Audio Input Section ---
st.subheader("Input Audio")

uploaded_file = st.file_uploader("Upload an audio file (MP3, WAV, OGG, WebM, etc.)", type=["mp3", "wav", "ogg", "webm"])

if uploaded_file is not None:
    # Read the audio file bytes
    audio_bytes = uploaded_file.read()
    audio_mime_type = uploaded_file.type

    st.audio(audio_bytes, format=audio_mime_type)

    if st.button("Transcribe & Translate"):
        process_audio(audio_bytes, audio_mime_type)

# --- Live Microphone Input (Experimental) ---
# Note: Direct, robust live microphone input in Streamlit is complex and often requires
# custom components or specific hosting environments. For simplicity in this example,
# we'll stick to file upload. If live mic is crucial, you'd need to explore:
# - streamlit-webrtc (complex setup, requires media servers)
# - Saving recording client-side to a file then uploading (user workflow can be clunky)
# For now, this is a placeholder.

# st.subheader("Or Record Live Audio")
# if st.button("Start Recording"):
#     st.warning("Live recording functionality is experimental and might require specific browser/server setups.")
#     # Placeholder for live recording logic
#     st.session_state.error = "Live recording is not fully implemented in this version for simplicity."
# if st.button("Stop Recording"):
#     pass # Placeholder

# --- Results Display ---
st.subheader("Results")

if 'error' in st.session_state and st.session_state.error:
    st.error(st.session_state.error)

if 'nepali_text' in st.session_state and st.session_state.nepali_text:
    st.info("### Nepali Transcription")
    st.write(st.session_state.nepali_text)

if 'english_text' in st.session_state and st.session_state.english_text:
    st.info("### English Translation")
    st.write(st.session_state.english_text)

# --- History Section (in-memory for this version) ---
# For a "big project," you would integrate with a database like SQLite, PostgreSQL,
# or a cloud database like Firestore (via Python SDK) for persistent history.
# For now, it's a simple append to a list in session_state
if 'history' not in st.session_state:
    st.session_state.history = []

# Example of adding to history (you'd integrate this within process_audio success path)
# This part is illustrative; you'd want to add a structured record.
if 'nepali_text' in st.session_state and st.session_state.nepali_text and \
   'english_text' in st.session_state and st.session_state.english_text and \
   st.button("Add to History (Session Only)"):
    st.session_state.history.insert(0, { # Insert at beginning for most recent on top
        "timestamp": st.session_state.get("last_processed_time", "N/A"),
        "nepali": st.session_state.nepali_text,
        "english": st.session_state.english_text,
        "provider": st.session_state.translation_model_provider
    })
    st.session_state.nepali_text = "" # Clear current results after adding
    st.session_state.english_text = ""

if st.session_state.history:
    st.subheader("Recent History (Current Session)")
    for i, entry in enumerate(st.session_state.history):
        st.expander(f"Entry {i+1} ({entry['timestamp'] or 'No Time'}) - {entry['provider']}")
        st.write(f"**Nepali:** {entry['nepali']}")
        st.write(f"**English:** {entry['english']}")
        st.write(f"**Provider:** {entry['provider']}")

