#função para monitorar os custos
from langchain_community.callbacks import get_openai_callback
from langchain_openai.chat_models import ChatOpenAI

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document


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
def AnaliseMedicamentos(docsearch, model="gpt-3.5-turbo", Verbose=False, Resumo=True):

    #caso seja a análise de um documento, e não do seu resumo
    if not Resumo: 
        llm = ChatOpenAI(model_name=model, temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, tais como medicamentos."
            "Sua tarefa consiste em extrair dos documentos os nomes e as dosagens de medicamentos, caso possua."
            "Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. "
            "Utilize o contexto para responder às perguntas."
            "Seja conciso nas respostas."
            "Contexto: {context}"
        )
    #caso seja a análise de um resumo de documento
    else: 
        llm = ChatOpenAI(model_name=model, temperature=0)
        system_prompt = (
        "Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial."
        "Utilize o resumo para responder às perguntas. "
        "Seja conciso nas respostas, entregando apenas as informações solicitadas"
        "Resumo: {context}"
        )


    #prompt do chat
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    #cria uma chain de perguntas e respostas
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    #cria uma chain de retrieval para realizar as perguntas e respostas
    chain = create_retrieval_chain(docsearch.as_retriever(), question_answer_chain)


    lm = [] #lista de medicamentos
    cost = 0

    if not Resumo:
        #Aqui o objetivo dos prompts é listar os itens que são medicamentos
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma petições ou decisão judicial.
        
            Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
        
            Outros itens médicos ou de assistência, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos
            
            Sua tarefa é fornecer uma lista contendo apenas os itens que são medicamentos na decisão judicial e a dosagem em miligramas(MG).
            
            Nunca calcule a dosagem total, o que interessa é a dosagem para cada caixa de medicamento.
            
            Em hipótese alguma forneça na lista medicamentos que não estavam na decisão. Se não houverem medicamentos, apenas responda que não há medicamentos.
        """
    else:
        q1 = """
        Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial.
            
        Sua tarefa é verificar se são listados medicamentos no resumo do documento, trazendo todas as informações sobre estes, tais como nomes, dosagem, quantidade e duração do tratamento.
        
        Em hipótese alguma forneça na lista medicamentos que não estavam no resumo do documento. Se não houverem medicamentos, apenas responda que não há medicamentos.
        """
    
    with get_openai_callback() as c1:
        r1 = chain.invoke({"input": q1}).get('answer')
        cost += c1.total_cost

    if Verbose:
        print(f"=> Medicamentos presentes no documento judicial: {r1}")
    
    parser = JsonOutputParser(pydantic_object=Medicamentos)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos medicamentos e o valor da dosagem em miligramas (MG).\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser
    
    with get_openai_callback() as c2:
        lm = chain2.invoke({"query": r1}).get("meds")
        cost += c2.total_cost

    if Verbose:
        print(f"=> Medicamentos extraidos do documento judicial: {lm}")  
    
    r = []
    
    #previne algumas situações chatas em que não é retornado no formato previsto
    for med in lm:
        if 'dose' not in med:
            med['dose'] = 0 
        if 'nome' not in med:
            med['nome'] = ""
        r.append((med['nome'], med['dose']))
    
    if Verbose:
        print(f"=> Medicamentos já dentro da estrutura: {r}") 
 
    return (r, cost)


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