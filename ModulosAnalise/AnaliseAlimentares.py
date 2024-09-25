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



# Define your desired data structure.
class Alim(BaseModel):
    alim: list[str] = Field(description="Lista de compostos alimentares presentes na sentença")

#Recebe uma retrieval chain de uma sentença e retorna uma lista de medicamentos presentes
# pares (medicamento, dosagem_em_mg)
def AnaliseAlimentares(docsearch, model="gpt-3.5-turbo", Verbose=False):

    #Prompts que podem ser utilizados:

    """
    Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

    Considere como compostos alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, excluindo medicamentos e suplementos farmacêuticos.

    Outros itens não alimentares, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros, não são compostos alimentares.

    Sua tarefa é fornecer uma lista contendo apenas os itens que são compostos alimentares na decisão judicial.
    """
    """
    Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

    Sua tarefa é identificar e listar apenas os itens relacionados à alimentação mencionados na decisão judicial. 

    Considere como compostos alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, incluindo dietas especiais como a dieta enteral. Exclua medicamentos e suplementos farmacêuticos.

    Ignore todos os itens não alimentares, como fraldas, seringas, luvas, oxímetros, leitos hospitalares, termômetros, entre outros.

    Forneça uma lista contendo apenas os compostos alimentares identificados na decisão judicial.
    """
    if model == "gpt-4" or model == "gpt-4o":
        llm = ChatOpenAI(model_name=model, temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, tais como medicamentos."
            "Sua tarefa consiste em extrair dos documentos os nomes dos itens relacionados à alimentação, caso possua algum."
            "Considere como itens alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, incluindo dietas especiais como a dieta enteral. Exclua medicamentos e suplementos farmacêuticos."
            "Utilize o contexto para responder às perguntas."
            "Seja conciso nas respostas."
            "Contexto: {context}"
        )
    elif model == "gpt-3.5-turbo":
        
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, tais como medicamentos."
            "Sua tarefa consiste em extrair dos documentos os nomes dos itens relacionados à alimentação, caso possua algum."
            "Considere como itens alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, incluindo dietas especiais como a dieta enteral. Exclua medicamentos e suplementos farmacêuticos."
            "Utilize o contexto para responder às perguntas."
            "Seja conciso nas respostas."
            "Contexto: {context}"
        )
    elif model == "gpt-3.5-turbo-16k":
        
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
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


    la = [] #lista de medicamentos
    cost = 0

    if model == "gpt-4" or model == "gpt-4o":
        #Aqui o objetivo dos prompts é listar os itens que são medicamentos
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

            Sua tarefa é identificar e listar apenas os itens relacionados à alimentação mencionados na decisão judicial. 

            Considere como itens alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, incluindo dietas especiais como a dieta enteral. Exclua medicamentos e suplementos farmacêuticos.

            Algumas marcas conhecidas destes itens são: FORTINI, TROPHI, NUTREN, NOVASOURCE.
            
            Alguns padrões que surgem nos nomes destes itens são: NUTRI, DIET, ENERGY, PROTEIN.

            Ignore todos os itens não alimentares, como fraldas, seringas, luvas, oxímetros, leitos hospitalares, termômetros, entre outros.

            Forneça uma lista contendo apenas os itens alimentares identificados na decisão judicial.
            
            Em hipótese alguma forneça na lista compostos que não estavam na decisão. Se não houverem itens alimentares, apenas responda que não há medicamentos.
        """
    elif model == "gpt-3.5-turbo":
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

            Sua tarefa é identificar e listar apenas os itens relacionados à alimentação mencionados na decisão judicial. 

            Considere como itens alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, incluindo dietas especiais como a dieta enteral. Exclua medicamentos e suplementos farmacêuticos.

            Ignore todos os itens não alimentares, como fraldas, seringas, luvas, oxímetros, leitos hospitalares, termômetros, entre outros.

            Forneça uma lista contendo apenas os itens alimentares identificados na decisão judicial.
            
            Em hipótese alguma forneça na lista compostos que não estavam na decisão. Se não houverem itens alimentares, apenas responda que não há medicamentos.
        """
    
    elif model == "gpt-3.5-turbo-16k":
        q1 = """
            Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial.

            Considere como itens alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, incluindo dietas especiais como a dieta enteral. Exclua medicamentos e suplementos farmacêuticos.

            Sua tarefa é identificar e listar apenas os itens relacionados à alimentação mencionados no resumo do documento. 

            Forneça uma lista contendo apenas os itens alimentares identificados na decisão judicial.
            
            Em hipótese alguma forneça na lista itens alimentares que não estavam na decisão. Se não houverem itens alimentares, apenas responda que não há medicamentos.
        """
    
    with get_openai_callback() as c1:
        r1 = chain.invoke({"input": q1}).get('answer')
        cost += c1.total_cost

    if Verbose:
        print(f"Itens Alimentares presentes no documento judicial: {r1}")
    
    #r1 = chain.invoke({"input": q1}).get('answer')

    parser = JsonOutputParser(pydantic_object=Alim)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos itens alimentares.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser
    
    with get_openai_callback() as c2:
        la = chain2.invoke({"query": r1}).get("alim")
        cost += c2.total_cost

    if Verbose:
        print(f"Itens Alimentares extraidos do documento judicial: {la}")   
 
    return (la, cost)

