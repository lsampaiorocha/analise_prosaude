#função para monitorar os custos
from langchain_community.callbacks import get_openai_callback
from langchain_openai.chat_models import ChatOpenAI

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


# Recebe uma retrieval chain e verifica se existe algum pedido de consulta, exame ou procedimento clínico/cirúrgico
def AnaliseConsultasProcedimentos(docsearch, model="gpt-3.5-turbo", Verbose=False, Resumo=True):

    if not Resumo:
        llm = ChatOpenAI(model_name=model, temperature=0)
        # Prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças relacionadas a tratamentos de saúde."
            "Sua tarefa consiste em verificar se o documento solicita ou obriga a realização de consultas, exames médicos ou procedimentos clínicos ou cirúrgicos."
            "Utilize o contexto para responder às perguntas."
            "Seja conciso nas respostas."
            "Contexto: {context}"
        )
    else:
        llm = ChatOpenAI(model_name=model, temperature=0)
        system_prompt = (
        "Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial."
        "Utilize o resumo para responder às perguntas."
        "Seja conciso nas respostas, entregando apenas as informações solicitadas."
        "Resumo: {context}"
        )

    # Prompt do chat
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    # Cria uma chain de perguntas e respostas
    question_answer_chain = create_stuff_documents_chain(llm, prompt)

    # Cria uma chain de retrieval para realizar as perguntas e respostas
    chain = create_retrieval_chain(docsearch.as_retriever(), question_answer_chain)

    if not Resumo:
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma petição ou decisão judicial.
        
            Sua tarefa consiste em detectar se o documento solicita ou obriga a realização de consultas, exames médicos ou procedimentos clínicos ou cirúrgicos.
                        
            Em hipótese alguma forneça informações que não estavam na decisão. 
            
            Responda apenas 'Sim' ou 'Não', especificando se houve uma solicitação ou obrigação de consulta, exame ou procedimento conforme foi especificado.
        """
    else:
        q1 = """
        Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial.
            
        Sua tarefa consiste em detectar se o documento solicita ou obriga a realização de consultas, exames médicos ou procedimentos clínicos ou cirúrgicos.
        
        Em hipótese alguma forneça informações que não estavam no resumo do documento. 
            
        Responda apenas 'Sim' ou 'Não', especificando se houve uma solicitação ou obrigação de consulta, exame ou procedimento conforme foi especificado.
        """
    
    with get_openai_callback() as c1:
        # Invoca a cadeia de análise com o prompt fornecido
        resposta = chain.invoke({"input": q1}).get('answer')
        
    cost = (c1.prompt_tokens, c1.completion_tokens)

    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_consulta_exame_procedimento = True if resposta.strip().lower().startswith('sim') else False

    if Verbose:
        print(f'=> Detectou Consulta, Exame ou Procedimento: {possui_consulta_exame_procedimento}')

    # Retorna o resultado encapsulado no modelo Pydantic
    return (possui_consulta_exame_procedimento, cost)

