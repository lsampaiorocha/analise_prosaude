"""
This module contains the ProjectBuilder class, which is used to build research
projects.
It provides functionalities for configuring, building, and saving projects.

Attributes
----------
ProjectBuilder : class
    A class used to build research projects.

"""
import re
import json
import time
import logging
import asyncio
import traceback
from typing import Callable
from pathlib import Path

from aigents.constants import MODELS
from google.api_core.exceptions import InternalServerError

from .agents import create_agent
from .article import DocumentProcessor
from .prompts import (
    PROMPT_ENHANCE_SECTION_PT_V2,
    SECTION_WRITER_SETUP_PT,
    WRITE_PROJECT_TITLE_PROMPT_PT,
    fix_json_response_prompt,
    enhance_section_prompt
)


logger = logging.getLogger('client')


class ProjectBuilder:
    """
    A class used to build research projects.

    This class provides methods to configure a project, build it by generating content
    using an AI agent, and save the project. It supports enhancing the generated content
    through additional API calls.

    Parameters
    ----------
    agent_name : str, optional
        The name of the agent. Default is 'openai'.
    agent_kwargs : dict, optional
        Additional keyword arguments for the agent. Default is None.
    helper_setup : str, optional
        The setup for the helper agent. Default is None.

    Attributes
    ----------
    agent : Agent
        The AI agent used to generate content.
    helper : Agent
        An optional helper agent used for enhancing content.
    model : str
        The model used by the agent.
    setup : str
        The setup for the project.
    prompts : list
        A list of prompts for generating content.
    agent_name : str
        The name of the agent.
    agent_kwargs : dict
        Additional keyword arguments for the agent.
    helper_setup : str
        The setup for the helper agent.
    __configured : bool
        Indicates if the project has been configured.
    __built : bool
        Indicates if the project has been built.
    doc : DocumentProcessor
        An instance of DocumentProcessor for managing the project document.
    version : int
        The version of the ProjectBuilder.
    """
    def __init__(self,
                 *args,
                 agent_name: str = 'openai',
                 helper_agent_name: str = 'openai',
                 agent_kwargs: dict = None,
                 helper_agent_kwargs: dict = None,
                 helper_setup: str = None,
                 **kwargs):
        self.agent = None
        self.helper = None
        self.model = None
        self.setup = None
        self.helper_setup = helper_setup
        self.prompts = None
        self.agent_name = agent_name
        self.helper_agent_name = helper_agent_name
        self.agent_kwargs = agent_kwargs
        self.helper_agent_kwargs = helper_agent_kwargs
        self.__configured = False
        self.__built = False
        self.doc = DocumentProcessor()
        self.version = 1
        if args or kwargs:
            self.configure(*args, **kwargs)

    def configure(self,
                  *args,
                  prompt_func: Callable,
                  context: str = None,
                  **kwargs):
        # just a place holder. It is the agent that holds the model
        self.model = MODELS[0]
        data = prompt_func(*args, **kwargs)
        if context:
            data['setup'] += f"\n###\nContexto:\n{context}###"
        self.setup = data['setup']
        self.prompts = data['prompts']
        setup = self.agent_kwargs.pop('setup', None)
        if setup:
            logger.warning(
                'Provided setup will be disregarded. '
                'You must provide setup via `prompt_func`'
            )
        # instantiate the agent
        self.agent, _ = create_agent(
            name=self.agent_name,
            setup=data['setup'],
            **self.agent_kwargs
        )
        self.model = self.agent.model
        self.__configured = True

    async def ask(self, agent_name, prompt, setup, retry: int = 1, **kwargs):
        agent, agent_kwargs = create_agent(
            name=agent_name,
            setup=setup,
            **kwargs
        )
        while retry:
            try:
                retry -= 1
                if 'model' in agent_kwargs:
                    agent_kwargs.pop('model')
                if 'setup' in agent_kwargs:
                    agent_kwargs.pop('setup')
                response = await agent.answer(
                    prompt, use_agent=False, conversation=False,
                    response_format={"type": "json_object"},
                    **agent_kwargs
                )
                response = response.replace("**", "").replace("'", '"')
                # logger.info("prompt: %s", prompt)
                # logger.info("response: %s", response)
                return json.loads(response)
            except json.JSONDecodeError as err:
                match = re.search(r'json(.*)', response, re.DOTALL)
                if match and match.group(1):
                    try:
                        return json.loads(match.group(1))
                    except json.JSONDecodeError:
                        if not retry:
                            return response
                        logger.warning(
                            "%s. Agent %s messed up json formart. "
                            "Asking another "
                            "%s agent to fix it.",
                            err,
                            agent_name,
                            agent_name
                        )
                        data = fix_json_response_prompt(
                            response, f"JSONDecodeError: {err}"
                        )
                        return await self.ask(
                            agent_name, data["prompt"], data["setup"], retry=2
                        )
                return response
            except InternalServerError as err:
                logger.warning(
                    "%s. Retrying calling %s agent", err, agent_name
                )
                time.sleep(1)
        return ''


    async def ask_section(self,
                          prompt: str,
                          enhance_prompt: str = PROMPT_ENHANCE_SECTION_PT_V2,
                          retry: int = 1,
                          enhance_times: int = 0):
        response = await self.ask(
            self.agent_name,
            prompt,
            self.setup,
            retry=retry,
            **self.agent_kwargs
        )
        if enhance_times > 0:
            for _ in range(enhance_times):
                data = enhance_section_prompt(
                    response,
                    enhance_prompt,
                    setup=SECTION_WRITER_SETUP_PT
                )
                response = await self.ask(
                    self.helper_agent_name,
                    data["prompt"],
                    data["setup"],
                    retry=retry,
                    **self.helper_agent_kwargs
                )
        return response

    async def build(self,
                    enhance_times: int = 0,
                    enhance_prompt: str = PROMPT_ENHANCE_SECTION_PT_V2,
                    retry: int = 2):
        """
        Builds the project by generating content using the configured AI agent.

        This method generates content for each prompt in the project. It
        optionally enhances
        the generated content by making additional API calls. The method also
        generates a title
        for the project.

        Parameters
        ----------
        enhance_times : int, optional
            The number of times to enhance each section. Default is 0.
        enhance_prompt : str, optional
            The prompt used for enhancing sections. Default is
            PROMPT_ENHANCE_SECTION_PT_V2.
        write_title_prompt : str, optional
            The prompt used for generating the project title. Default is
            WRITE_PROJECT_TITLE_PROMPT_PT.

        Raises
        ------
        RuntimeError
            If the project has not been configured yet.

        Returns
        -------
        dict
            The project data in JSON format.
        """
        if not self.__configured:
            raise RuntimeError(
                "First configure project by calling 'configure' method."
            )
        total = len(self.prompts)
        tasks = []
        for idx, prompt in enumerate(self.prompts):
            logger.info("Section %s/%s requested.", idx, total)
            task = self.ask_section(
                prompt,
                enhance_prompt,
                retry=retry,
                enhance_times=enhance_times,
            )
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        # last API call. Write title
        title = await self.ask(
            self.agent_name,
            WRITE_PROJECT_TITLE_PROMPT_PT,
            self.setup,
            retry=retry
        )
        data = {"title": ""}
        if isinstance(title, str):
            try:
                data['title'] = json.loads(title)  # caso responda com '{"title": "Título"}'
            except json.JSONDecodeError:
                data['title'] = title  # caso responda simplesmente "Título"
        data['sections'] = responses
        try:
            self.doc.load(data)
            self.__built = True
        except (KeyError, TypeError) as err:  # depending on the model, it might fail following json format instructions  # noqa E501
            logger.error(err)
            logger.error(traceback.format_exc())
            logger.warning("Document wasn't created")
            return data
        return self.doc.json()

    @property
    def built(self,):
        return self.__built

    def save(self, path: str | Path):
        if not self.__built:
            raise RuntimeError(
                "First build project by calling 'build' method."
            )
        self.doc.docx().save(path)
        return self.doc.docx()
