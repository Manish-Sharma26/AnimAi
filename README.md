# 🎬 AnimAI Studio

AI-powered educational animation generator that creates professional Manim animations from natural language descriptions.

## ✨ Features

- 🤖 **AI-Powered Planning**: Automatic animation structure planning using LLM
- 🎨 **Professional Design System**: Consistent dark theme with stunning visuals
- 🔄 **Self-Healing Code**: Automatic debugging and retry logic
- 🎙️ **Voice Narration**: Built-in text-to-speech for educational voiceovers
- 📚 **RAG-Enhanced**: Retrieves relevant Manim patterns from documentation
- 📈 **Learning System**: Improves over time from user feedback
- 🔒 **Safe Execution**: Docker-isolated code compilation

## 📋 Prerequisites

- Python 3.9 or higher
- Docker Desktop installed and running
- FFmpeg installed (for audio merging)
- Groq API key ([get one free at Groq](https://console.groq.com))

## 🚀 Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/animai-studio.git
   cd animai-studio
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

5. **Build Docker image**
   ```bash
   docker build -t manim-voiceover .
   ```

6. **Initialize RAG system** (first time only)
   ```bash
   python rag/download_docs.py
   ```
   This downloads Manim documentation and builds the search index (~2-3 minutes).

7. **Run the application**
   ```bash
   streamlit run app.py
   ```

8. **Open your browser**
   
   Navigate to `http://localhost:8501`

## 🎯 Usage

1. Enter a description of the animation you want (e.g., "Animate bubble sort with array 5 2 8 1 9")
2. Click "Generate Animation"
3. Wait for the AI to plan, code, compile, and add voice narration
4. Watch your animation and download the MP4
5. Give feedback to help the system learn!

## 📁 Project Structure

```
animai-studio/
├── app.py                      # Streamlit web interface
├── Dockerfile                  # Docker image configuration
├── agent/                      # AI agent system
│   ├── orchestrator.py         # Main pipeline coordinator
│   ├── planner.py              # Animation structure planner
│   ├── coder.py                # Manim code generator
│   ├── debugger.py             # Automatic error fixing
│   ├── llm.py                  # LLM API wrapper
│   └── feedback.py             # Learning from user feedback
├── sandbox/                    # Isolated execution
│   ├── sandbox.py              # Docker-based Manim runner
│   └── audio_merger.py         # TTS and video merging
├── rag/                        # Retrieval-Augmented Generation
│   ├── download_docs.py        # Doc scraper and indexer
│   ├── retriever.py            # Vector similarity search
│   ├── manim_chunks.json       # Documentation chunks
│   └── manim_docs.index        # FAISS search index
└── outputs/                    # Generated videos
```

## 🧪 Testing

Run individual tests to verify setup:

```bash
# Test Manim sandbox
python test_sandbox.py

# Test full pipeline
python test_agent.py

# Test audio generation
python test_audio.py
```

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **LLM**: Groq (Llama-3.3 70B)
- **Animation**: Manim Community Edition
- **Execution**: Docker
- **RAG**: FAISS + Sentence Transformers
- **TTS**: Google Text-to-Speech (gTTS)
- **Video Processing**: FFmpeg

## 🎨 Visual Styles

The system automatically chooses the best visual style:

- `array_boxes` - Data structures, search algorithms
- `bar_chart` - Sorting algorithms, comparisons
- `diagram` - Biology, chemistry, science concepts
- `graph_plot` - Mathematical functions, equations
- `physics_motion` - Moving objects, forces, trajectories
- `timeline` - History, sequences, processes
- `flowchart` - Decision trees, workflows

## 🤝 Contributing

Contributions welcome! The system learns from feedback, so the more you use it, the better it gets.

## 📝 License

MIT License - feel free to use for educational purposes!

## ⚠️ Security Note

- Never commit your `.env` file
- Keep your Groq API key private
- Regenerate your API key if accidentally exposed

## 🐛 Troubleshooting

**Docker connection error**: Make sure Docker Desktop is running

**FFmpeg not found**: Install FFmpeg and add to system PATH

**Groq API error**: Verify your API key in `.env` file

**No video generated**: Check Docker logs with `docker logs <container_id>`

## 📧 Support

For issues and questions, please open a GitHub issue.

---

Built with ❤️ for educators and students everywhere
