from langchain_community.vectorstores import Chroma

from langchain_core.prompts import PromptTemplate

#organizar outputs
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

from dotenv import load_dotenv


# Define your desired data structure.
#class Meds(BaseModel):
#    meds: list[str] = Field(description="Lista de medicamentos presentes na sentença")
class Medicamento(BaseModel):
    nome: str = Field(default="N/A",description="Nome do medicamento")
    dose: int = Field(default=0,description="Dose do medicamento em miligramas")

class Medicamentos(BaseModel):
    meds: list[Medicamento] = Field(description="Lista de medicamentos com suas respectivas doses")
    

#Recebe uma retrieval chain de uma sentença e retorna uma lista de medicamentos presentes
# pares (medicamento, dosagem_em_mg)
def AnaliseMedicamentos(chain, llm, Verbose=False):

    lm = [] #lista de medicamentos

    #Aqui o objetivo dos prompts é listar os itens que são medicamentos

    q1 = """
        Você é um assessor jurídico analisando um documento que contém uma decisão judicial.
    
        Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
    
        Outros itens médicos ou de assistência, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos
        
        Sua tarefa é fornecer uma lista contendo apenas os itens que são medicamentos na decisão judicial e a dosagem em miligramas(MG).
        
        Em hipótese alguma forneça na lista medicamentos que não estavam na decisão. Se não houverem medicamentos, apenas responda que não há medicamentos.
    """
    
    r1 = chain.invoke({"input": q1}).get('answer')
    
    
    if Verbose:
        print(f"Medicamentos presentes na sentença: {r1}")
    

    parser = JsonOutputParser(pydantic_object=Medicamentos)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos medicamentos e o valor da dosagem em miligramas (MG).\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser

    lm = chain2.invoke({"query": r1}).get("meds")

    if Verbose:
        print(f"Medicamentos extraidos da sentença: {lm}")  
    
    r = []
    
    #previne algumas situações chatas em que não é retornado no formato previsto
    for med in lm:
        if 'dose' not in med:
            med['dose'] = 0 
        if 'nome' not in med:
            med['nome'] = ""
        r.append((med['nome'], med['dose']))
    
    if Verbose:
        print(f"Medicamentos já dentro da estrutura: {r}") 
 
    return r


#Recebe uma lista com tuplas (medicamento, dose_em_mg, nome_comercial, registro_anvisa, valor)
#e verifica se respeita o limite de 60 salários mínimos
#Por fazer
def VerificaTeto(lm):
    
    total = 0
    res = True
    
    #adiciona as informações de medicamentos obtidas
    for idx, (principio, nome_comercial, num_registro, preco) in enumerate(lm):
        if preco != None:
            total += 12*preco
    
    if total > 1640*60:
        res = False
        
        
    return (res, total)