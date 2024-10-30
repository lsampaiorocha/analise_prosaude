import re
import logging
import json

import logging
from typing import Union, Dict, Any

from aigents import (
    OpenAIChatter,
    AsyncOpenAIChatter,
    GoogleChatter,
    AsyncGoogleChatter,
    BingChatter,
    AsyncBingChatter
)

from .constants import AGENTS
from .prompts import prompt_search_terms

logger = logging.getLogger('client')


agent_classes = {
    AGENTS[0]: OpenAIChatter,
    AGENTS[1]: AsyncOpenAIChatter,
    AGENTS[2]: GoogleChatter,
    AGENTS[3]: AsyncGoogleChatter,
    AGENTS[4]: BingChatter,
    AGENTS[5]: AsyncBingChatter,
}

Agent = Union[
    OpenAIChatter,
    AsyncOpenAIChatter,
    GoogleChatter,
    AsyncGoogleChatter,
    BingChatter,
    AsyncBingChatter,
]

def create_agent(*args, name: str = AGENTS[1], **kwargs):
    name = name.lower()
    if name not in AGENTS:
        raise ValueError(
            f"Not supported agent '{name}'. Supported agents are {AGENTS}"
        )
    if 'google' in name or 'bing' in name:
        if kwargs and 'model' in kwargs:
            kwargs.pop('model')
        if kwargs and 'organization' in kwargs:
            kwargs.pop('organization')
        if kwargs and 'use_gpt4' in kwargs:
            kwargs.pop('use_gpt4')
    if kwargs and 'web_search' in kwargs and 'bing' not in name:
        kwargs.pop('web_search')
    if kwargs and 'cookies' in kwargs and 'bing' not in name:
        kwargs.pop('cookies')

    return agent_classes[name](*args, **kwargs), kwargs


class AsyncContextGenerator:
    """
    A class to generate context and interact with an agent.

    Attributes
    ----------
    agent : Agent
        The agent used for generating context.
    """

    def __init__(self, name: str = 'async_bing', **kwargs):
        """
        Initialize the ContextGenerator object.

        Parameters
        ----------
        name : str, optional
            The name of the agent to use. Default is 'async_bing'.
        **kwargs : dict, optional
            Additional keyword arguments for the agent.
        """
        if 'async' not in name:
            raise ValueError('For sync generator use ContextGenerator')
        self.agent, _ = create_agent(name=name, **kwargs)

    async def generate_context(self,
                               knowledge_area: str,
                               area: str,
                               subject: str,
                               topic: str,
                               language="pt",
                               n_terms: int = 5,
                               **kwargs) -> Dict[str, Any]:
        """
        Generate context using the agent.

        Parameters
        ----------
        knowledge_area : str
            The knowledge area of the context.
        area : str
            The area of the context.
        subject : str
            The subject of the context.
        topic : str
            The topic of the context.
        language : str, optional
            The language of the context. Default is "pt".
        n_terms : int, optional
            The number of terms to generate. Default is 5.

        Returns
        -------
        dict
            The generated context.
        """
        data = prompt_search_terms(
            knowledge_area=knowledge_area,
            area=area,
            subject=subject,
            topic=topic,
            language=language,
            n_terms=n_terms
        )
        response = await self.agent.answer(data['prompts'][0], **kwargs)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_pattern = r'\"terms\"\s*:\s*(\[.*?\])'
            json_matches = re.findall(json_pattern, response, re.DOTALL)
            if json_matches:
                try:
                    return json.loads(f'{{"terms": {json_matches[0]}}}')
                except json.JSONDecodeError:
                    logger.warning('Returning json bad formating')
            return response


class ContextGenerator:
    """
    A class to generate context and interact with an agent.

    Attributes
    ----------
    agent : Agent
        The agent used for generating context.
    """

    def __init__(self, name: str = 'bing', **kwargs):
        """
        Initialize the ContextGenerator object.

        Parameters
        ----------
        name : str, optional
            The name of the agent to use. Default is 'async_bing'.
        **kwargs : dict, optional
            Additional keyword arguments for the agent.
        """
        if 'async' in name:
            raise ValueError('For Async generator use ContextGenerator')
        self.agent, _ = create_agent(name=name, **kwargs)

    def generate_context(self,
                         knowledge_area: str,
                         area: str,
                         subject: str,
                         topic: str,
                         language="pt",
                         n_terms: int = 5,
                         **kwargs) -> Dict[str, Any]:
        """
        Generate context using the agent.

        Parameters
        ----------
        knowledge_area : str
            The knowledge area of the context.
        area : str
            The area of the context.
        subject : str
            The subject of the context.
        topic : str
            The topic of the context.
        language : str, optional
            The language of the context. Default is "pt".
        n_terms : int, optional
            The number of terms to generate. Default is 5.

        Returns
        -------
        dict
            The generated context.
        """
        data = prompt_search_terms(
            knowledge_area=knowledge_area,
            area=area,
            subject=subject,
            topic=topic,
            language=language,
            n_terms=n_terms
        )
        response = self.agent.answer(data['prompts'][0], **kwargs)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return response



