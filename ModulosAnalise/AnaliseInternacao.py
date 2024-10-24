#função para monitorar os custos
from langchain_community.callbacks import get_openai_callback
from langchain_openai.chat_models import ChatOpenAI

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


#Recebe uma retrieval chain e verificar se existe algum pedido de internação
# pares (medicamento, dosagem_em_mg)
def AnaliseInternacao(docsearch, model="gpt-3.5-turbo", Verbose=False, Resumo=True):

    #cost = 0

    if not Resumo:
        llm = ChatOpenAI(model_name=model, temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando documentos jurídicos que podem conter petições, decisões ou sentenças de fornecimento de itens de saúde, tais como medicamentos."
            "Sua tarefa consiste em verificar se o documento solicita ou obriga a internação em leito hospitalar, Unidade de Terapia Intensiva (UTI) ou Unidade de Cuidados Especiais (UCE)."
            "Utilize o contexto para responder às perguntas."
            "Seja conciso nas respostas."
            "Contexto: {context}"
        )
    else:
        llm = ChatOpenAI(model_name=model, temperature=0)
        system_prompt = (
        "Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial."
        "Utilize as informações do resumo para responder às perguntas. "
        "Considere como internação ou transferência para leito hospitalar como qualquer tipo de internação ou tranferência para unidades especializadas de saúde. Isto deve incluir UTIs (Unidades de Terapia Intensiva), UCEs (Unidades de Cuidados Especiais) e unidades de internação psiquiátrica ou para tratamento de drogas, dentre outras."        
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


    if not Resumo:
        q1 = """
            Você é um assessor jurídico analisando um documento que contém uma petições ou decisão judicial.
        
            Sua tarefa consiste em detectar se o documento solicita ou obriga a internação ou transferência para leito hospitalar, Unidade de Terapia Intensiva (UTI) ou Unidade de Cuidados Especiais (UCE).
                        
            Em hipótese alguma forneça informações que não estavam na decisão. 
            
            Responda apenas 'Sim' ou 'Não', especificando se houve uma solicitação ou obrigação de internação ou transferência conforme foi especificado.
        """
    else:
        q1 = """
        Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial.
        
        Considere como internação ou transferência para leito hospitalar como qualquer tipo de internação ou tranferência para unidades especializadas de saúde. Isto deve incluir UTIs (Unidades de Terapia Intensiva), UCEs (Unidades de Cuidados Especiais) e unidades de internação psiquiátrica ou para tratamento de drogas, dentre outras.
            
        Sua tarefa consiste em verificar no resumo se **Há Internação ou Transferência para leito hospitalar** e responder apenas 'Sim' ou 'Não', de acordo com o que foi dito no resumo.
        """
    
    with get_openai_callback() as c1:
        # Invoca a cadeia de análise com o prompt fornecido
        resposta = chain.invoke({"input": q1}).get('answer')
        #cost += c1.total_cost
        
    cost = (c1.prompt_tokens, c1.completion_tokens)

    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_internacao = True if resposta.strip().lower().startswith('sim') else False

    if Verbose:
        print(f'=> Detectou Internação: {possui_internacao}')

    # Retorna o resultado encapsulado no modelo Pydantic
    return (possui_internacao, cost)
