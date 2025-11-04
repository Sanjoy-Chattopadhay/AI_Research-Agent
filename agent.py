from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMMathChain
from langchain.prompts import PromptTemplate
from langchain.callbacks import get_openai_callback
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# ============ CUSTOM TOOLS ============

def create_summarizer_tool(llm):
    """Custom tool for intelligent summarization"""
    summarize_prompt = PromptTemplate(
        input_variables=["text"],
        template="""You are an expert research analyst. Summarize the following text in a clear, 
        structured format with key points and insights:
        
        {text}
        
        Provide:
        1. Main Findings (2-3 bullet points)
        2. Key Insights
        3. Implications/Applications
        """
    )
    
    def summarize(text: str) -> str:
        """Summarize research findings intelligently"""
        if len(text) < 100:
            return "Text too short to summarize."
        return llm.predict(summarize_prompt.format(text=text[:3000]))
    
    return Tool(
        name="IntelligentSummarizer",
        func=summarize,
        description="Use this to create structured summaries of research content. Input should be the text to summarize."
    )

def create_citation_tool():
    """Tool to generate proper academic citations"""
    def generate_citation(source_info: str) -> str:
        """Generate academic citations from source information"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"[Citation generated at {timestamp}]\n{source_info}\n\nNote: Always verify source credibility and publication date."
    
    return Tool(
        name="CitationGenerator",
        func=generate_citation,
        description="Generate academic-style citations from source information. Input should be source details."
    )

def create_comparison_tool(llm):
    """Tool for comparing multiple sources or concepts"""
    compare_prompt = PromptTemplate(
        input_variables=["items"],
        template="""You are a research analyst. Compare and contrast the following items:
        
        {items}
        
        Provide:
        1. Similarities
        2. Key Differences
        3. Which is better for different use cases
        """
    )
    
    def compare(items: str) -> str:
        """Compare multiple concepts or sources"""
        return llm.predict(compare_prompt.format(items=items))
    
    return Tool(
        name="ComparativeAnalyzer",
        func=compare,
        description="Compare and contrast multiple concepts, sources, or approaches. Input should describe what to compare."
    )

# ============ AGENT SYSTEM ============

class MultiAgentResearchSystem:
    """
    Advanced multi-agent research system with specialized agents:
    - Research Agent: Web search and information gathering
    - Analysis Agent: Deep analysis and summarization
    - Verification Agent: Fact-checking and source validation
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # Create specialized tools
        self.tools = self._create_tools()
        
        # Create the main agent
        self.agent = self._create_agent()
        
        # Track metrics
        self.metrics = {
            "total_queries": 0,
            "tokens_used": 0,
            "cost": 0.0,
            "avg_response_time": 0.0
        }
    
    def _create_tools(self):
        """Create comprehensive toolset"""
        # External API tools
        tavily = TavilySearchResults(
            max_results=5,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=False,
            include_domains=["arxiv.org", "scholar.google.com", "ieee.org", "acm.org"]
        )
        
        wiki = WikipediaQueryRun(
            api_wrapper=WikipediaAPIWrapper(
                top_k_results=3,
                doc_content_chars_max=5000
            )
        )
        
        # Math tool for calculations
        math_chain = LLMMathChain.from_llm(llm=self.llm, verbose=False)
        
        # Custom tools
        summarizer = create_summarizer_tool(self.llm)
        citation_gen = create_citation_tool()
        comparator = create_comparison_tool(self.llm)
        
        return [
            Tool(
                name="WebSearch",
                func=tavily.run,
                description="Search the web for recent information. Useful for finding papers, articles, and current research. Prioritizes academic sources."
            ),
            Tool(
                name="Wikipedia",
                func=wiki.run,
                description="Get comprehensive background information on topics. Good for foundational knowledge and definitions."
            ),
            Tool(
                name="Calculator",
                func=math_chain.run,
                description="Perform mathematical calculations and data analysis. Input should be a math expression."
            ),
            summarizer,
            citation_gen,
            comparator
        ]
    
    def _create_agent(self):
        """Create the main ReAct agent with memory"""
        system_message = """You are an advanced AI Research Assistant built by an MTech student at NIT Durgapur.

Your capabilities:
- Conduct comprehensive research using web search and Wikipedia
- Analyze and synthesize information from multiple sources
- Generate structured summaries and comparisons
- Provide academic citations
- Perform calculations when needed

Response Guidelines:
1. Always cite your sources
2. Provide structured, well-organized answers
3. Highlight key findings prominently
4. Suggest related topics for deeper exploration
5. Be critical and analytical, not just informative

When researching papers or technical topics:
- Look for recent publications (2023-2025)
- Prioritize peer-reviewed sources
- Explain complex concepts clearly
- Provide practical applications
"""
        
        return initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            memory=self.memory,
            agent_kwargs={
                "system_message": system_message
            },
            handle_parsing_errors=True,
            max_iterations=6,
            early_stopping_method="generate"
        )
    
    def query(self, question: str) -> dict:
        """Execute a research query and track metrics"""
        import time
        start_time = time.time()
        
        try:
            # Use callback to track token usage
            with get_openai_callback() as cb:
                result = self.agent.invoke({"input": question})
                
                # Update metrics
                self.metrics["total_queries"] += 1
                self.metrics["tokens_used"] += cb.total_tokens
                self.metrics["cost"] += cb.total_cost
                
                elapsed_time = time.time() - start_time
                self.metrics["avg_response_time"] = (
                    (self.metrics["avg_response_time"] * (self.metrics["total_queries"] - 1) + elapsed_time) 
                    / self.metrics["total_queries"]
                )
                
                return {
                    "answer": result["output"],
                    "success": True,
                    "metadata": {
                        "tokens": cb.total_tokens,
                        "cost": f"${cb.total_cost:.4f}",
                        "time": f"{elapsed_time:.2f}s",
                        "conversation_turns": len(self.memory.chat_memory.messages) // 2
                    }
                }
        
        except Exception as e:
            return {
                "answer": f"Error: {str(e)}",
                "success": False,
                "metadata": {}
            }
    
    def get_metrics(self) -> dict:
        """Get current system metrics"""
        return {
            "total_queries": self.metrics["total_queries"],
            "total_tokens": self.metrics["tokens_used"],
            "total_cost": f"${self.metrics['cost']:.4f}",
            "avg_response_time": f"{self.metrics['avg_response_time']:.2f}s",
            "memory_size": len(self.memory.chat_memory.messages)
        }
    
    def get_conversation_history(self) -> list:
        """Get formatted conversation history"""
        messages = self.memory.chat_memory.messages
        history = []
        for msg in messages:
            history.append({
                "role": "human" if msg.type == "human" else "ai",
                "content": msg.content
            })
        return history
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        return {"status": "memory_cleared"}

# ============ SINGLETON INSTANCE ============

_agent_system = None

def get_agent_system() -> MultiAgentResearchSystem:
    """Get or create the agent system singleton"""
    global _agent_system
    if _agent_system is None:
        _agent_system = MultiAgentResearchSystem()
    return _agent_system

# ============ PUBLIC API ============

def run_query(query: str) -> dict:
    """Main entry point for queries"""
    system = get_agent_system()
    return system.query(query)

def get_metrics() -> dict:
    """Get system metrics"""
    system = get_agent_system()
    return system.get_metrics()

def get_history() -> list:
    """Get conversation history"""
    system = get_agent_system()
    return system.get_conversation_history()

def clear_history() -> dict:
    """Clear conversation history"""
    system = get_agent_system()
    return system.clear_memory()