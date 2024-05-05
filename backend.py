from dotenv import load_dotenv
import os
load_dotenv()

import datetime
from flask import Flask, request, jsonify

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

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/sugamify', methods = ['POST'])
def handle_message():
    data = request.json
    user_query = data['message']

    global chat_history

    # Get rephrased search queries
    try:
        rephrased_search_queries = llm_engine.forward(
                                        REPHRASE_QUERY_FOR_SEARCH_SYSTEM_PROMPT.format(CHAT_HISTORY = "\n".join(chat_history), CURRENT_DATE = datetime.date.today().strftime('%B %-d, %Y')),
                                        QUERY_REPHRASE_COMPLETION_PROMPT.format(QUERY = user_query),
                                    )
    except Exception as e:
        return jsonify(error = "An error while rephrasing your query for search."), 500
    
    try:
        rephrased_search_queries = eval(rephrased_search_queries)
        if type(rephrased_search_queries) != list:
            return jsonify(error = "Could not parse rephrased queries."), 500
        
        # Restrict to only 3 phrases max
        rephrased_search_queries = rephrased_search_queries[:3]
    except Exception as e:
        return jsonify(error = "An error occurred while processing your message."), 500
    
    # Web search, form articles
    search_articles_formed = web_search.form_articles(rephrased_search_queries, GS_API_KEY, GS_CSE_ID)
    
    # Fetch model response
    try:
        query_response = llm_engine.forward(
                                RESPONSE_FORMATION_SYSTEM_PROMPT.format(ARTICLES = search_articles_formed, CURRENT_DATE = datetime.date.today().strftime('%B %-d, %Y')),
                                USER_QUERY_ANSWER_COMPLETION_PROMPT.format(QUERY = user_query),
                            )
    except Exception as e:
        return jsonify(error = "An error while rephrasing your query for search."), 500

    # Update chat history
    chat_history.append(CHAT_TEMPLATE.format(
                            USER_QUERY = user_query,
                            ASSISTANT_RESPONSE = query_response,
                        ))
    
    # Chat history to only store, last 2 QUERY:RESPONSE pairs
    if len(chat_history) > 2:
        chat_history = chat_history[1:]

    return jsonify(reply = query_response)

if __name__ == '__main__':
    app.run(debug = True, port = 6969)