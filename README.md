
# Multi-Agent AI System (LangGraph)

1. Architecture Overview
This project implements a **Supervisor-based Multi-Agent Workflow** using LangGraph. Three distinct AI agents collaborate via a shared `TypedDict` state to solve a user task. 

The 3 Agents:
1. Researcher: Gathers raw facts and uses tools (e.g., `word_count`).
2. Analyst: Critiques the research, finds gaps, and performs calculations using the `calculate` tool.
3. Writer: Synthesizes the research and analysis into a polished final answer.

The Coordinator (Supervisor):
The Supervisor reads the shared state and routes the task to the correct agent (Researcher ➔ Analyst ➔ Writer ➔ Finish). 

## 2. Model Choice: Ollama (Qwen 2.5 7B)
* **Why:** Fully local, zero API costs, no quota limits, and runs offline.
* **Trade-off:** Local models struggle with strict JSON formats. To ensure reliability, the Supervisor uses **Plain-Text Routing** (outputs a single word) parsed via Python, rather than Pydantic structured outputs. Qwen 2.5 7B was chosen over Llama 3.1 for its superior tool-calling reliability.

## 3. Reliability & Error Handling
* Sentinel Failures: If an agent's LLM call fails, it writes a `[failed]` flag to the state so the Supervisor moves on instead of looping infinitely.
* **Loop Guards:** The Supervisor hard-caps the workflow at 6 steps, preventing LangGraph `RecursionError`.
* **Deterministic Fallback:** If the Supervisor LLM crashes, Python logic dictates the next step.

## 4. Setup & Execution

**Prerequisites:** Python 3.10+, Ollama installed.

1. **Install dependencies:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Download the local model:**
   ```cmd
   ollama pull qwen2.5:7b
   ```

3. **Configure `.env`:**
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=qwen2.5:7b
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. **Run the system:**
   ```cmd
   venv\Scripts\python -u main.py
   ```