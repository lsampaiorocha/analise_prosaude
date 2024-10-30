"""

    Constants of the project

    - used in agents: Most constants comes from OpenAI documentation. See:
                      https://platform.openai.com/docs/models
"""

MODELS = (
    'gpt-3.5-turbo-0125',
    'gpt-3.5-turbo-1106',
    'gpt-4',
    'gpt-4o',  # 3
    'gpt-4-1106-preview',
    'gpt-4-vision-preview',
    'gemini-pro',  # Google # 6
    'gemini-pro-vision'
)

MAX_TOKENS = (
    (MODELS[0], 16385),
    (MODELS[1], 16385),
    (MODELS[2], 8192),
    (MODELS[3], 128000),
    (MODELS[4], 128000),
    (MODELS[5], 128000),
    (MODELS[6], 30720),
    (MODELS[7], 12288),
)

ROLES = (  # roles for messages objects
    'system',
    'user',
    'assistant',
    'model'  # Google gemini
)  # see https://platform.openai.com/docs/guides/gpt/chat-completions-api

MODELS_EMBEDDING = (
    'text-embedding-ada-002',
)

TOKENIZER = (
    'cl100k_base',
)

AGENTS = (
    'openai',
    'async_openai',
    'google',
    'async_google',
    'bing',
    'async_bing',
)
