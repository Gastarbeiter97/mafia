# 🕵️ Mafia AI

**🎮 [Play it live](https://mafiaai.streamlit.app)**

A multi-agent social deduction game where 5 AI players each have secret roles, lie, accuse each other, and vote — powered by LLM APIs.

## Features
- **5 autonomous AI agents**, each with a hidden role (mafia, doctor, detective, citizen) and its own personality
- **Information isolation** — each AI only knows what its role should know
- **Night & day phases** — mafia kills, doctor saves, detective investigates, then the town discusses and votes
- **Multi-provider failover** — rotates across Groq, Cerebras, and Gemini so one dead API never stops the game
- **Post-game AI analysis** — a commentator-style recap of who played well
- **Two interfaces** — terminal (`mafia.py`) and web UI (`mafia_app.py`, built with Streamlit)

## Tech
Python · LLM APIs (Groq / Gemini / Cerebras) · Streamlit

## Run it
1. Install dependencies:
```
pip install -r requirements.txt
```
2. Create a `.env` file with your API keys:
```
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
CEREBRAS_API_KEY=your_key
```
3. Terminal version: `python mafia.py`
4. Web version: `streamlit run mafia_app.py`

## Concepts demonstrated
Multi-agent orchestration · prompt engineering · structured JSON output · API fallback design · dictionaries, list comprehensions, functions · Streamlit session state