from langchain_core.prompts import PromptTemplate

#organizar outputs
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field


# Define your desired data structure.
class Alim(BaseModel):
    alim: list[str] = Field(description="Lista de compostos alimentares presentes na sentença")

#Recebe uma retrieval chain de uma sentença e retorna uma lista de medicamentos presentes
# pares (medicamento, dosagem_em_mg)
def AnaliseAlimentares(chain, llm, Verbose=False):

    la = [] #lista de compostos alimentares

    #Aqui o objetivo dos prompts é listar os itens que são compostos alimentares

    """
    Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

    Considere como compostos alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, excluindo medicamentos e suplementos farmacêuticos.

    Outros itens não alimentares, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros, não são compostos alimentares.

    Sua tarefa é fornecer uma lista contendo apenas os itens que são compostos alimentares na decisão judicial.
    """

    
    r1 = chain.invoke({"input": q1}).get('answer')

    parser = JsonOutputParser(pydantic_object=Alim)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos compostos alimentares.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser

    la = chain2.invoke({"query": r1}).get("meds") 
        
    return la

