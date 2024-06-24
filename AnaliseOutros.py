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


import re

class Outros(BaseModel):
    outr: list[str] = Field(description="Lista de itens presentes na petição ou decisão que não são medicamentos")


def AnaliseOutrosLLM(docsearch, model="gpt-3.5-turbo", Verbose=False):
    
    
    if model == "gpt-4":
        llm = ChatOpenAI(model_name="gpt-4", temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, tais como consultas, exames, medicamentos, procedimentos, etc."
            "Sua tarefa consiste em identificar e extrair do documento os produtos ou serviços que foram solicitados que não sejam medicamentos."
            "Utilize o contexto para responder às perguntas."
            "Seja conciso nas respostas, entregando apenas as informações solicitadas"
            "Contexto: {context}"
        )

        #prompt do chat
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
    elif model == "gpt-3.5-turbo":
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        system_prompt = (
        "Você é um assessor jurídico analisando um documento que contém uma decisão judicial."
        "Utilize o contexto para responder às perguntas. "
        "Seja conciso nas respostas, entregando apenas as informações solicitadas"
        "Contexto: {context}"
        )

    #cria uma chain de perguntas e respostas
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    #cria uma chain de retrieval para realizar as perguntas e respostas
    chain = create_retrieval_chain(docsearch.as_retriever(), question_answer_chain)


    lo = [] #lista de medicamentos
    cost = 0


    if model == "gpt-4":
        #Aqui o objetivo dos prompts é listar os itens que não são medicamentos
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma petição ou decisão judicial.
            Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
            Outros itens médicos ou de assistência que não são medicamentos são: fraldas, compostos para dieta enteral, consulta médica, cirurgia, procedimento, terapia, atendimento com médico, cadeira de roda, internação, UTI, UCE, leitos hospitalares, fralda, seringas, agulhas, dentre vários outros insumos e serviços médicos.
            Sua tarefa é fornecer uma lista contendo apenas os outros itens médicos, que não sejam medicamentos, do documento.
            Em hipótese alguma forneça itens que não estavam na decisão. Se não houverem itens que não sejam medicamentos, responda que não há itens.
        """
    elif model == "gpt-3.5-turbo":
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma petição ou decisão judicial.
            Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
            Outros itens médicos ou de assistência que não são medicamentos são: fraldas, compostos para dieta enteral, consulta médica, cirurgia, procedimento, terapia, atendimento com médico, cadeira de roda, internação, UTI, UCE, leitos hospitalares, fralda, seringas, agulhas, dentre vários outros insumos e serviços médicos.
            Sua tarefa é fornecer uma lista contendo apenas os outros itens médicos, que não sejam medicamentos, do documento.
            Em hipótese alguma forneça itens que não estavam na decisão. Se não houverem itens que não sejam medicamentos, responda que não há itens.
        """
        
    with get_openai_callback() as c1:
        r1 = chain.invoke({"input": q1}).get('answer')
        cost += c1.total_cost

    
    if Verbose:
        print(f"Outros itens presentes no documento judicial: {r1}")
    

    parser = JsonOutputParser(pydantic_object=Outros)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos outros itens que não sejam medicamentos.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser

    with get_openai_callback() as c2:
        lo = chain2.invoke({"query": r1}).get("outr")
        cost += c2.total_cost

    if Verbose:
        print(f"Outros itens extraidos do documento judicial: {lo}")  
 
    return (len(lo) != 0, lo, cost)

#Recebe um conjunto de páginas e verifica se ocorre alguma das palavras proibitivas
def AnaliseOutrosRegex(pages, Verbose=False):
    
    #palavras que tiveram que ser retiradas: procedimento, consulta, tratamento
    # Definindo palavras-chave importantes - OBS: Errar por excesso não é problema, o problema maior é não detectar
    palavras_filtro = ['aliment', 'enteral', 'dieta', 'Energy','sonda','frasco','fralda', 'álcool', 'atadura', 'tubo',
                       'gase', 'luvas', 'esparadrapo', 'algodão','cama', 'colchão', 'UTI', 'UCE', 'seringa', 'aspirador',
                       'terapia', 'exame', 'consulta médica', 'procedimento cirúrgico', 'cirurgia', 'cadeira de roda', 
                       'internação', 'sessão de laser', 'sessão de fisio', 'atendimento com médico',
                       'tratamento cirúrgico', 'equipo', 'suplementação alimentar', 'compostos alimentares',
                       'sensor de glicose', 'insulina', 'fonoaudiólogo', 'fisioterapia', 'CPAP', 
                       'aparelho', 'BIPAP', 'umidificador', 'mascara', 'psicopedagógico', 'psicólogo', 'psiquiatr', 'agulha']
    
    
    # Aplicando a função de normalização para lidar com acentos e assegurar espaço em branco no início
    #regex_patterns = [r'\b' + normalize_regex(re.escape(keyword)).replace(r'\ ', r'\s+') + r'\b' for keyword in palavras_filtro]
    regex_patterns = [r'\b' + normalize_regex(re.escape(keyword)).replace(r'\ ', r'\s+') for keyword in palavras_filtro]
    filtro_regex = re.compile('|'.join(regex_patterns), re.IGNORECASE)
    
    # Filtrando páginas com base nas palavras-chave
    filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
    
    # Conjunto para armazenar palavras-chave únicas encontradas
    unique_keywords = set()

    # Analisando cada página para correspondências
    for page in pages:
        matches = filtro_regex.findall(page.page_content)
        if matches:
            # Adicionando correspondências ao conjunto, que automaticamente remove duplicatas
            unique_keywords.update([match.lower() for match in matches])  # Converte para lowercase para evitar duplicatas por case
    
    #necessário para apresentar onde foram identificados os padrões e que padrões foram identificados
    if Verbose:
        if len(filtered_pages) > 0:
            print("Correspondências encontradas na análise de Outros itens:")
            # Estrutura para capturar trechos correspondentes
            filtered_pages_with_matches = [
            (page, [match.group(0) for match in filtro_regex.finditer(page.page_content)])
            for page in pages
            if filtro_regex.search(page.page_content)
            ]
            # Agora filtered_pages_with_matches contém tuplas de página e lista de todos os trechos correspondentes
            for page, matches in filtered_pages_with_matches:
                print(f"Na página {page.metadata['page']}: Correspondências encontradas - {matches}")
    
    
    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_outros = True if len(filtered_pages) > 0 else False
    
    if Verbose:
        print(f"Possui outros itens: {possui_outros} Quais: {list(unique_keywords)}")

    # Retorna o resultado encapsulado no modelo Pydantic
    return (possui_outros, list(unique_keywords))


# Criando uma função para substituir letras acentuadas por regex que aceita ambas as formas
def normalize_regex(keyword):
    replacements = {
        'á': '[aá]', 'é': '[eé]', 'í': '[ií]', 'ó': '[oó]', 'ú': '[uú]',
        'â': '[aâ]', 'ê': '[eê]', 'î': '[iî]', 'ô': '[oô]', 'û': '[uû]',
        'ã': '[aã]', 'õ': '[oõ]',
        'ç': '[cç]'
    }
    for accented, regex in replacements.items():
        keyword = re.sub(accented, regex, keyword)
    return keyword

