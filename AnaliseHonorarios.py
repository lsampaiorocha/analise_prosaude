#função para monitorar os custos
from langchain_community.callbacks import get_openai_callback
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

#Recebe uma retrieval chain de uma sentença e retorna Sim ou não se houve condenação do estado do ceará ao pagamento de honorários
def AnaliseHonorarios(docsearch, model="gpt-3.5-turbo", Verbose=False, Resumo=True):
    
    #cost = 0

    #caso seja análise de um documento, e não do seu resumo
    if not Resumo:
        llm = ChatOpenAI(model_name=model, temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando um documento que contém uma decisão judicial."
            "Utilize o contexto para responder às perguntas. "
            "Seja conciso nas respostas, entregando apenas as informações solicitadas"
            "Contexto: {context}"
            )  
    #caso seja análise de um resumo
    else:
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
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
    
    if not Resumo:
        q1 = """
        Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

        Seu objetivo é verificar se o Estado do Ceará foi condenado ao pagamento de honorários advocatícios, também chamados de honorários sucumbenciais. 
        
        Considere que a condenação de honorários sucumbenciais em uma sentença de uma ação refere-se à obrigação imposta pela justiça ao partido perdedor de uma ação judicial de pagar os honorários advocatícios do advogado da parte vencedora.
        
        As condenações podem variar em forma e valor, por vezes fixados em percentual sobre o valor da causa, em valores absolutos ou determinados por equidade.

        Revise o documento e responda apenas 'Sim' ou 'Não', especificando se houve uma condenação do Estado do Ceará ao pagamento de honorários advocatícios.

        """
    else:
        q1 = """
        Você é um assessor jurídico analisando o resumo de um documento que contém uma petição ou decisão judicial.

        Seu objetivo é verificar se o Estado do Ceará foi condenado ao pagamento de honorários advocatícios, também chamados de honorários sucumbenciais. 
        
        Considere que a condenação de honorários sucumbenciais em uma sentença de uma ação refere-se à obrigação imposta pela justiça ao partido perdedor de uma ação judicial de pagar os honorários advocatícios do advogado da parte vencedora.
        
        As condenações podem variar em forma e valor, por vezes fixados em percentual sobre o valor da causa, em valores absolutos ou determinados por equidade.

        Responda apenas 'Sim' ou 'Não', especificando se houve uma condenação do Estado do Ceará ao pagamento de honorários advocatícios.

        """
        
    with get_openai_callback() as c1:
        # Invoca a cadeia de análise com o prompt fornecido
        resposta = chain.invoke({"input": q1}).get('answer')
        #cost += c1.total_cost

    cost = (c1.prompt_tokens, c1.completion_tokens)
    
    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_indenizacao = True if resposta.strip().lower().startswith('sim') else False
    
    if Verbose:
        print(f'=> Detectou condenação por honorário: {possui_indenizacao}')

    # Retorna o resultado encapsulado no modelo Pydantic
    return (possui_indenizacao, cost)


