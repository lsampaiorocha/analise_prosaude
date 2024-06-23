#from langchain.chains import create_retrieval_chain
#from langchain.chains.combine_documents import create_stuff_documents_chain


#Recebe uma retrieval chain de uma sentença e retorna Sim ou não se houve condenação do estado do ceará ao pagamento de honorários
def AnaliseHonorarios(chain, llm, Verbose=False):
      
    q1 = """
    Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

    Seu objetivo é verificar se o Estado do Ceará foi condenado ao pagamento de honorários advocatícios, também chamados de honorários sucumbenciais. 
    
    Considere que a condenação de honorários sucumbenciais em uma sentença de uma ação refere-se à obrigação imposta pela justiça ao partido perdedor de uma ação judicial de pagar os honorários advocatícios do advogado da parte vencedora.
    
    As condenações podem variar em forma e valor, por vezes fixados em percentual sobre o valor da causa, em valores absolutos ou determinados por equidade.

    Revise o documento e responda apenas 'Sim' ou 'Não', especificando se houve uma condenação do Estado do Ceará ao pagamento de honorários advocatícios.

    """

    # Invoca a cadeia de análise com o prompt fornecido
    resposta = chain.invoke({"input": q1}).get('answer')

    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_indenizacao = True if resposta.strip().lower().startswith('sim') else False

    # Retorna o resultado encapsulado no modelo Pydantic
    return possui_indenizacao


