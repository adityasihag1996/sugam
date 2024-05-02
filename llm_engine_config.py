from dotenv import load_dotenv
import os
load_dotenv()


HF_TOKEN = os.getenv('HF_TOKEN')
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

USE_4BIT = False
USE_8BIT = True

USE_FLASH_ATTN = True