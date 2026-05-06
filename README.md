# 🧠 AI Consensus Engine v1.0

A **multi-model AI debate & consensus system** that runs 3 different LLMs locally via [Ollama](https://ollama.ai). Ask a question and watch the models debate, critique each other, and converge on a single, non-diplomatic definitive answer.

---

## ✨ How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  1. INITIAL ANSWERS   →  All 3 models answer independently     │
│  2. CRITIQUE PHASE    →  Each model critiques the other two    │
│  3. REFINEMENT        →  Each model improves using critiques   │
│  4. CONSENSUS         →  Final synthesized decisive answer     │
└─────────────────────────────────────────────────────────────────┘
```

The system leverages **diversity of thought** from three different AI architectures:

| Model | Company | Strength |
|-------|---------|----------|
| **Gemma 2** (`gemma:2b`) | Google | Balanced reasoning, structured output |
| **DeepSeek R1** (`deepseek-r1:7b`) | DeepSeek | Chain-of-thought reasoning specialist |
| **Llama 3.1** (`llama3.1:8b`) | Meta | Versatile general-purpose model |

---

## 🖥️ Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **VRAM** | 6 GB | 8 GB+ |
| **RAM** | 16 GB | 16 GB+ |
| **Disk** | 10 GB free | 20 GB free |
| **GPU** | NVIDIA GTX 1060+ | RTX 3050+ |

> **Note:** Models are loaded one at a time — Ollama handles swapping automatically.
> A full debate takes ~1–3 minutes depending on your hardware.

---

## 🚀 Quick Start

### 1. Install Ollama

Download from [ollama.ai](https://ollama.ai) and install it. Make sure it's running:

```bash
ollama serve
```

### 2. Pull the Models

```bash
ollama pull gemma:2b
ollama pull deepseek-r1:7b
ollama pull llama3.1:8b
```

### 3. Install Python Dependencies

```bash
cd consensus/backend
pip install -r requirements.txt
```

### 4. Start the Server

```bash
python main.py
```

### 5. Open the UI

Navigate to **http://localhost:8000** in your browser.

---

## 📁 Project Structure

```
consensus/
├── backend/
│   ├── main.py              # FastAPI server & API endpoints
│   ├── debate.py            # Debate orchestration engine
│   ├── ollama_client.py     # Async Ollama API wrapper
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Web UI structure
│   ├── style.css            # Holographic futuristic theme
│   └── app.js               # Frontend logic & SSE streaming
└── README.md                # This file
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Check if Ollama is running |
| `GET` | `/api/models` | List configured models & availability |
| `POST` | `/api/debate` | Start a new debate (SSE stream) |
| `GET` | `/` | Serve the web UI |

### Start a Debate

```bash
curl -X POST http://localhost:8000/api/debate \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the best way to learn programming?", "rounds": 2}'
```

---

## ⚙️ Configuration

Edit `debate.py` to customize:

- **`MODELS`** — Change which models participate in the debate
- **`max_rounds`** — Number of critique/refine rounds (1–5)
- **System prompts** — Adjust the tone and rigor of the debate
- **Temperature** — Adjust creativity in `ollama_client.py` (default: 0.7)

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| "OFFLINE" in header | Make sure `ollama serve` is running |
| Model not available | Run `ollama pull <model-name>` |
| Slow responses | Normal — models run one at a time. Reduce rounds to 1 |
| Connection error | Check if port 11434 (Ollama) and 8000 (app) are free |

---

## 📝 License

This project is for personal/educational use. The LLM models have their own licenses:
- Gemma 2: [Google Gemma License](https://ai.google.dev/gemma/terms)
- DeepSeek R1: [DeepSeek License](https://github.com/deepseek-ai/DeepSeek-R1/blob/main/LICENSE)
- Llama 3.1: [Meta Llama License](https://llama.meta.com/llama3/license/)
