from projai.constants import MODELS

from projai.prompts import prompt_projeto_inovafit
from aigents.constants import AGENTS


def config_build(knowledge_area: str,
                 area: str,
                 subject: str,
                 topic: str,
                 context: str = None,
                 template: dict = None):
    # parâmetros para o agente baseado na IA
    agent_kwargs = {
        'web_search': True,  # only for Bing
        "model": MODELS[3]  # only for openai
    }
    helper_agent_kwargs = {
        'web_search': True,  # only for Bing
        "model": MODELS[3],  # only for openai
    }
    config = {
        "agent_name": AGENTS[1],  # AGENTS[1] é `async_openai``
        "helper_agent_name": AGENTS[1],  # AGENTS[1] é `async_openai``
        "agent_kwargs": agent_kwargs,
        "helper_agent_kwargs": helper_agent_kwargs,
        "helper_setup": None, # (str) texto de setup para o agente responsável por aprimorar o texto  # noqa E501
        "prompt_func": prompt_projeto_inovafit,  # função que gera o setup e os prompts. Veja no módulo prompts
    }
    project_data = {
        "knowledge_area": knowledge_area,
        "area": area,
        "subject": subject,
        "topic": topic,
    }
    if template:
        config['template'] = template
    if context:
        project_data['context'] = context
    config.update(project_data)
    return config
