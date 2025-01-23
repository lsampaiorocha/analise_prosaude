from langchain_openai import ChatOpenAI
import openai

from langchain_community.callbacks import get_openai_callback

from langchain.chains.combine_documents.stuff import StuffDocumentsChain
#from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate

from langchain.schema.runnable import RunnableSequence

#from AnalisePortaria import CustoGpt4o



def GeraResumoOld(pages, model, api_key, Verbose=False):
  openai.api_key = api_key
    
  try:
    
    prompt_template = """
        Você é um assessor jurídico e precisa resumir o conteúdo de um documento solicitando ou obrigando a fornecer itens e/ou serviços da área médica.
        
        Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
        Outros itens médicos ou de assistência, como fraldas, compostos alimentares, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos.
        Em hipótese alguma forneça na lista medicamentos que não estavam na decisão. Se não houverem medicamentos, apenas responda que não há medicamentos.
        
        Considere como internação ou transferência para leito hospitalar como qualquer tipo de internação ou tranferência para unidades especializadas de saúde. Isto deve incluir UTIs (Unidades de Terapia Intensiva), UCEs (Unidades de Cuidados Especiais) e unidades de internação psiquiátrica ou para tratamento de drogas, dentre outras.
        
        Considere que consultas são Avaliações médicas realizadas por profissionais de saúde para diagnóstico, acompanhamento ou tratamento de condições de saúde.
        
        Considere que exames são Procedimentos de investigação médica, como laboratoriais ou de imagem, para auxiliar no diagnóstico de doenças ou monitoramento do paciente.

        Considere que procedimentos clínicos ou cirúrgicos são intervenções terapêuticas ou diagnósticas, que podem ser mínimas (como curativos ou remoção de pontos) ou invasivas (como cirurgias), visando tratar ou melhorar a condição do paciente.
        
        Considere que compostos Nutricionais e/ou Dietas Especiais são Suplementos ou regimes alimentares específicos recomendados para atender às necessidades nutricionais de pacientes com condições de saúde particulares, como alergias, intolerâncias, deficiências nutricionais ou doenças crônicas, visando promover ou restaurar a saúde. Eles não devem ser confundidos com medicamentos.
        
        decisão de cumprimento de sentença:
        
        O resumo deve ser escrito em português do Brasil e deve conter as seguintes informações e estrutura:

        **Resumo do Documento**

        - **Tipo de Documento:** Indique se é uma Sentença, Decisão Interlocutória ou Petição Inicial
        - **Valor da Causa:** Informe o valor da causa
        - **Itens a serem fornecidos:**
          - **Medicamentos:**
            - Liste os medicamentos, cada um com suas dosagens, quantidades e duração do tratamento
          - **Compostos nutricionais:**
            - Liste os compostos nutricionais com suas dosagens, quantidades e duração do tratamento
          - **Internação ou transferência para leito hospitalar:**
            - Liste as internações ou transferências para leito hospitalar 
          - **Consultas, exames ou procedimentos:**
            - Liste as consultas, exames ou procedimentos 
          - **Outros Itens ou Serviços:**
            - Liste os outros itens ou serviços necessários que não se enquadrem nas categorias anteriores
        - **Há Internação ou Transferência para leito hospitalar:** 'Sim' ou 'Não', se há solicitação ou obrigação de internação para leito hospitalar.
        - **Há Consultas, exames e/ou procedimentos:** 'Sim' ou 'Não', se há solicitação ou obrigação de realização de consultas e exames, bem como de procedimentos clínicos e/ou cirúrgicos.
        - **Há Danos Morais:** 'Sim' ou 'Não', se há solicitação ou condenação por danos morais.
        - **Há Honorários:** Detalhe se há condenação por honorários, especificando quem foi condenado e o valor.
        - **Há Pedido de Liminar ou Antecipação de Tutela:** 'Sim' ou 'Não', se há pedido de liminar ou antecipação de tutela.
        - **Há Deferimento ou Indeferimento do pedido liminar ou antecipação de tutela:** Informe se foi deferido, indeferido ou não se aplica.

        - **Houve a extinção do processo:** 'Sim' ou 'Não', se o processo foi explicitamente declarado extinto no documento.
        - **Trata-se de uma decisão de cumprimento de sentença:** 'Sim' ou 'Não', se trata-se de uma decisão de cumprimento de sentença, na qual o juiz cobra que sejam executadas as obrigações impostas em uma sentença anterior.
        - **Trata-se de uma decisão de bloqueio de recursos ou contas:** 'Sim' ou 'Não', se trata-se de uma decisão de bloqueio de recursos ou contas. Caso o bloqueio seja mencionado como uma possibilidade, mas a decisão ainda não o determine, a resposta é 'Não'.
        - **Trata-se de um documento intitulado decisão monocrática:** 'Sim' ou 'Não', se o documento está denominado como uma decisão monocrática.

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
    #llm_chain = RunnableSequence([prompt, llm])
    
    # Define StuffDocumentsChain
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
    #stuff_chain = create_stuff_documents_chain(
    #  llm_chain=llm_chain,
    #  document_variable_name="text"
    #)
    
    with get_openai_callback() as c1:
        #r1 = stuff_chain.invoke({"input_documents": pages})
        r1 = stuff_chain.invoke(pages)
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
      return ("", (0, 0))  # Resumo vazio e tokens zerados
    
    

def GeraResumo(pages, model, api_key, Verbose=False):
  openai.api_key = api_key
    
  try:
    
    prompt_template = """
        Você é um assessor jurídico e precisa resumir o conteúdo de um documento solicitando ou obrigando a fornecer itens e/ou serviços da área médica.
        
        Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
        Outros itens médicos ou de assistência, como fraldas, compostos alimentares, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos.
        Em hipótese alguma forneça na lista medicamentos que não estavam na decisão. Se não houverem medicamentos, apenas responda que não há medicamentos.
        
        Considere como internação ou transferência para leito hospitalar como qualquer tipo de internação ou tranferência para unidades especializadas de saúde. Isto deve incluir UTIs (Unidades de Terapia Intensiva), UCEs (Unidades de Cuidados Especiais) e unidades de internação psiquiátrica ou para tratamento de drogas, dentre outras.
        
        Considere que consultas são Avaliações médicas realizadas por profissionais de saúde para diagnóstico, acompanhamento ou tratamento de condições de saúde.
        
        Considere que exames são Procedimentos de investigação médica, como laboratoriais ou de imagem, para auxiliar no diagnóstico de doenças ou monitoramento do paciente.

        Considere que procedimentos clínicos ou cirúrgicos são intervenções terapêuticas ou diagnósticas, que podem ser mínimas (como curativos ou remoção de pontos) ou invasivas (como cirurgias), visando tratar ou melhorar a condição do paciente.
        
        Considere que compostos Nutricionais e/ou Dietas Especiais são Suplementos ou regimes alimentares específicos recomendados para atender às necessidades nutricionais de pacientes com condições de saúde particulares, como alergias, intolerâncias, deficiências nutricionais ou doenças crônicas, visando promover ou restaurar a saúde. Eles não devem ser confundidos com medicamentos.
        
        decisão de cumprimento de sentença:
        
        O resumo deve ser escrito em português do Brasil e deve conter as seguintes informações e estrutura:

        **Resumo do Documento**

        - **Tipo de Documento:** Indique se é uma Sentença, Decisão Interlocutória ou Petição Inicial
        - **Valor da Causa:** Informe o valor da causa
        - **Itens a serem fornecidos:**
          - **Medicamentos:**
            - Liste os medicamentos, cada um com suas dosagens, quantidades e duração do tratamento
          - **Compostos nutricionais:**
            - Liste os compostos nutricionais com suas dosagens, quantidades e duração do tratamento
          - **Internação ou transferência para leito hospitalar:**
            - Liste as internações ou transferências para leito hospitalar 
          - **Consultas, exames ou procedimentos:**
            - Liste as consultas, exames ou procedimentos 
          - **Outros Itens ou Serviços:**
            - Liste os outros itens ou serviços necessários que não se enquadrem nas categorias anteriores
        - **Há Internação ou Transferência para leito hospitalar:** 'Sim' ou 'Não', se há solicitação ou obrigação de internação para leito hospitalar.
        - **Há Consultas, exames e/ou procedimentos:** 'Sim' ou 'Não', se há solicitação ou obrigação de realização de consultas e exames, bem como de procedimentos clínicos e/ou cirúrgicos.
        - **Há Danos Morais:** 'Sim' ou 'Não', se há solicitação ou condenação por danos morais.
        - **Há Honorários:** Detalhe se há condenação por honorários, especificando quem foi condenado e o valor.
        - **Há Pedido de Liminar ou Antecipação de Tutela:** 'Sim' ou 'Não', se há pedido de liminar ou antecipação de tutela.
        - **Há Deferimento ou Indeferimento do pedido liminar ou antecipação de tutela:** Informe se foi deferido, indeferido ou não se aplica.

        - **Houve a extinção do processo:** 'Sim' ou 'Não', se o processo foi explicitamente declarado extinto no documento.
        - **Trata-se de uma decisão de cumprimento de sentença:** 'Sim' ou 'Não', se trata-se de uma decisão de cumprimento de sentença, na qual o juiz cobra que sejam executadas as obrigações impostas em uma sentença anterior.
        - **Trata-se de uma decisão de bloqueio de recursos ou contas:** 'Sim' ou 'Não', se trata-se de uma decisão de bloqueio de recursos ou contas. Caso o bloqueio seja mencionado como uma possibilidade, mas a decisão ainda não o determine, a resposta é 'Não'.
        - **Trata-se de um documento intitulado decisão monocrática:** 'Sim' ou 'Não', se o documento está denominado como uma decisão monocrática.

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
    #llm_chain = RunnableSequence([prompt, llm])
    
    # Define StuffDocumentsChain
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
    #stuff_chain = create_stuff_documents_chain(
    #  llm_chain=llm_chain,
    #  document_variable_name="text"
    #)
    
    with get_openai_callback() as c1:
        #r1 = stuff_chain.invoke({"input_documents": pages})
        r1 = stuff_chain.invoke(pages)
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
      return ("", (0, 0))  # Resumo vazio e tokens zerados
    

