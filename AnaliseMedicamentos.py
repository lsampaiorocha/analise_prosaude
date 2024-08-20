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
    quantidade: int = Field(default=0,description="Quantidade por mês")
    duracao: int = Field(default=0,description="Duração em meses")

#class Medicamentos(BaseModel):
#    meds: list[Medicamento] = Field(description="Lista de medicamentos com suas respectivas doses")
    
class Medicamentos(BaseModel):
    meds: list[Medicamento] = Field(description="Lista de medicamentos com seus nomes, dose, quantidade de caixas por mês, e duração do tratamento")

#Recebe uma retrieval chain e retorna uma lista de medicamentos presentes
# pares (medicamento, dosagem_em_mg)
def AnaliseMedicamentos(docsearch, model="gpt-3.5-turbo", Verbose=False, Resumo=True):

    #caso seja a análise de um documento, e não do seu resumo
    if not Resumo: 
        llm = ChatOpenAI(model_name=model, temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, tais como medicamentos."
            "Sua tarefa consiste em extrair dos documentos os nomes, dose, quantidade e duração do tratamento, quando estiverem presentes."
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
    #cost = 0

    if not Resumo:
        #Aqui o objetivo dos prompts é listar os itens que são medicamentos
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma petições ou decisão judicial.
        
            Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
        
            Outros itens médicos ou de assistência, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos
            
            Sua tarefa é fornecer uma lista contendo apenas os itens que são medicamentos na decisão judicial, com os seus nomes, doses, quantidade por mês e duração do tratamento em meses, na medida em que estiverem presentes.
                        
            Nunca calcule a dose total, o que interessa é a dose para cada caixa de medicamento.
            
            Em hipótese alguma forneça na lista medicamentos que não estavam na decisão. Se não houverem medicamentos, apenas responda que não há medicamentos.
        """
    else:
        q1 = """
        Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial.
            
        Sua tarefa é verificar se são listados medicamentos no resumo do documento, trazendo todas as informações sobre estes, tais como nomes, dose, quantidade por mês e duração em meses do tratamento.
        
        Em hipótese alguma forneça na lista medicamentos que não estavam no resumo do documento. Se não houverem medicamentos, apenas responda que não há medicamentos.
        """
    
    with get_openai_callback() as c1:
        r1 = chain.invoke({"input": q1}).get('answer')
        #cost += c1.total_cost

    cost1 = (c1.prompt_tokens, c1.completion_tokens)

    if Verbose:
        print(f"=> Medicamentos presentes no documento judicial: {r1}")
    
    parser = JsonOutputParser(pydantic_object=Medicamentos)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com nomes dos medicamentos, valor da dose em miligramas (MG), quantidade por mês e duração do tratamento em meses.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser
    
    with get_openai_callback() as c2:
        lm = chain2.invoke({"query": r1}).get("meds")
        #cost += c2.total_cost

    cost2 = (c2.prompt_tokens, c2.completion_tokens)

    if Verbose:
        print(f"=> Medicamentos extraidos do documento judicial: {lm}")  
    
    r = []
    
    #previne algumas situações chatas em que não é retornado no formato previsto
    for med in lm:
        """
        if 'dose' not in med:
            med['dose'] = 0
        if 'quantidade' not in med:
            med['quantidade'] = 0
        if 'duracao' not in med:
            med['duracao'] = 0 
        if 'nome' not in med:
            med['nome'] = ""
        """
    
        med.setdefault('dose', 0)
        med.setdefault('quantidade', 0)
        med.setdefault('duracao', 0)
        med.setdefault('nome', "")
        r.append((med['nome'], med['dose'], med['quantidade'], med['duracao']))
    
    if Verbose:
        print(f"=> Medicamentos no formato estruturado: {r}") 
        
    #calcula os tokens das duas chamadas
    cost = (cost1[0] + cost2[0], cost1[1] + cost2[1])
 
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