"""
Gradio interface for the Unofficial Guide RAG pipeline.

Wraps query.ask() in a simple web UI: a question box, an answer box, and a
sources box. Run with:  python app.py
"""

import gradio as gr

from query import ask


def answer_question(question: str):
    """Adapt ask() for Gradio: return (answer_text, sources_text)."""
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""

    result = ask(question)
    sources = result["sources"]
    sources_text = "\n".join(f"• {s}" for s in sources) if sources else "No sources."
    return result["answer"], sources_text


with gr.Blocks(title="UIC CS Unofficial Guide") as demo:
    gr.Markdown("# UIC CS Unofficial Guide")
    gr.Markdown(
        "Ask about professors, course difficulty, workload, and student experiences."
    )

    question_box = gr.Textbox(
        label="Ask a question about UIC CS professors and courses",
        placeholder="e.g. What is the workload like for CS 401 with DasGupta?",
    )
    ask_button = gr.Button("Ask", variant="primary")

    answer_box = gr.Textbox(label="Answer", lines=10)
    sources_box = gr.Textbox(label="Sources", lines=5)

    # Trigger on both the button click and Enter key in the input box.
    ask_button.click(
        fn=answer_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        fn=answer_question,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )


if __name__ == "__main__":
    demo.launch()
