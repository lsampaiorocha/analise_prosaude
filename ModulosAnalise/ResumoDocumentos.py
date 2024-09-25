from langchain_openai import ChatOpenAI
import openai

from langchain_community.callbacks import get_openai_callback

from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate

#from AnalisePortaria import CustoGpt4o



def GeraResumo(pages, model, api_key, Verbose=False):
  openai.api_key = api_key
    
  try:
    
    prompt_template = """
        Você é um assessor jurídico e precisa resumir o conteúdo de um documento solicitando ou obrigando a fornecer itens e/ou serviços da área médica.
        Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
        Outros itens médicos ou de assistência, como fraldas, compostos alimentares, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos.
        Em hipótese alguma forneça na lista medicamentos que não estavam na decisão. Se não houverem medicamentos, apenas responda que não há medicamentos.
        O resumo deve ser escrito em português do Brasil e deve conter as seguintes informações:

        **Resumo do Documento**

        - **Tipo de Documento:** Indique se é uma Sentença, Decisão Interlocutória, Petição Inicial
        - **Valor da Causa:** Informe o valor da causa
        - **Itens a serem fornecidos:**
          - **Medicamentos:**
            - Liste os medicamentos com suas dosagens e quantidades
          - **Serviços:**
            - Liste os serviços necessários
        - **Dosagem, Quantidade e Duração do Tratamento:**
          - Detalhe as dosagens, quantidades e duração do tratamento para cada medicamento
        - **Internação ou Transferência para UTI/UCE:** Informe se há solicitação ou obrigação de internação ou transferência para UTI ou UCE.
        - **Danos Morais:** Informe se há solicitação ou condenação por danos morais.
        - **Honorários:** Detalhe se há condenação por honorários, especificando quem foi condenado e o valor.
        - **Multa ou Bloqueio de Recursos:** Detalhe se há condenação por multa ou bloqueio de recursos, especificando o valor.
        - **Pedido de Liminar ou Antecipação de Tutela:** Informe se há pedido de liminar ou antecipação de tutela.
        - **Deferimento ou Indeferimento do pedido liminar ou antecipação de tutela:** Informe se foi deferido, indeferido ou não se aplica.

        **Detalhes Adicionais:**
        - **Requerente:** Informe o nome do requerente e, se for o caso, quem ele representa.
        - **Requeridos:** Liste os requeridos.
        - **Fundamentação:** Resuma em poucas linhas do que trata o documento.

        "{text}"
        Resumo do texto:"""
    
       
    prompt = PromptTemplate.from_template(prompt_template)
    
    #llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    llm = ChatOpenAI(temperature=0, model_name=model)
    
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    # Define StuffDocumentsChain
    
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
    
    with get_openai_callback() as c1:
        r1 = stuff_chain.invoke({"input_documents": pages})
        cost = c1.total_cost
    
    resumo = r1.get('output_text')
    
    #cost = CustoGpt4o(c1.prompt_tokens, c1.completion_tokens)
    cost = (c1.prompt_tokens, c1.completion_tokens)
    
    if Verbose:
      print(f'=> Resumo do documento:{resumo}')
      print(f'=> Tokens para resumo:{c1.total_tokens}')
      print(f'=> Custo do resumo:{cost}')
    
    return (resumo, cost)
    
  except Exception as e:
      print(f"Erro durante chamada da API para resumo: {e}")
      return ""
    

