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
import itertools

#expressoes regulares
import re

from AnalisePortaria import *


import pdb

from openpyxl import Workbook

#Roda uma bateria de testes a partir dos nomes de arquivos presentes na coleção dourada
def roda_teste_outros(models, Verbose=False, MedRobot=False, Mode="Sentença"):
    # Caminho para o arquivo Excel
    caminho_dourada = os.path.join(os.getcwd(), "inputs", 'Colecao_dourada_decisoes.xlsx')
    
    df = pd.read_excel(caminho_dourada)
    lista_arquivos = df['nome do arquivo'].tolist()
    
    print(lista_arquivos)
    
    resultados = []
                
    # Loop através dos arquivos filtrados
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(['Nome do Arquivo','Possui Outros Além de Medicamentos','Resultado Outros',
                    'VP_outros','FN_outros','FP_outros','VN_outros', 
                    'Custo', 'Lista de Outros'])
    workbook.save('teste_dourada_decisoes_outros_gpt4o.xlsx')
    for nome_arquivo in lista_arquivos:
        print(f"Iniciando análise de {nome_arquivo}...")
        linha = df[df['nome do arquivo'] == nome_arquivo].iloc[0]
        possui_outros = str(linha['Possui outros alem de medicamentos (SIM/NÃO)'])
        
        possui_outros = True if possui_outros.strip().lower().startswith('sim') else False
        
        caminho = os.path.join(os.getcwd(), "uploads", nome_arquivo)
        
        #realiza o preprocessamento das paginas do pdf
        filtered_pages = preprocessamento(caminho, Verbose=Verbose, Mode=Mode)

        try:
            if Verbose:    
                print(f"Número de páginas após pré-processamento: {len(filtered_pages)}\n")
                for page in filtered_pages:
                    print(f"Página {page.metadata['page']}")
                    print(f"Página {page.page_content}")

            # cria ids para as páginas, o que vai ser útil para gerenciar o banco de dados de vetores
            ids = [str(i) for i in range(1, len(filtered_pages) + 1)]

            #utiliza embeddings da OpenAI para o banco de vetores Chroma
            embeddings = OpenAIEmbeddings()
            docsearch = Chroma.from_documents(filtered_pages, embeddings, ids=ids, collection_metadata={"hnsw:M": 1024}) #essa opção "hnsw:M": 1024 é importante para não ter problemas


            outrosregex = False
            doutrosllm = False
            cdoutros=0

            #(outrosregex, listaoutrosregex) = AnaliseOutrosRegex(filtered_pages, Verbose)
            
            (outrosregex_permitidos, listaoutrosregex_permitidos, outrosregex_proibidos, listaoutrosregex_proibidos) = AnaliseOutrosRegex(filtered_pages, Verbose)
    
            
            outrosregex = outrosregex_permitidos or outrosregex_proibidos
            listaoutrosregex = listaoutrosregex_permitidos + listaoutrosregex_proibidos
            
            
            if Verbose:
                print(f"Regex detectou outros:{outrosregex}")
                print(f"Regex lista outros:{listaoutrosregex}")
            
            
            #detecta (usando LLM) se existem outros itens além de medicamentos na sentença
            (doutrosllm, cdoutros) = DetectaOutrosLLM(docsearch, model=models['doutros'], Verbose=Verbose)
            
            #(outrosllm, listaoutrosllm, coutros) = AnaliseOutrosLLM(docsearch, model=models['outros'], Verbose=Verbose)
        
            outros=False
            if doutrosllm:
                if outrosregex:
                    outros = True   
        
            resultado_outros = outros

        
            resultados.append({
                'Nome do Arquivo': nome_arquivo,
                'Possui Outros Além de Medicamentos': possui_outros,
                'Resultado Outros': resultado_outros,
                'VP_outros': possui_outros and resultado_outros,  # Verdadeiro Positivo: ambos True
                'FN_outros': possui_outros and not resultado_outros,  # Falso Negativo: possui_outros True, resultado_outros False
                'FP_outros': not possui_outros and resultado_outros,  # Falso Positivo: possui_outros False, resultado_outros True
                'VN_outros': not possui_outros and not resultado_outros,  # Verdadeiro Negativo: ambos False
                'Custo': cdoutros,
                'Lista de outros': str(listaoutrosregex)
            })

            print(f"...Sucesso")
            workbook = openpyxl.load_workbook('teste_dourada_decisoes_outros_gpt4o.xlsx')
            sheet = workbook.active
            sheet.append([nome_arquivo, 
                        possui_outros, 
                        resultado_outros,
                        possui_outros and resultado_outros,
                        possui_outros and not resultado_outros,
                        not possui_outros and resultado_outros,
                        not possui_outros and not resultado_outros,
                        cdoutros, 
                        str(listaoutrosregex)])
            workbook.save('teste_dourada_decisoes_outros_gpt4o.xlsx')

            # Converter a lista de resultados em um DataFrame e salvar em um arquivo Excel
            resultados_df = pd.DataFrame(resultados)
            # Suponha que 'resultados_df' é o DataFrame que você quer salvar
            resultados_df.to_excel('teste_dourada_decisoes_outros_gpt4o.xlsx', index=False, engine='openpyxl')
            
        except IndexError:
            print(f"Erro: Você tentou acessar um índice inválido ao analisar o arquivo {caminho.split()[-1]}.")
            return None
            
        except Exception as e:
            print(f"Erro ao processar o arquivo {caminho.split()[-1]}: {e}")
            return None
        

models = {
    "honorarios" : "gpt-3.5-turbo", 
    "outros" : "gpt-3.5-turbo", 
    "doutros" : "gpt-4o", 
    "medicamentos" : "gpt-3.5-turbo"
}

#caminho_completo = os.path.join(os.getcwd(), "uploads", "sentenca_II_8.pdf")
roda_teste_outros(models=models, Verbose=True, Mode="Decisão")

