import os
from typing import Annotated

from flask import Flask, jsonify, request
from flask_cors import CORS
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

LANGSMITH_API_KEY = os.getenv("langsmith_key")
GROQ_API_KEY = os.getenv("groq_key")

os.environ['LANGSMITH_API_KEY'] = LANGSMITH_API_KEY
os.environ['LANGSMITH_TRACING'] = "true"
os.environ['LANGSMITH_PROJECT'] = "AIchatbot"

llm = ChatGroq(groq_api_key = GROQ_API_KEY,model_name="gemma2-9b-it")

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
graph_builder = StateGraph(State)
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            return ("Assistant:", value["messages"][-1].content)
app = Flask(__name__)
CORS(app)
@app.route('/bot',methods=['POST'])
def home():
    data = request.get_json()
    user_message = data.get("message")
    try:
        user_input = user_message.lower()
        if user_message in ["bye", "exit", "q"]:
            bot_msg = [" ","Goodbye from luffy👋! Have a nice day!"]
        elif user_message in ["what is your name", "who are you", "tell me about you","what's your name","your name"]:
            bot_msg = [" ","I’m Luffy, the King of AI Bots! 🌟 I can assist you with anything in any language you want. My knowledge is vast, and I’m always learning and upgrading myself to serve you better. Whether it’s answering your questions, translating languages, or just having a fun conversation,\n I’m here for you!Got something on your mind? Let’s chat!"]
        else:
            bot_msg=stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "Tell Me About python"
        bot_msg=stream_graph_updates(user_input)
    bot_msg = list(bot_msg)
    msg_to_send = str(bot_msg[1])
    return jsonify(msg_to_send)

if __name__ == "__main__":
    app.run(debug=False)