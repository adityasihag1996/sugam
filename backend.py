from dotenv import load_dotenv
import os
load_dotenv()

import datetime, time
from contexttimer import Timer
from flask import Flask, request, jsonify, Response

from web_search_api import WebSearcher
from llm_engine import LLM_engine
from prompts_dump import REPHRASE_QUERY_FOR_SEARCH_SYSTEM_PROMPT, QUERY_REPHRASE_COMPLETION_PROMPT, RESPONSE_FORMATION_SYSTEM_PROMPT, USER_QUERY_ANSWER_COMPLETION_PROMPT, CHAT_TEMPLATE

GS_API_KEY = os.getenv('GS_API_KEY')
GS_CSE_ID = os.getenv('GS_CSE_ID')

app = Flask(__name__, static_folder = 'static', static_url_path = '')

# Initiate the LLM Engine
llm_engine = LLM_engine()
web_search = WebSearcher()

# Initialise the chat history
chat_history = []

# Some Variables needed for state
response_streamer = None
prev_user_query, prev_idx_url_mapping = "", {}

@app.route('/')
def index():
    return app.send_static_file('index.html')

def generate_data():
    global chat_history, response_streamer, prev_user_query, prev_idx_url_mapping

    # Stream the response
    query_response = []
    for token in response_streamer:
        token = token["message"]["content"]
        query_response.append(token)
        token = token.replace("\n", "<br>")
        yield f"data: {token}\n\n"
    
    query_response = "".join(query_response)

    # Update chat history
    chat_history.append(CHAT_TEMPLATE.format(
                            USER_QUERY = prev_user_query,
                            ASSISTANT_RESPONSE = query_response,
                        ))
    
    # Chat history to only store, last 2 QUERY:RESPONSE pairs
    if len(chat_history) > 2:
        chat_history = chat_history[1:]

    # Add 'Sources' to the response
    sources_query_response = " <br><br> "
    for idx, url in prev_idx_url_mapping.items():
        sources_query_response += f"[{idx}] - {url} <br> "

    for token in sources_query_response.split():
        yield f"data: {token}\n\n"
        time.sleep(0.1)

    yield "event: end\ndata: stream ended\n\n"

@app.route('/stream_response')
def stream_response():
    return Response(generate_data(), mimetype = 'text/event-stream')

@app.route('/sugamify', methods = ['POST'])
def handle_message():
    global chat_history, response_streamer, prev_user_query, prev_idx_url_mapping

    data = request.json
    prev_user_query = data['message']

    # Get rephrased search queries
    try:
        with Timer() as t:
            rephrased_search_queries = llm_engine.forward(
                                            REPHRASE_QUERY_FOR_SEARCH_SYSTEM_PROMPT.format(CHAT_HISTORY = "\n".join(chat_history), CURRENT_DATE = datetime.date.today().strftime('%B %-d, %Y')),
                                            QUERY_REPHRASE_COMPLETION_PROMPT.format(QUERY = prev_user_query),
                                        )
        print(f"Rephrasing formation took: {t.elapsed} seconds")
    except Exception as e:
        return jsonify(error = "An error while rephrasing your query for search."), 500
    
    try:
        rephrased_search_queries = eval(rephrased_search_queries)
        if type(rephrased_search_queries) != list:
            return jsonify(error = "Could not parse rephrased queries."), 500
        
        # Restrict to only 3 phrases max
        rephrased_search_queries = rephrased_search_queries[:3]

        if rephrased_search_queries == 0:
            return jsonify(error = "No search phrases returned by LLM rephrasing tool."), 500
    except Exception as e:
        return jsonify(error = "An error occurred while processing your message."), 500
    
    # Web search, form articles
    try:
        search_articles_formed, prev_idx_url_mapping = web_search.form_articles_mp(rephrased_search_queries, GS_API_KEY, GS_CSE_ID)
    except Exception as e:
        return jsonify(error = "An error occurred while web search and articles formation."), 500

    # Fetch model response
    try:
        response_streamer = llm_engine.forward(
                                RESPONSE_FORMATION_SYSTEM_PROMPT.format(ARTICLES = search_articles_formed, CURRENT_DATE = datetime.date.today().strftime('%B %-d, %Y')),
                                USER_QUERY_ANSWER_COMPLETION_PROMPT.format(QUERY = prev_user_query),
                                stream = True,
                            )
    except Exception as e:
        return jsonify(error = "An error while rephrasing your query for search."), 500
    
    return jsonify(reply = "")

if __name__ == '__main__':
    app.run(debug = True, port = 6969)