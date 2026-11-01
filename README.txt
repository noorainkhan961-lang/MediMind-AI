MEDIMIND AI — COMPLETE EDUCATIONAL PROTOTYPE
================================================

WHAT IS INCLUDED
- Flask website and responsive interface
- Registration and dashboard
- Symptom explorer (simple rule-based educational possibilities, not diagnosis)
- Ollama-powered general health information chatbot
- Health profile and medical history
- Manual test-result entry
- PDF/JPG/JPEG/PNG report upload (5 MB maximum per file)
- Saved-record list, download and delete
- Health overview counters and recent-record timeline
- SQLite local database

REQUIREMENTS
- Python 3.10 or newer
- Ollama installed and running
- One Ollama model installed (the project prefers qwen2.5:3b or qwen2.5:0.5b)

RUN ON WINDOWS (VS CODE)
1. Extract the ZIP.
2. Open the INNER folder named MediMind-AI-Ollama in VS Code.
   It must contain app.py, requirements.txt, backend, frontend and static.
3. Open Terminal > New Terminal.
4. Install Python packages:
      python -m pip install -r requirements.txt
5. Check installed Ollama models:
      ollama list
6. If you want to choose the smaller Qwen model in Git Bash:
      export OLLAMA_MODEL=qwen2.5:0.5b
   In PowerShell use:
      $env:OLLAMA_MODEL="qwen2.5:0.5b"
   Use the exact model tag shown by `ollama list`.
7. Make sure the Ollama application is running.
8. Start the website:
      python app.py
9. Open:
      http://127.0.0.1:5000

STOP THE SERVER
- In the terminal where Flask is running, press Ctrl+C.

LOCAL DATA
- Profile and manually entered results: medimind.db
- Uploaded reports: uploads/
- Back up BOTH medimind.db and uploads/ if you want to preserve the records.
- These files are created automatically when the app starts / files are uploaded.

IMPORTANT LIMITATIONS
- This is a student educational prototype, not a medical device or clinical record system.
- Symptom results are basic keyword-based possibilities and may be incomplete or wrong.
- The chatbot can make mistakes. It must not be used for diagnosis, treatment decisions,
  medication selection or dosage advice. Seek a qualified healthcare professional.
- The app does not currently encrypt medical records, provide secure user accounts,
  implement role-based access, or meet healthcare privacy/compliance requirements.
- Do not use real sensitive medical records, shared/public computers, or expose this
  development server or Ollama endpoint to the internet.
- Uploaded files are stored locally. The app does not extract or interpret report contents.
- Test only with fictional/sample information for demonstrations.

PROJECT STRUCTURE
MediMind-AI-Ollama/
  app.py
  requirements.txt
  medimind.db          (created at runtime)
  backend/
    __init__.py
    chatbot.py
    symptom_analyzer.py
  frontend/
    index.html
  static/
    script.js
    style.css
  uploads/             (created / used for uploaded files)
  README.txt
