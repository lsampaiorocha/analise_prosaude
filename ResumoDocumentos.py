from langchain_openai import ChatOpenAI
import openai

from langchain_community.callbacks import get_openai_callback

from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate

#from AnalisePortaria import CustoGpt4o


def CustoGpt4o(prompt_tokens, completion_tokens):
    # Custos durante o horário de pico
    custo_input = 5.00 / 1_000_000
    custo_output = 15.00 / 1_000_000
    
    # Calculando o custo
    custo_pico = (prompt_tokens * custo_input) + (completion_tokens * custo_output)
    
    return custo_pico


def GeraResumo(pages, model, api_key, Verbose=False):
  openai.api_key = api_key
    
  try:
    
    prompt_template = """Você é um assessor jurídico e precisa resumir o conteúdo de um documento solicitando ou obrigando a fornecer itens e/ou serviços da área médica. 
    O resumo deve ser escrito em português do Brasil e deve conter as seguintes informações:
    - Valor da Causa
    - Lista completa dos itens a serem fornecidos, com suas especificações tais como nomes completos e quantidades
    - Se houverem medicamentos, os nomes, dosagem, quantidade e duração do tratamento
    - Se contém solicitação ou obrigação de internação ou transferência para Unidade de Terapia Intensiva (UTI) ou Unidade de Cuidados Especiais (UCE)
    - Se é solicitada indenização por danos morais
    - Se há condenação por danos morais
    - Se há condenação por honorários e em que valor
    - Se há condenação por multa ou bloqueio de recursos e em que valor
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
    
    cost = CustoGpt4o(c1.prompt_tokens, c1.completion_tokens)
    
    if Verbose:
      print(f'=> Resumo do documento:{resumo}')
      print(f'=> Tokens para resumo:{c1.total_tokens}')
      print(f'=> Custo do resumo:{cost}')
    
    return (resumo, cost)
    
  except Exception as e:
      print(f"Erro durante chamada da API para resumo: {e}")
      return ""


