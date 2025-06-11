# Nepali Transcribe and Translate 
The app to transcribe and translate Nepali language audio using python. 


## Folder Structure 
```
Nepali_transcribe_translate/ <br>
├── app.py                      # Streamlit frontend application <br>
├── llm_service.py              # Backend logic for LLM interactions <br>
├── .streamlit/                 # Streamlit configuration directory <br>
│   └── secrets.toml            # Secure storage for API keys<br>
├── notebooks/<br>
│   ├── transcription_test.ipynb # Jupyter notebook for testing transcription <br>
│   └── translation_test.ipynb   # Jupyter notebook for testing translation <br>
└── requirements.txt    <br>
```

## How to Run This Project
1. Set up your environment:
   - Install Python: Download and install Python (3.8+) from python.org.
   - Create a virtual environment (recommended):
  ```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```
   - Install dependencies:
```
pip install -r requirements.txt
```
2. Create API Key Storage:
   - Add your API key and default URLs to .streamlit/secrets.toml
     Remember to replace `YOUR_GEMINI_API_KEY_HERE` with your actual Gemini API key.
     
3. Run Streamlit App:
   - Navigate to your project root in the terminal.
   - Run:
```
streamlit run app.py
```
   - This will open the app in your web browser, usually at `http://localhost:8501`

## Practice Notebooks


