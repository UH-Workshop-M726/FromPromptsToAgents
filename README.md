# From Prompt to Agent: Your First Intelligent AI System

**Workshop | 18 April 2026 | University of Hertfordshire**

---

## Presenters

| Presenter                     | Role                                   | LinkedIn                                                         |
| ----------------------------- | -------------------------------------- | ---------------------------------------------------------------- |
| **Abolfazl Zaraki**           | Senior Lecturer in Robotics and AI     | [Profile](https://www.linkedin.com/in/abolfazl-zaraki-8b48b12a/) |
| **M. Reza Shahabian A.**      | Principal AI Engineer \| AI Researcher | [Profile](https://www.linkedin.com/in/mrshahabian/)              |
| **Khashayar Ghamati**         | Principal AI Engineer \| AI Researcher | [Profile](https://www.linkedin.com/in/khashayarghamati/)         |
| **Ali Fallahi**               | AI UX Researcher \| HRI                | [Profile](https://www.linkedin.com/in/ali-fallahi/)              |
| **Danial Zafaranchizadeh M.** | AI Engineer \| Robotics Researcher     | [Profile](https://www.linkedin.com/in/danial-za/)                |

Brought to you by **PARSAI** and the **School of Physics, Engineering and Computer Science, University of Hertfordshire**.

---

## Quick Start

```bash
git clone https://github.com/UH-Workshop-M726/FromPromptsToAgents.git
cd FromPromtsToAgents/
```

Each session is self-contained. Follow the steps in order within each session folder.

---

## Python Environment Setup

Create a virtual environment once at the root of the repo, then activate it before running any session code.

**Create and activate:**

```bash
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (Command Prompt):
.venv\Scripts\activate.bat

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

Your prompt will show `(.venv)` when the environment is active.

**Install dependencies for the session you are working on:**

```bash
pip install -r session1/requirements.txt   # repeat for each session as needed
```

> **Tip:** You only need to create the virtual environment once. Just re-run the `activate` command each time you open a new terminal.

---

## LLM Setup — Choose Your Backend

This workshop supports **two LLM backends**. You need at least one working.

### Option 1: Local University LLM (Primary)

The university runs **Qwen2.5-72B-Instruct** on a GPU cluster. This is the best option during the workshop — no SSH tunnel required, just set your `.env`:

```
LLM_SERVICE_URL=https://uhhpc.herts.ac.uk/qwen
LLM_API_TOKEN=your-token-here
```

The workshop instructor will provide the token on the day.

### Option 2: Google Gemini (Free Fallback)

If the local service is down or you're working from home, use Google Gemini. It's **free** and takes 2 minutes to set up.

**Setup:**

1. Go to **https://aistudio.google.com**
2. Sign in with your Google account
3. Click **"Get API Key"** in the left sidebar
4. Click **"Create API key"** → select any project → copy the key
5. keep the API key somewhere safe then copy it to the to .env on each session:
   In your `.env` file set:
   `      GEMINI_API_KEY=your-key-here
    `

That's it! The code automatically detects which backend is available and uses it.

**Test your connection:**

```bash
cd session1
cp .env.example .env      # Copy the template
# Then open .env and fill in your key(s) — see options above
python llm_client.py
```

You should see `Backend: local` or `Backend: gemini` and a test response.

> **"No backend available"?** This means your `.env` file is missing or the keys are not filled in.
> Make sure you copied `.env.example` to `.env` and set at least one of `LLM_API_TOKEN` or `GEMINI_API_KEY`.

---

## How to Follow Along — Step by Step

Each session has a `steps/` folder with numbered files. **Run them in order:**

### Session 1 : Building Blocks

```bash
cd session1
pip install -r requirements.txt
cp .env.example .env        # Edit with your keys

python steps/step1_hello_llm.py          # Your first LLM call
python steps/step2_conversation.py       # Multi-turn chat
python steps/step3_temperature.py        # Temperature comparison
streamlit run steps/step4_chatbot.py     # Build a chatbot UI
streamlit run steps/step5_personas.py    # Prompt engineering
```

### Session 2 : MCP & Robotics Agent

```bash
cd session2
pip install -r requirements.txt
cp .env.example .env

python steps/step1_explore_data.py       # Browse the parts database
python steps/step2_test_tools.py         # Test MCP tools directly
python steps/step3_run_agent.py          # Run the full agent!
```

### Session 3 : RAG Concepts

```bash
cd session3
pip install -r requirements.txt
cp .env.example .env

python rag_demo.py                       # See RAG in action (demo only)
streamlit run rag_streamlit.py
```

### Session 4 : Recipe Agent

```bash
cd session4
pip install -r requirements.txt
cp .env.example .env

python steps/step1_explore_dishes.py     # Browse the recipe database
python steps/step2_test_tools.py         # Test recipe tools
python steps/step3_run_agent.py          # Run the recipe agent
```

### Session 5 : A2A

```bash
cd session5
pip install -r requirements.txt
cp .env.example .env

streamlit run app.py                     # Run the full platform!
```

---

## Prerequisites

- Python 3.10+
- A Google account (for Gemini API key)
- A code editor (VS Code recommended)
- A GitHub account (for challenge submission)

---

## Troubleshooting

**"No LLM backend available"**
→ Check your `.env` file has either a working `LLM_API_TOKEN` or `GEMINI_API_KEY`.

**"ModuleNotFoundError"**
→ Make sure you ran `pip install -r requirements.txt` in the current session folder.

**Gemini 429 Too Many Requests**
→ The shared workshop key is rate-limited. You must get your own free key:

1. Go to **https://aistudio.google.com** → sign in → click **"Get API Key"**
2. Click **"Create API key"** → copy it
3. Open your `.env` file and replace the existing value: `GEMINI_API_KEY=your-new-key`

**Gemini returns another error**
→ Check your API key at https://aistudio.google.com. The free tier has rate limits (15 requests/minute).

**Streamlit text box not accepting keyboard input**
→ Run `streamlit run` from a **standalone terminal**, not from inside PyCharm or VS Code. IDE-embedded terminals keep keyboard focus and intercept your keystrokes.

**Local service not reachable**
→ Check your `LLM_SERVICE_URL` and `LLM_API_TOKEN` in `.env`. Try `curl https://uhhpc.herts.ac.uk/qwen/health` to verify the service is up.

---

## Community & Communication

Join our Discord to ask questions, share progress, and connect with other participants:

**Discord:** https://discord.gg/UGsfhZq3

---

**The Workshop Team — PARSAI**
School of Physics, Engineering and Computer Science | University of Hertfordshire
