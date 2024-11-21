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


#prompt para detecção de outros itens de uma sentença usando LLM
def DetectaOutrosLLM(docsearch, model="gpt-3.5-turbo", Verbose=False, Resumo=True):
    
    
    if not Resumo:
        llm = ChatOpenAI(model_name=model, temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, tais como consultas, exames, medicamentos, procedimentos, etc."
            "Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças."            
            "Sua tarefa consiste em detectar se existem no documento produtos ou serviços tenham sido solicitados para fornecimento e que não sejam medicamentos."
            "Utilize o contexto para responder às perguntas."
            "Seja conciso nas respostas, entregando apenas as informações solicitadas"
            "Contexto: {context}"
        )
    else:
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

    #cost = 0

    if not Resumo:
        #Aqui o objetivo dos prompts é listar os itens que não são medicamentos
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma petição ou decisão judicial.
            Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
            Outros itens médicos ou de assistência que não são medicamentos são: fraldas, compostos para dieta enteral, consulta médica, exame, cirurgia, procedimento, terapia, atendimento com médico, cadeira de roda, internação, UTI, UCE, leitos hospitalares, fralda, seringas, agulhas, dentre vários outros insumos e serviços médicos.
            Sua tarefa é detectar se existem outros itens médicos, que não sejam medicamentos, no documento.
            Responda apenas Sim ou Não, se estão presentes no documento itens que não sejam medicamentos.
        """
    else:
        q1 = """
            Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial.
            Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
            Outros itens médicos ou de assistência que não são medicamentos são: fraldas, compostos para dieta enteral, consulta médica, exame, cirurgia, procedimento, terapia, atendimento com médico, cadeira de roda, internação, UTI, UCE, leitos hospitalares, fralda, seringas, agulhas, dentre vários outros insumos e serviços médicos.
            Sua tarefa é detectar se existem outros itens médicos, que não sejam medicamentos, no documento.
            Responda apenas Sim ou Não, se estão presentes no documento itens que não sejam medicamentos
        """
        
    with get_openai_callback() as c1:
        r1 = chain.invoke({"input": q1}).get('answer')
        #cost += c1.total_cost
        
    cost = (c1.prompt_tokens, c1.completion_tokens)

    if Verbose:
        print(f"Outros itens foram detectados por LLM: {r1}")  
        
    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_outros = True if r1.strip().lower().startswith('sim') else False
 
    return (possui_outros, cost)



#Recebe um conjunto de páginas e verifica se ocorre alguma das palavras proibitivas
def AnaliseOutrosRegex(pages, Verbose=False):
    
    #palavras que tiveram que ser retiradas: procedimento, consulta, tratamento
    # Definindo palavras-chave importantes - OBS: Errar por excesso não é problema, o problema maior é não detectar
    # Estas são as palavras chaves
    """
    palavras_filtro_permitidos = ['aliment', 'enteral', 'dieta', 'Energy','sonda','frasco','fralda', 'álcool', 'atadura', 'tubo',
                       'gase', 'luvas', 'esparadrapo', 'algodão', 'colchão', 'UTI ', 'terapia intensiva', 'UCE', 'cuidados especiais', 
                       'seringa', 'aspirador', 'terapia', 'exame', 'consulta médica', 'internação', 'sessão de laser', 'sessão de fisio', 
                       'atendimento com médico', 'equipo', 'suplementação alimentar', 'compostos alimentares','sensor de glicose', 
                       'insulina', 'fonoaudiólogo', 'fisioterapia', 'CPAP', 'aparelho', 'BIPAP', 'umidificador', 'mascara', 
                       'psicopedagógico', 'psicólogo', 'psiquiatr', 'agulha']
    
    
    #versão ajustada para uso com resumos e também por haver o detector de internação
    palavras_filtro_permitidos = ['sonda','frasco','fralda', 'álcool', 'atadura', 'tubo',
                       'gase', 'luvas', 'esparadrapo', 'algodão', 'colchão','seringa', 'aspirador', 
                       'equipo', 'sensor de glicose', 'insulina',  'umidificador', 'mascara', 'agulha']
    """
    
    palavras_filtro_permitidos = ['frasco', 'hidratante', 'umidificador', 'mascara', 
				  'agulha', 'sonda', 'frasco', 'fralda', 'álcool', 'atadura', 
                                  'tubo', 'gase', 'luvas', 'esparadrapo', 'algodão', 'colchão','seringa', 'aspirador', 
                                  'equipo', 'sensor', 'cama', 'cadeira de roda'
                                  ]

    
    
    # Aplicando a função de normalização para lidar com acentos e assegurar espaço em branco no início
    #regex_patterns = [r'\b' + normalize_regex(re.escape(keyword)).replace(r'\ ', r'\s+') + r'\b' for keyword in palavras_filtro]
    regex_patterns = [r'\b' + normalize_regex(re.escape(keyword)).replace(r'\ ', r'\s+') for keyword in palavras_filtro_permitidos]
    filtro_regex = re.compile('|'.join(regex_patterns), re.IGNORECASE)
    
    # Filtrando páginas com base nas palavras-chave
    filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
    
    # Conjunto para armazenar palavras-chave únicas encontradas
    outros_permitidos = set()

    # Analisando cada página para correspondências
    for page in pages:
        matches = filtro_regex.findall(page.page_content)
        if matches:
            # Adicionando correspondências ao conjunto, que automaticamente remove duplicatas
            outros_permitidos.update([match.lower() for match in matches])  # Converte para lowercase para evitar duplicatas por case
    
    #necessário para apresentar onde foram identificados os padrões e que padrões foram identificados
    if Verbose:
        if len(filtered_pages) > 0:
            print("Correspondências encontradas - Outros itens PERMITIDOS:")
            # Estrutura para capturar trechos correspondentes
            filtered_pages_with_matches = [
            (page, [match.group(0) for match in filtro_regex.finditer(page.page_content)])
            for page in pages
            if filtro_regex.search(page.page_content)
            ]
            # Agora filtered_pages_with_matches contém tuplas de página e lista de todos os trechos correspondentes
            for page, matches in filtered_pages_with_matches:
                print(f"Na página {page.metadata['page']}: Outros itens PERMITIDOS - {matches}")
    
    
    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_outros_permitidos = True if len(filtered_pages) > 0 else False
    
    if Verbose:
        print(f"Possui Outros itens PERMITIDOS: {possui_outros_permitidos} Quais: {list(outros_permitidos)}")


    #palavras que tiveram que ser retiradas: procedimento, consulta, tratamento
    # Definindo palavras-chave importantes - OBS: Errar por excesso não é problema, o problema maior é não detectar
    # Estas são as palavras chaves
    """
    palavras_filtro_proibidas = ['cama', 'procedimento cirúrgico', 'cirurgia', 'cadeira de roda', 'tratamento cirúrgico']
    
    palavras_filtro_proibidas = ['aliment', 'enteral', 'dieta', 'Energy', 'cama', 'procedimento cirúrgico', 
                                 'cirurgia', 'cadeira de roda', 'tratamento cirúrgico', 'exame', 'consulta médica',
                                 'sessão de laser', 'sessão de fisio', 'atendimento com médico',
                                 'suplementação alimentar', 'compostos alimentares', 'fonoaudiólogo', 'fisioterapia', 'CPAP', 
                                 'aparelho', 'BIPAP','psicopedagógico', 'psicólogo', 'psiquiatr',]
    """
    palavras_filtro_proibidas = ['insulina']
    
    # Aplicando a função de normalização para lidar com acentos e assegurar espaço em branco no início
    #regex_patterns = [r'\b' + normalize_regex(re.escape(keyword)).replace(r'\ ', r'\s+') + r'\b' for keyword in palavras_filtro]
    regex_patterns = [r'\b' + normalize_regex(re.escape(keyword)).replace(r'\ ', r'\s+') for keyword in palavras_filtro_proibidas]
    filtro_regex = re.compile('|'.join(regex_patterns), re.IGNORECASE)
    
    # Filtrando páginas com base nas palavras-chave
    filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
    
    # Conjunto para armazenar palavras-chave únicas encontradas
    outros_proibidos = set()

    # Analisando cada página para correspondências
    for page in pages:
        matches = filtro_regex.findall(page.page_content)
        if matches:
            # Adicionando correspondências ao conjunto, que automaticamente remove duplicatas
            outros_proibidos.update([match.lower() for match in matches])  # Converte para lowercase para evitar duplicatas por case
    
    #necessário para apresentar onde foram identificados os padrões e que padrões foram identificados
    if Verbose:
        if len(filtered_pages) > 0:
            print("Correspondências encontradas - Outros itens PROIBIDOS:")
            # Estrutura para capturar trechos correspondentes
            filtered_pages_with_matches = [
            (page, [match.group(0) for match in filtro_regex.finditer(page.page_content)])
            for page in pages
            if filtro_regex.search(page.page_content)
            ]
            # Agora filtered_pages_with_matches contém tuplas de página e lista de todos os trechos correspondentes
            for page, matches in filtered_pages_with_matches:
                print(f"Na página {page.metadata['page']}: Outros itens PROIBIDOS - {matches}")
    
    
    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_outros_proibidos = True if len(filtered_pages) > 0 else False
    
    if Verbose:
        print(f"Possui Outros itens PROIBIDOS: {possui_outros_proibidos} Quais: {list(outros_proibidos)}")


    return (possui_outros_permitidos, list(outros_permitidos), possui_outros_proibidos, list(outros_proibidos))


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

