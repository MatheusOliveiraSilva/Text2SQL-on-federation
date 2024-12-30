from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import openai
import os
import time
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.callbacks import get_openai_callback
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.chains import LLMChain
import time
import faiss
import gptconfig as gptconfig

def get_llm(temperature=0, max_tokens=400, n=1, model_kwargs={}, model=gptconfig.MODEL_4O):
    llm = AzureChatOpenAI(
        temperature=temperature,
        model=model,
        # max_tokens=max_tokens,
        n=n,
        model_kwargs=model_kwargs,

        openai_api_key=gptconfig.OPENAI_API_KEY,
        openai_api_version=gptconfig.OPENAI_API_VERSION,
        # azure_endpoint=config['OPENAI']['OPENAI_API_BASE'],
        openai_api_base=gptconfig.AZURE_OPENAI_BASE_URL
    )

    return llm


def get_embeddings_model(model=gptconfig.MODEL_EMBEDDING):
    embeddings = AzureOpenAIEmbeddings(
        model=model,
        openai_api_key=gptconfig.OPENAI_API_KEY,
        openai_api_version=gptconfig.OPENAI_API_VERSION,
        # azure_endpoint=config['OPENAI']['OPENAI_API_BASE'],
        openai_api_base=gptconfig.AZURE_OPENAI_BASE_URL
    )
    return embeddings


# def get_llm(temperature=0, max_tokens=50, n=1, model="gpt-3.5-turbo"):
#     apikey = os.environ["OPENAI_API_KEY"]
#     openai.api_key = apikey
#     return ChatOpenAI(temperature=temperature, model=model, max_tokens=max_tokens, n=n)

def get_embeddings(text, model=gptconfig.MODEL_EMBEDDING, delay=None):
    embeddings = get_embeddings_model(model=model)

    if delay is not None:
        # Sleep for the delay
        time.sleep(delay)

    return embeddings.embed_query(text)


def get_openai_response_msg(model, messages, max_tokens=400, temperature=0, delay=None, **kwargs):
    llm = get_llm(temperature=temperature, max_tokens=max_tokens, model_kwargs=kwargs, model=model)
    messages = convert_chat_models_to_langchain(messages)

    message = {}
    with get_openai_callback() as cb:
        response = llm(messages)
        message['content'] = response.content
        message['usage'] = cb

    if delay is not None:
        # Sleep for the delay
        time.sleep(delay)

    return message

def convert_chat_models_to_langchain(messages):
    langchain_chat_models = []
    for m in messages:
        if type(m) == dict:
            if m['role'].lower() == 'system':
                langchain_chat_models.append(SystemMessage(content=m['content']))
            elif m['role'].lower() == 'assistant':
                langchain_chat_models.append(AIMessage(content=m['content']))
            elif m['role'].lower() == 'user':
                langchain_chat_models.append(HumanMessage(content=m['content']))
        else:
            langchain_chat_models = messages
            break

    return langchain_chat_models
