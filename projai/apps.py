import logging
import asyncio
from typing import Callable

from .prompts import prompt_projeto_inovafit
from .prompts import PROMPT_ENHANCE_SECTION_PT_V2
from .prompts import WRITE_PROJECT_TITLE_PROMPT_PT
from .builders import ProjectBuilder
from .utils import open_docx_file, normalize_string

logger = logging.getLogger('client')


class AppProjectInovafit(ProjectBuilder):
    def __init__(self,
                 knowledge_area: str,
                 area: str,
                 subject: str,
                 topic: str,
                 agent_name: str = 'async_openai',
                 agent_kwargs: dict = None,
                 helper_setup: str = None,
                 prompt_func: Callable = prompt_projeto_inovafit,
                 context: str = None,
                 **kwargs):
        super().__init__(
            knowledge_area,
            area,
            subject,
            topic,
            agent_name=agent_name,
            agent_kwargs=agent_kwargs,
            helper_setup=helper_setup,
            prompt_func=prompt_func,
            context=context,
            **kwargs
        )
        self.last_response = None

    async def run(self,
                  enhance_times: int = 0,
                  enhance_prompt: str = PROMPT_ENHANCE_SECTION_PT_V2,
                  save_docx: bool = False,
                  open_docx: bool = False,
                  **kawrgs):
        logger.info(">> Starting building process...")
        self.last_response = await self.build(
            enhance_times=enhance_times,
            enhance_prompt=enhance_prompt,
            **kawrgs
        )
        if self.built:
            logger.info(">> Building process finished!")
            path = f"{normalize_string(self.doc.title)}.docx"
            if save_docx:
                self.save(path)
                if open_docx:
                    open_docx_file(path)
            else:
                if open_docx:
                    logger.warning("No docx was created!")
        return self.last_response


def app_project_inovafit(knowledge_area: str,
                         area: str,
                         subject: str,
                         topic: str,
                         prompt_func: Callable = prompt_projeto_inovafit,
                         context: str = None,
                         agent_name: str = 'async_openai',
                         agent_kwargs: dict = None,
                         helper_setup: str = None,
                         enhance_times: int = 0,
                         enhance_prompt: str = PROMPT_ENHANCE_SECTION_PT_V2,
                         **kwargs):
    app = AppProjectInovafit(
            knowledge_area=knowledge_area,
            area=area,
            subject=subject,
            topic=topic,
            prompt_func=prompt_func,
            context=context,
            agent_name=agent_name,
            agent_kwargs=agent_kwargs,
            helper_setup=helper_setup,
            **kwargs
        )
    return asyncio.run(
        app.run(
            enhance_times=enhance_times,
            enhance_prompt=enhance_prompt,
        )
    )
