import os
import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "").strip()

SYSTEM_PROMPT = """
You are MediMind AI, a health-education assistant.

Your role is limited to general, understandable health education.
Important safety rules:
- Never diagnose a person or claim that symptoms prove a disease.
- Never prescribe medicines, recommend dosages, or tell users to start,
  stop, or change medication.
- Explain that many symptoms have several possible causes.
- Encourage a qualified healthcare professional for personal assessment.
- For severe or rapidly worsening symptoms, trouble breathing, chest pain,
  fainting, seizures, severe allergic reactions, or other emergencies,
  advise the user to seek urgent medical help immediately and contact
  local emergency services.
- Do not ask for full name, address, phone number, passwords, or other
  identifying information.
- If asked something unrelated to health, politely say this chatbot is
  designed for general health education.
- Be calm, concise, non-judgmental, and use simple language.
- Do not present yourself as a doctor or a clinically validated system.
- If uncertain, say so rather than inventing facts.
This is educational information, not a diagnosis or substitute for care.
"""


def _get_tags():
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        payload = response.json()
        return payload.get("models", [])
    except requests.RequestException as error:
        raise RuntimeError(
            "Ollama is not reachable. Open the Ollama application and make sure it is running."
        ) from error


def get_available_model():
    if OLLAMA_MODEL:
        installed = [item.get("name", "") for item in _get_tags()]
        if OLLAMA_MODEL in installed:
            return OLLAMA_MODEL
        raise RuntimeError(
            f"The configured Ollama model '{OLLAMA_MODEL}' is not installed. "
            "Check the model name shown by the command: ollama list"
        )

    models = _get_tags()
    names = [item.get("name", "") for item in models if item.get("name")]

    if not names:
        raise RuntimeError(
            "No Ollama model is installed. Open a terminal and download a model with Ollama first."
        )

    # Prefer the Qwen models mentioned in the project setup, otherwise use
    # the first model Ollama reports as installed.
    for preferred in ("qwen2.5:3b", "qwen2.5:0.5b"):
        for name in names:
            if name.lower() == preferred:
                return name

    return names[0]


def chat_with_ollama(message, history=None):
    model = get_available_model()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Keep only a small amount of recent conversation in memory.
    if isinstance(history, list):
        for item in history[-8:]:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({
                    "role": role,
                    "content": content[:1200]
                })

    messages.append({"role": "user", "content": message})

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False
            },
            timeout=120
        )
        response.raise_for_status()
        payload = response.json()
        answer = payload.get("message", {}).get("content", "").strip()

        if not answer:
            raise RuntimeError("Ollama returned an empty response. Please try again.")

        return answer, model

    except requests.Timeout as error:
        raise RuntimeError(
            "The AI model is taking too long to respond. Please try again."
        ) from error
    except requests.RequestException as error:
        raise RuntimeError(
            "Could not get a response from Ollama. Check that Ollama is running and try again."
        ) from error
