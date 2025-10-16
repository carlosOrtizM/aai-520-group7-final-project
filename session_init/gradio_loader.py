import gradio as gr
from utilities.metric_utils import track_generation_metrics

def gradio_ui_loader(graph):
    @track_generation_metrics
    def output_print(prompt, history=None):
        """
         Generate AI response using the loaded LLM model

         Args:
             user_input (str): User's input message
             history (list): Conversation history for context

         Returns:
             str: Generated AI response
         """
        response = ""

        for step in graph.stream(
                {"messages": [{"role": "user", "content": prompt}]},
                stream_mode="values",
        ):
            #step["messages"][-1].pretty_print()
            response = step["messages"][-1].content

        return response

    # Create Gradio interface
    def chat_interface(message, history):
        """
        Handle chat interactions with conversation history
        """
        response = output_print(message, history)
        history.append((message, response))
        return "", history

    def exit_gradio():
        demo.close()

    with gr.Blocks(title="Financial Advisor") as demo:
        gr.Markdown("<center><h1>Automator</h1></center>")
        gr.Markdown("Static prompts generated. Y/N button. (ORL)")

        chatbot = gr.Chatbot(
            type='tuples',
            value=[],
            height=400,
            label="Conversation"
        )

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Type your message here...", #eventually becomes the prompter
                label="Message",
                scale=4
            )
            send_btn = gr.Button("Send", scale=1)

        with gr.Row():
            # Clear conversation button
            clear_btn = gr.Button("Clear Conversation")
            # Exit button
            exit_btn = gr.Button("Exit")

        # Event handlers
        send_btn.click(
            chat_interface,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )

        msg.submit(
            chat_interface,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )

        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
        exit_btn.click(exit_gradio)

    return demo