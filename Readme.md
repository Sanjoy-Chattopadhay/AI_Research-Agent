# 🔬 AI Research Agent - Advanced Multi-Agent System

> **Tech Stack:** LangChain, React, FastAPI, OpenAI GPT-4  
> **Type:** Production-Ready Multi-Agent Research System

[![LangChain](https://img.shields.io/badge/LangChain-1.0-blue)](https://langchain.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)](https://fastapi.tiangolo.com)

## 🎯 Project Overview

An advanced AI-powered research assistant that uses **multi-agent architecture** to search, analyze, and synthesize information from multiple sources. Built with modern LangChain agents, conversational memory, and a beautiful React frontend.

### Key Features

#### 🤖 **Multi-Agent Architecture**
- **Research Agent**: Web search with academic source prioritization
- **Analysis Agent**: Deep analysis and intelligent summarization  
- **Verification Agent**: Fact-checking and source validation
- **Custom Tool Integration**: Calculator, Summarizer, Citation Generator, Comparator

#### 💬 **Conversational Memory**
- Maintains context across multiple queries
- Multi-turn conversations with coherent responses
- Session-based memory management

#### 🛠️ **Advanced Tools**
- **Web Search**: Tavily API with academic domain filtering
- **Wikipedia**: Comprehensive background information
- **Math Calculator**: LLMMathChain for calculations
- **Intelligent Summarizer**: Structured research summaries
- **Citation Generator**: Academic-style citations
- **Comparative Analyzer**: Side-by-side comparisons

#### 📊 **Real-time Analytics**
- Token usage tracking
- Cost monitoring ($0.0001 precision)
- Response time metrics
- Query history management

#### 🎨 **Modern React Frontend**
- Responsive design with gradient UI
- Real-time message streaming
- Export conversations (JSON, Markdown)
- Suggested research queries
- Dark/Light mode support

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 FastAPI Backend                     │
│  ┌──────────────────────────────────────────────┐  │
│  │         Multi-Agent Research System          │  │
│  │                                              │  │
│  │  ┌────────────┐  ┌────────────┐              │  │
│  │  │  Research  │  │  Analysis  │              │  │
│  │  │   Agent    │  │   Agent    │              │  │
│  │  └─────┬──────┘  └─────┬──────┘              │  │
│  │        │                │                    │  │
│  │        └────────┬───────┘                    │  │
│  │                 │                            │  │
│  │         ┌───────▼────────┐                   │  │
│  │         │   Tool Suite   │                   │  │
│  │         │  - Web Search  │                   │  │
│  │         │  - Wikipedia   │                   │  │
│  │         │  - Calculator  │                   │  │
│  │         │  - Summarizer  │                   │  │
│  │         │  - Citations   │                   │  │
│  │         └────────────────┘                   │  │
│  │                                              │  │
│  │         ┌────────────────┐                   │  │
│  │         │ Conversational │                   │  │
│  │         │     Memory     │                   │  │
│  │         └────────────────┘                   │  │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │    React Frontend     │
            │  - Query Interface    │
            │  - Chat Display       │
            │  - Analytics Dashboard│
            │  - Export Options     │
            └───────────────────────┘
```

---

## 📁 Project Structure

```
ai-research-agent/
├── agent.py              # Multi-agent system implementation
├── main.py               # FastAPI backend with API endpoints
├── static/
│   └── index.html        # React frontend (single file)
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not in repo)
├── feedback.jsonl        # User feedback log
└── README.md            # This file
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- OpenAI API Key
- Tavily API Key

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/ai-research-agent.git
cd ai-research-agent
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file:
```env
OPENAI_API_KEY=sk-proj-xxxxx
TAVILY_API_KEY=tvly-xxxxx
```

### Step 4: Create Directory Structure
```bash
mkdir static
# Move index.html to static/
```

### Step 5: Run the Application
```bash
uvicorn main:app --reload
```

Visit: **http://localhost:8000**

---

## 📡 API Endpoints

### Research Endpoints
- `GET /api/ask?query=<question>` - Submit research query
- `POST /api/ask` - Submit with full context (JSON body)

### Management Endpoints
- `GET /api/metrics` - Get system performance metrics
- `GET /api/history` - Retrieve conversation history
- `POST /api/history/clear` - Clear conversation memory
- `POST /api/feedback` - Submit user feedback

### Export Endpoints
- `GET /api/export/json` - Export as JSON
- `GET /api/export/md` - Export as Markdown
- `GET /api/export/txt` - Export as plain text

### Health Check
- `GET /api/health` - Service health status

---

## 🎓 Usage Examples

### Example 1: Basic Research Query
```bash
curl "http://localhost:8000/api/ask?query=What%20are%20the%20latest%20advances%20in%20quantum%20computing"
```

### Example 2: Multi-turn Conversation
```python
import requests

# First query
response1 = requests.post('http://localhost:8000/api/ask', 
    json={"query": "What is LangChain?"})

# Follow-up (maintains context)
response2 = requests.post('http://localhost:8000/api/ask',
    json={"query": "How does it compare to AutoGen?"})
```

### Example 3: Export History
```bash
curl "http://localhost:8000/api/export/md" > research.md
```

---

## 🧪 Testing

### Test Basic Functionality
```bash
# Health check
curl http://localhost:8000/api/health

# Simple query
curl "http://localhost:8000/api/ask?query=What%20is%20AI"

# Get metrics
curl http://localhost:8000/api/metrics
```

### Test Advanced Features
- Multi-turn conversations
- Memory persistence
- Tool usage (calculator, summarizer)
- Export functionality

---

## 🎨 Customization

### Add New Tools
```python
# In agent.py
def create_custom_tool(llm):
    def custom_function(input: str) -> str:
        # Your logic here
        return result
    
    return Tool(
        name="CustomTool",
        func=custom_function,
        description="Description for the agent"
    )
```

### Modify Agent Behavior
```python
# In agent.py - MultiAgentResearchSystem._create_agent()
system_message = """
Your custom system prompt here...
"""
```

### Change UI Theme
```css
/* In index.html - <style> section */
background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
```

---

## 📊 Features in Detail

### 1. **Multi-Agent Orchestration**
- Uses LangChain's OpenAI Functions agent
- ReAct pattern for reasoning and acting
- Dynamic tool selection based on query

### 2. **Conversational Memory**
- ConversationBufferMemory for context retention
- Maintains dialogue history across sessions
- Enables follow-up questions

### 3. **Academic Source Prioritization**
```python
include_domains=["arxiv.org", "scholar.google.com", "ieee.org", "acm.org"]
```

### 4. **Cost Tracking**
- Uses OpenAI callbacks to monitor token usage
- Real-time cost calculation
- Per-query and cumulative metrics

### 5. **Error Handling**
- Graceful fallbacks for tool failures
- Parsing error recovery
- User-friendly error messages

---

## 🎯 Use Cases

### For Students
- Literature review assistance
- Concept explanations
- Paper comparisons
- Citation generation

### For Researchers
- Quick fact-checking
- Multi-source information synthesis
- Technical concept clarification
- Recent publication discovery

### For Developers
- Framework comparisons
- Best practice research
- Technical documentation search
- Code concept explanations

---

## 🔒 Security & Privacy

- API keys stored in `.env` (never committed)
- No conversation data stored permanently by default
- CORS configured for localhost development
- Input sanitization on all endpoints

---

## 📈 Performance Metrics

Typical performance (GPT-4-mini):
- **Response Time**: 2-5 seconds
- **Cost per Query**: $0.001-0.005
- **Tokens per Query**: 500-2000
- **Accuracy**: High (multi-source verification)

---

## 🚧 Roadmap

- [ ] Add user authentication
- [ ] Implement database for conversation storage
- [ ] Add PDF/document upload support
- [ ] Create mobile-responsive design improvements
- [ ] Add voice input/output
- [ ] Implement collaborative research sessions
- [ ] Add graph visualization for concept relationships

---

## 🤝 Contributing

This is an academic project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a pull request

---

## 📝 License

MIT License - feel free to use for educational purposes

---



## 📚 References

1. [LangChain Documentation](https://python.langchain.com/)
2. [FastAPI Documentation](https://fastapi.tiangolo.com/)
3. [OpenAI API Reference](https://platform.openai.com/docs)
4. [React Documentation](https://react.dev/)

---

**Built with ❤️ at NIT Durgapur**
