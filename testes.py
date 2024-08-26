from langchain_openai.chat_models import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate


#organizar outputs
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.documents import Document

#usando KOR
from kor import from_pydantic
from typing import List, Optional
from kor.extraction import create_extraction_chain  
from kor import extract_from_documents, from_pydantic, create_extraction_chain
from langchain_community.callbacks import get_openai_callback
from kor.nodes import Object, Text, Number
import asyncio

#OCRIZACAO
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Ajuste o caminho
import fitz  # PyMuPDF
from PIL import Image
import io


import pandas as pd
import xlwt
from dotenv import load_dotenv

import os

#expressoes regulares
import re

from AnalisePortaria import *
from AnaliseGeral import *


from openpyxl import Workbook

#Roda uma bateria de testes a partir dos nomes de arquivos presentes na coleção dourada
def roda_teste(models, Verbose=False, MedRobot=False):
    # Caminho para o arquivo Excel
    caminho_dourada = os.path.join(os.getcwd(), "inputs", 'Colecao_dourada_peticoes_iniciais.xlsx')
    
    df = pd.read_excel(caminho_dourada)
    lista_arquivos = df['nome do arquivo'].tolist()
    
    print(lista_arquivos)
    
    resultados = []
    
    resultado = None
    
    nome_arquivo_saida = "teste_dourada_peticoes_1.xlsx"
            

    # Loop através dos arquivos filtrados
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(['Nome do Arquivo',
                    'Tipo do documento',
                    'Resumo do documento',
                    'Possui Outros Além de Medicamentos',
                    'Condenação Honorários Sucumbenciais (acima de 1500)',
                    'Possui medicamentos',
                    'Possui internação',
                    'Deveria aplicar a Portaria',
                    'Resultado Outros',
                    'Resultado Outros Proibidos',
                    'Resultado Condenação',
                    'Resultado medicamentos',
                    'Resultado internação',
                    'Resultado Teto',
                    'Resultado aplicação portaria',
                    'VP_outros',
                    'FN_outros',
                    'FP_outros',
                    'VN_outros',
                    'VP_honorarios',
                    'FN_honorarios',
                    'FP_honorarios',
                    'VN_honorarios',
                    'VP_medicamentos',
                    'FN_medicamentos',
                    'FP_medicamentos',
                    'VN_medicamentos',
                    'VP_internacao',
                    'FN_internacao',
                    'FP_internacao',
                    'VN_internacao',
                    'VP_portaria',
                    'FN_portaria',
                    'FP_portaria',
                    'VN_portaria', 
                    'Custo',
                    'Tokens', 
                    'Lista de medicamentos', 
                    'Lista de Outros'])
    workbook.save(nome_arquivo_saida)
    for nome_arquivo in lista_arquivos:
        print(f"Iniciando análise de {nome_arquivo}...")
        linha = df[df['nome do arquivo'] == nome_arquivo].iloc[0]
        possui_outros = str(linha['Possui outros alem de medicamentos (SIM/NÃO)'])
        condenacao = str(linha['Condenação honorários sucumbenciais (acima de 1500) (SIM/NÃO)'])
        medicamentos=str(linha['Possui medicamentos (SIM/NÃO)'])
        internacao=str(linha['Possui internacao (SIM/NÃO)'])
        #MODIFICADO (Leonardo)
        portaria=str(linha['Aplica-se a portaria considerando o inciso I? (SIM/NÃO)'])
        
        possui_outros = True if possui_outros.strip().lower().startswith('sim') else False
        condenacao = True if condenacao.strip().lower().startswith('sim') else False
        medicamentos =  True if medicamentos.strip().lower().startswith('sim') else False
        internacao =  True if internacao.strip().lower().startswith('sim') else False
        #MODIFICADO (Leonardo)
        portaria = True if portaria.strip().lower().startswith('sim') else False
        
        # Supondo que as funções verifica_condenacao e verifica_outros já estão definidas
        caminho_completo = os.path.join(os.getcwd(), "uploads", nome_arquivo)
        #pdb.set_trace()
        resultado = AnalisePortaria(caminho_completo, models, TipoDocumento="Indeterminado", MedRobot=MedRobot, Verbose=Verbose)
        
        if resultado == None:
            print(f"...Erro")
            continue
        
        tipo_documento = resultado['tipo_documento']
        resultado_resumo = resultado['resumo']
            
        resultado_condenacao = resultado['condenacao_honorarios']
        resultado_internacao = resultado['internacao']
        
        
        resultado_outros = resultado['possui_outros']
        resultado_outros_proibidos = resultado['possui_outros_proibidos']
        
        resultado_medicamentos = False if not resultado['lista_medicamentos'] else True

        #MODIFICADO (Leonardo)
        resultado_teto = resultado['respeita_valor_teto']
        
        #ATENCAO: MODIFICAR PARA MODIFICAR APLICACAO DA PORTARIA
        #resultado_portaria = (resultado_medicamentos or resultado_internacao) and resultado_teto and not resultado_condenacao and not resultado_outros_proibidos
        #caso das petições
        resultado_portaria = (resultado_medicamentos or resultado_internacao) and resultado_teto and not resultado_outros_proibidos
        

        print(f"...Sucesso")
        #workbook = openpyxl.load_workbook('teste_dourada_decisoes_e_sentencas_1.xlsx')
        #sheet = workbook.active
        sheet.append([nome_arquivo,
                        tipo_documento,
                        resultado_resumo,
                        possui_outros,
                        condenacao,  
                        medicamentos, 
                        internacao,
                        portaria, 
                        resultado_outros,
                        resultado_outros_proibidos,
                        resultado_condenacao,
                        resultado_medicamentos,
                        resultado_internacao,
                        resultado_teto,
                        resultado_portaria,
                        possui_outros and resultado_outros,
                        possui_outros and not resultado_outros,
                        not possui_outros and resultado_outros,
                        not possui_outros and not resultado_outros,
                        condenacao and resultado_condenacao,
                        condenacao and not resultado_condenacao,
                        not condenacao and resultado_condenacao,
                        not condenacao and not resultado_condenacao,
                        medicamentos and resultado_medicamentos,
                        medicamentos and not resultado_medicamentos,
                        not medicamentos and resultado_medicamentos,
                        not medicamentos and not resultado_medicamentos,
                        internacao and resultado_internacao,
                        internacao and not resultado_internacao,
                        not internacao and resultado_internacao,
                        not internacao and not resultado_internacao,
                        portaria and resultado_portaria,
                        portaria and not resultado_portaria,
                        not portaria and resultado_portaria, 
                        not portaria and not resultado_portaria, 
                        resultado['custollm'],
                        str(resultado['tokensllm']), 
                        str(resultado['lista_medicamentos']),
                        str(resultado['lista_outros'])
        ]) 
        workbook.save(nome_arquivo_saida)

  
    # Converter a lista de resultados em um DataFrame e salvar em um arquivo Excel
    #resultados_df = pd.DataFrame(resultados)
    # Suponha que 'resultados_df' é o DataFrame que você quer salvar
    #resultados_df.to_excel('testes_dourada.xlsx', index=False, engine='openpyxl')



#Roda testes em módulos específicos, configurados a partir do dicionário modulos
def teste_unitario(caminho, models, modulos, Verbose=False, MedRobot=False, TipoDocumento="Sentença", Resumo=True):
    
    if Verbose:
        print("Modo verbose ativado.")    
        if MedRobot:
            print("MedRobot está ativado.")
            
    #realiza o preprocessamento das paginas do pdf
    (filtered_pages, custo) = preprocessamento(caminho, models, Verbose, TipoDocumento, Resumo=Resumo)
    
    try:
        if Verbose:    
            print(f"Número de páginas após pré-processamento: {len(filtered_pages)}\n")
            #for page in filtered_pages:
            #    print(f"Página {page.metadata['page']}")
            #    print(f"Página {page.page_content}")

        
        #print("Que foi doido1")
        
        # cria ids para as páginas, o que vai ser útil para gerenciar o banco de dados de vetores
        ids = [str(i) for i in range(1, len(filtered_pages) + 1)]


        #print("Que foi doido2")
        
        #utiliza embeddings da OpenAI para o banco de vetores Chroma
        embeddings = OpenAIEmbeddings()
        docsearch = Chroma.from_documents(filtered_pages, embeddings, ids=ids, collection_metadata={"hnsw:M": 1024}) #essa opção "hnsw:M": 1024 é importante para não ter problemas

        #print("Que foi doido3")
        
        if modulos['geral']:
            #analisa se existe condenação por honorários na sentença
            (resposta, cgeral) = AnaliseGeral(docsearch, model=models['geral'], Verbose=Verbose, Resumo=Resumo)
                     
            #print(f"Usando {models['honorarios']} detecção de cond. honorários:{honor}")
        
            #if Verbose:
            #print(f"Resultado Detecção de outros: {outrosllm}")
            #print(f"Custo Detecção de honorários usando {models['honorarios']}: {chonor}")


        #Testa o modulo de detecção de extração de outros itens na sentença
        if modulos['outros']:            
            outrosregex = False
            outrosllm = False
            doutrosllm = False
            listaoutrosllm = []
            coutros=0
            cdoutros=0
            (outrosregex_permitidos, listaoutrosregex_permitidos, outrosregex_proibidos, listaoutrosregex_proibidos) = AnaliseOutrosRegex(filtered_pages, Verbose)
            
            #verifica se existe algum item de outros
            outrosregex = outrosregex_permitidos or outrosregex_proibidos
            listaoutrosregex = listaoutrosregex_permitidos + listaoutrosregex_proibidos
            
            if Verbose:
                print(f"Regex detectou outros:{outrosregex}")
                print(f"Regex lista outros:{listaoutrosregex}")
            
            
            #detecta (usando LLM) se existem outros itens além de medicamentos na sentença
            (doutrosllm, cdoutros) = DetectaOutrosLLM(docsearch, model=models['doutros'], Verbose=Verbose)
            
            #(outrosllm, listaoutrosllm, coutros) = AnaliseOutrosLLM(docsearch, model=models['outros'], Verbose=Verbose)
        
            routros = False
            if doutrosllm:
                if outrosregex:
                    routros = True    
            
            
            print(f"LLM1 (apenas detecção) detectou outros:{doutrosllm}")
            print(f"LLM2 detectou outros:{outrosllm}")
            print(f"LLM2 extraiu outros:{listaoutrosllm}")
        
            print(f"Resultado OUTROS1 com AND:{doutrosllm and outrosregex}")
            print(f"Resultado OUTROS1 com OR:{doutrosllm or outrosregex}")
            print(f"Resultado OUTROS2 com AND:{outrosllm and outrosregex}")
            print(f"Resultado OUTROS2 com OR:{outrosllm or outrosregex}")
            print(f"Resultado OUTROSX :{routros}")
                
            #if Verbose:
            #print(f"Resultado Detecção de outros: {outrosllm}")
            print(f"Custo Detecção de outros LLM1: {cdoutros}")
            print(f"Custo Detecção de outros LLM2: {cdoutros}")
                
            if Verbose:
                print(f"Custo com LLMs para detecção de outros itens: {"$ {:.4f}".format(cdoutros+coutros)}")
            #apaga as entradas criadas no Chroma
        
        
        if modulos['alimentares']:
            #detecta (usando LLM) se existem outros itens além de medicamentos na sentença
            (alim, calim) = AnaliseAlimentares(docsearch, model=models['alimentares'], Verbose=Verbose)
            
            print(f"Usando {models['alimentares']} detecção de itens alimentares:{alim}")
        
            print(f"Custo Detecção de itens alimentares usando {models['alimentares']}: {calim}")
            
            
        if modulos['internação']:
            #detecta (usando LLM) se existem outros itens além de medicamentos na sentença
            (alim, calim) = AnaliseAlimentares(docsearch, model=models['alimentares'], Verbose=Verbose)
            
            print(f"Usando {models['alimentares']} detecção de itens alimentares:{alim}")
        
            print(f"Custo Detecção de itens alimentares usando {models['alimentares']}: {calim}")
            
            
        #Testa o modulo de detecção de extração de outros itens na sentença
        if modulos['honorarios']:            
            
            #analisa se existe condenação por honorários na sentença
            (honor, chonor) = AnaliseHonorarios(docsearch, model=models['honorarios'], Verbose=Verbose, Resumo=Resumo)
            
            
            print(f"Usando {models['honorarios']} detecção de cond. honorários:{honor}")
        
            #if Verbose:
            #print(f"Resultado Detecção de outros: {outrosllm}")
            print(f"Custo Detecção de honorários usando {models['honorarios']}: {chonor}")
                
    
        #apaga as entradas criadas no Chroma        
        docsearch._collection.delete(ids=ids)
    
    except IndexError:
        print(f"Erro: Você tentou acessar um índice inválido ao analisar o arquivo {caminho.split()[-1]}.")
        return None
        
    except Exception as e:
        print(f"Erro ao processar o arquivo {caminho.split()[-1]}: {e}")
        return None
          
models = {
    #"honorarios" : "gpt-3.5-turbo-16k", 
    "honorarios" : "gpt-4o",
    #"outros" : "gpt-4o", 
    #"outros" : "gpt-3.5-turbo", 
    "doutros" : "gpt-4o",
    #"doutros" : "gpt-3.5-turbo-16k", 
    #"doutros" : "gpt-4o",
    "medicamentos" : "gpt-4o",
    #"medicamentos" : "gpt-3.5-turbo",
    "alimentares" : "gpt-4o",
    #"alimentares" : "gpt-3.5-turbo-16k",
    #"internacao" : "gpt-3.5-turbo-16k",   
    "internacao" : "gpt-4o",      
    #"resumo" : "gpt-4o",
    "resumo" : "gpt-4o",
    "geral" : "gpt-4o"
}


"""
models = {
    "honorarios" : "gpt-3.5-turbo", 
    "outros" : "gpt-3.5-turbo", 
    "doutros" : "gpt-3.5-turbo",
    "medicamentos" : "gpt-3.5-turbo",
}
"""

modulos = {
    "medicamentos" : False,
    "alimentares" : False,
    "outros" : False, 
    "honorarios" : False, 
    "precos" : False,
    "geral" : True
}

caminho_completo = os.path.join(os.getcwd(), "uploads", "peticao_NA_27.pdf")

#roda_teste(models=models, Verbose=False, MedRobot=True)

#caminho_completo = os.path.join(os.getcwd(), "uploads", "decisao_I_4.pdf")

#caminho_completo = r'H:\Meu Drive\Trabalhos\2023\projetos\UNIFOR\prosaude\robo_portaria_v6\uploads\sentenca_I_9.pdf'


AnalisePortaria(caminho_completo, models, TipoDocumento="Indeterminado", Verbose=True, MedRobot=True, Resumo=True)


#teste_unitario(caminho_completo, modulos=modulos, models=models, Verbose=True, MedRobot=False, TipoDocumento="Decisão Interlocutória", Resumo=True)

"""
caminho_completo = os.path.join(os.getcwd(), "uploads", "sentenca_II_1.pdf")
print("É pra ser True - sentenca_II_1.pdf\n")
AnalisePortaria(caminho_completo, Verbose=True)
print("\n")


"""


'''
Art. 1º. Ficam os Procuradores, em exercício na Procuradoria da Administração
Indireta e Políticas Públicas, autorizados a não apresentar recursos e
contrarrazões, nas demandas de saúde face a decisões que determinem:

I - fornecimento de medicamento, desde que registrados na ANVISA- Agência Nacional de Vigilância Sanitária;

II - realização de consultas, exames, procedimentos clínicos e cirúrgicos 
(inclusive com fornecimento de órteses e próteses) ou internação em leito especializado, 
unidade de cuidados especiais (UCE) ou UTI, 
desde que tenha sido facultado o seu cumprimento no âmbito da rede pública;

III - fornecimento de compostos alimentares de comercialização autorizada no país;

IV - fornecimento de insulinas e insumos para aplicação e monitoramento do índice glicêmico;

V - fornecimento de insumos de atenção básica, como fraldas, cadeira de rodas, cama hospitalar e outros.

VI - tratamento multidisciplinar disponibilizado pelo SUS, entre eles, sessões de fisioterapia e fonoaudiologia; 
fornecimento de oxigênio domiciliar, embolização e oxigenoterapia hiperbárica;

'''

'''
Art. 2º. Fica dispensada, além da interposição de recursos, a oferta de defesa,
nas hipóteses definidas no artigo, desde que:

I - os pleitos estejam amparados em laudo, relatório ou prescrição médica
oriundos da rede pública ou, na hipótese de documento da rede privada, o
medicamento, produto, insumo ou tratamento sejam ofertados regularmente no
SUS; e

II - não haja requerimento de indenização por danos morais e/ou materiais.
'''