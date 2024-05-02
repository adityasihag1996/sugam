from dotenv import load_dotenv
import os
load_dotenv()

import datetime

from web_search_api import WebSearcher
from llm_engine import LLM_engine
from prompts_dump import REPHRASE_QUERY_FOR_SEARCH_SYSTEM_PROMPT, QUERY_REPHRASE_COMPLETION_PROMPT, RESPONSE_FORMATION_SYSTEM_PROMPT, USER_QUERY_ANSWER_COMPLETION_PROMPT, CHAT_TEMPLATE

GS_API_KEY = os.getenv('GS_API_KEY')
GS_CSE_ID = os.getenv('GS_CSE_ID')

def main():
    # Initiate the LLM Engine
    llm_engine = LLM_engine()
    web_search = WebSearcher()

    print("\n\n<<<<<<<<<<  Sugama AI assistant  >>>>>>>>>> \n")

    # Initialise the chat history
    chat_history = []

    # Loop the runner
    while True:
        # Ask for user input
        user_query = input("Query: ")

        # Get rephrased search queries
        rephrased_search_queries = llm_engine.forward(
                                        llm_engine.apply_chat_template(
                                            REPHRASE_QUERY_FOR_SEARCH_SYSTEM_PROMPT.format(CHAT_HISTORY = "\n".join(chat_history), CURRENT_DATE = datetime.date.today().strftime('%B %-d, %Y')),
                                            QUERY_REPHRASE_COMPLETION_PROMPT.format(QUERY = user_query),
                                            return_pt = True,
                                        ).to(llm_engine.model.device)
                                    )
        
        try:
            rephrased_search_queries = eval(rephrased_search_queries)
            if type(rephrased_search_queries) != list:
                raise Exception(f"Could not parse rephrased queries.")
            
            # Restrict to only 3 phrases max
            rephrased_search_queries = rephrased_search_queries[:3]
        except Exception as e:
            print("Sugama:  Cannot answer this query at this moment.")
            print("\n\n")
            continue
        
        # Web search, form articles
        search_articles_formed = web_search.form_articles(rephrased_search_queries, GS_API_KEY, GS_CSE_ID)
        
        # Fetch model response
        query_response = llm_engine.forward(
                                llm_engine.apply_chat_template(
                                    RESPONSE_FORMATION_SYSTEM_PROMPT.format(ARTICLES = search_articles_formed, CURRENT_DATE = datetime.date.today().strftime('%B %-d, %Y')),
                                    USER_QUERY_ANSWER_COMPLETION_PROMPT.format(QUERY = user_query),
                                    return_pt = True,
                                ).to(llm_engine.model.device)
                            )
        
        # Show model response to query
        print("Sugama: ")
        print(query_response)
        print("\n\n")

        # Update chat history
        chat_history.append(CHAT_TEMPLATE.format(
                                USER_QUERY = user_query,
                                ASSISTANT_RESPONSE = query_response,
                            ))
        
        # Chat history to only store, last 2 QUERY:RESPONSE pairs
        if len(chat_history) > 2:
            chat_history = chat_history[1:]



if __name__ == "__main__":
    main()
    