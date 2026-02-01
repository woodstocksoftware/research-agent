"""
Research Agent - Gradio UI
"""

import gradio as gr
from src.agent.researcher import ResearchAgent


def research_topic(topic: str, progress=gr.Progress()) -> str:
    """Run research and return the report."""
    if not topic.strip():
        return "Please enter a research topic."
    
    agent = ResearchAgent()
    status_messages = []
    
    def on_status(msg):
        status_messages.append(msg)
        # Update progress display
        progress(len(status_messages) / 15, desc=msg)  # Rough estimate of steps
    
    report = agent.research(topic, on_status=on_status)
    return report


# Build the UI
with gr.Blocks(title="Research Agent", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 🔍 Research Agent
    
    Enter any topic and the agent will:
    1. **Plan** research questions
    2. **Search** the web for information
    3. **Analyze** gaps and search more if needed
    4. **Synthesize** a comprehensive report with citations
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            topic_input = gr.Textbox(
                label="Research Topic",
                placeholder="e.g., AI agents in enterprise software",
                lines=2
            )
            
            research_btn = gr.Button("🚀 Start Research", variant="primary")
            
            gr.Markdown("""
            ### Example Topics
            - AI agents in enterprise software
            - Remote work trends 2024
            - Sustainable packaging innovations
            - Electric vehicle battery technology
            - No-code development platforms
            """)
        
        with gr.Column(scale=2):
            output = gr.Markdown(label="Research Report")
    
    research_btn.click(
        fn=research_topic,
        inputs=[topic_input],
        outputs=[output],
        show_progress="full"
    )
    
    # Also trigger on Enter
    topic_input.submit(
        fn=research_topic,
        inputs=[topic_input],
        outputs=[output],
        show_progress="full"
    )


if __name__ == "__main__":
    app.launch()
