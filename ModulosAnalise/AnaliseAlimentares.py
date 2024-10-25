# Função para monitorar os custos
from langchain_community.callbacks import get_openai_callback
from langchain_openai.chat_models import ChatOpenAI

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

# Organizar outputs
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# Define a estrutura de dados desejada para alimentos
class Alimento(BaseModel):
    nome: str = Field(default="N/A", description="Nome do composto alimentar")
    quantidade: int = Field(default=0, description="Quantidade por mês")
    duracao: int = Field(default=0, description="Duração em meses")

class Alimentos(BaseModel):
    alim: list[Alimento] = Field(description="Lista de compostos alimentares com nome, quantidade por mês e duração")

# Função de análise de itens alimentares
def AnaliseAlimentares(docsearch, model="gpt-3.5-turbo", Verbose=False, Resumo=True):

    # Definição do modelo e prompt de sistema
    llm = ChatOpenAI(model_name=model, temperature=0)
    if Resumo:
        system_prompt = (
            "Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial."
            "Utilize o resumo para responder às perguntas. Seja conciso nas respostas, entregando apenas as informações solicitadas."
            "Resumo: {context}"
        )
    else:
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, como itens alimentares."
            "Sua tarefa consiste em extrair dos documentos os nomes dos itens relacionados à alimentação, quantidade e duração do tratamento, quando estiverem presentes."
            "Considere como compostos alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir ou complementar a dieta, como a dieta enteral. Medicamentos não são itens alimentares."
            "Contexto: {context}"
        )

    # Template do prompt do chat
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    # Criação da chain de perguntas e respostas
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    # Chain de retrieval para perguntas e respostas
    chain = create_retrieval_chain(docsearch.as_retriever(), question_answer_chain)

    la = []  # Lista de alimentos
    if not Resumo:
        q1 = """
            Você é um assessor jurídico analisando um documento judicial.
            Considere que compostos Nutricionais e/ou Dietas Especiais são Suplementos ou regimes alimentares específicos recomendados para atender às necessidades nutricionais de pacientes com condições de saúde particulares, como alergias, intolerâncias, deficiências nutricionais ou doenças crônicas, visando promover ou restaurar a saúde. Eles não devem ser confundidos com medicamentos.
            Sua tarefa é fornecer uma lista com os compostos nutricionais mencionados na decisão, como nome, quantidade por mês e duração em meses caso estas informações estejam presentes.
            Forneça apenas a lista com os itens e suas informações, e indique caso não haja nenhum item desta categoria.
        """
    else:
        q1 = """
            Você é um assessor jurídico analisando o resumo de um documento judicial.
            Considere que compostos Nutricionais e/ou Dietas Especiais são Suplementos ou regimes alimentares específicos recomendados para atender às necessidades nutricionais de pacientes com condições de saúde particulares, como alergias, intolerâncias, deficiências nutricionais ou doenças crônicas, visando promover ou restaurar a saúde. Eles não devem ser confundidos com medicamentos.
            Sua tarefa é fornecer uma lista com os compostos Nutricionais mencionados no resumo, incluindo nomes, quantidade por mês e duração em meses, caso estas informações estejam presentes.
            Forneça apenas a lista com os itens e suas informações, e indique caso não haja nenhum item desta categoria.
        """

    # Chamadas de API e monitoramento de custos
    with get_openai_callback() as c1:
        r1 = chain.invoke({"input": q1}).get("answer")

    cost1 = (c1.prompt_tokens, c1.completion_tokens)

    if Verbose:
        print(f"=> Compostos alimentares presentes no documento: {r1}")

    # Definindo o parser
    parser = JsonOutputParser(pydantic_object=Alimentos)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com nomes dos compostos alimentares, quantidade por mês e duração em meses.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser

    with get_openai_callback() as c2:
        la = chain2.invoke({"query": r1}).get("alim")

    cost2 = (c2.prompt_tokens, c2.completion_tokens)

    if Verbose:
        print(f"=> Compostos alimentares extraídos: {la}")

    # Formatação estruturada dos resultados
    r = []
    for alimento in la:
        alimento.setdefault("nome", "")
        alimento.setdefault("quantidade", 0)
        alimento.setdefault("duracao", 0)
        r.append((alimento["nome"], alimento["quantidade"], alimento["duracao"]))

    if Verbose:
        print(f"=> Compostos alimentares no formato estruturado: {r}")

    # Cálculo total de custos
    cost = (cost1[0] + cost2[0], cost1[1] + cost2[1])

    return r, cost
