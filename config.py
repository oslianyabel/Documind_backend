import os
import logging

from dotenv import load_dotenv
from openai import OpenAI
from logging_conf import configure_logging

configure_logging()
logger = logging.getLogger("app")

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
