from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from MagnusGPTConnector.config import Config
config = Config()
from MagnusGPTConnector.gpt_client import GPTClient
client = GPTClient(config)



def callGPT(message):
    # print(message)
    response = client.invoke_gpt_4o(path_to_file='hackathon-small.pdf', prompt=message)
    # response = client.invoke_gpt_35(message)
    # print(response)
    return response