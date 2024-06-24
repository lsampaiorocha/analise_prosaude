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
def roda_teste(Verbose=False, MedRobot=False, Seleciona=False, ArqSeleciona=None):
    # Caminho para o arquivo Excel
    caminho_dourada = os.path.join(os.getcwd(), "inputs", 'Colecao_dourada_2.xlsx')
    
    df = pd.read_excel(caminho_dourada)
    lista_arquivos = df['nome do arquivo'].tolist()
    
    print(lista_arquivos)
    
    resultados = []
    
    resultado = None
            

    if not Seleciona:
        # Loop através dos arquivos filtrados
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(['Nome do Arquivo','Possui Outros Além de Medicamentos','Condenação Honorários Sucumbenciais (acima de 1500)','Resultado Outros','Resultado Condenação','VP_outros','FN_outros','FP_outros','VN_outros','VP_honorarios'
                      ,'FN_honorarios',	'FP_honorarios','VN_honorarios','VP_medicamentos','FN_medicamentos'
                      ,'FP_medicamentos','VN_medicamentos','VP_portaria','FN_portaria',
                      'FP_portaria','VN_portaria'])
        workbook.save('teste_dourada_2.xlsx')
        for nome_arquivo in lista_arquivos:
            print(f"Iniciando análise de {nome_arquivo}...")
            linha = df[df['nome do arquivo'] == nome_arquivo].iloc[0]
            possui_outros = str(linha['Possui outros alem de medicamentos (SIM/NÃO)'])
            condenacao = str(linha['Condenação honorários sucumbenciais (acima de 1500) (SIM/NÃO)'])
            medicamentos=str(linha['Possui medicamentos (SIM/NÃO)'])
            #MODIFICADO (Leonardo)
            portaria=str(linha['Aplica-se a portaria considerando o inciso I? (SIM/NÃO)'])
            
            possui_outros = True if possui_outros.strip().lower().startswith('sim') else False
            condenacao = True if condenacao.strip().lower().startswith('sim') else False
            medicamentos =  True if medicamentos.strip().lower().startswith('sim') else False
            #MODIFICADO (Leonardo)
            portaria = True if portaria.strip().lower().startswith('sim') else False
            
            # Supondo que as funções verifica_condenacao e verifica_outros já estão definidas
            caminho_completo = os.path.join(os.getcwd(), "uploads", nome_arquivo)
            #pdb.set_trace()
            resultado = AnalisePortaria(caminho_completo, MedRobot=MedRobot, Verbose=Verbose)
            #resultado = AnalisePortaria(caminho_completo, Robot, Verbose)
            if resultado == None:
                print(f"...Erro")
                continue
                
            resultado_condenacao = resultado['condenacao_honorarios']
            
            resultado_outros = resultado['possui_outros']
            
            resultado_medicamentos = False if not resultado['lista_medicamentos'] else True

            #resultado_portaria = resultado_medicamentos and not resultado_condenacao and not resultado_outros
            #MODIFICADO (Leonardo)
            resultado_teto = resultado['respeita_valor_teto']
            resultado_portaria = resultado_medicamentos and resultado_teto and not resultado_condenacao and not resultado_outros
            
            resultados.append({
                'Nome do Arquivo': nome_arquivo,
                'Possui Outros Além de Medicamentos': possui_outros,
                'Condenação Honorários Sucumbenciais (acima de 1500)': condenacao,
                'Resultado Outros': resultado_outros,
                'Resultado Condenação': resultado_condenacao,
                'VP_outros': possui_outros and resultado_outros,  # Verdadeiro Positivo: ambos True
                'FN_outros': possui_outros and not resultado_outros,  # Falso Negativo: possui_outros True, resultado_outros False
                'FP_outros': not possui_outros and resultado_outros,  # Falso Positivo: possui_outros False, resultado_outros True
                'VN_outros': not possui_outros and not resultado_outros,  # Verdadeiro Negativo: ambos False
                'VP_honorarios': condenacao and resultado_condenacao,  # Verdadeiro Positivo: ambos True
                'FN_honorarios': condenacao and not resultado_condenacao,  # Falso Negativo: possui_outros True, resultado_outros False
                'FP_honorarios': not condenacao and resultado_condenacao,  # Falso Positivo: possui_outros False, resultado_outros True
                'VN_honorarios': not condenacao and not resultado_condenacao,  # Verdadeiro Negativo: ambos False
                'VP_medicamentos': medicamentos and resultado_medicamentos,  # Verdadeiro Positivo: ambos True
                'FN_medicamentos': medicamentos and not resultado_medicamentos,  # Falso Negativo: possui_outros True, resultado_outros False
                'FP_medicamentos': not medicamentos and resultado_medicamentos,  # Falso Positivo: possui_outros False, resultado_outros True
                'VN_medicamentos': not medicamentos and not resultado_medicamentos,  # Verdadeiro Negativo: ambos False
                'VP_portaria': portaria and resultado_portaria,  # Verdadeiro Positivo: ambos True
                'FN_portaria': portaria and not resultado_portaria,  # Falso Negativo: possui_outros True, resultado_outros False
                'FP_portaria': not portaria and resultado_portaria,  # Falso Positivo: possui_outros False, resultado_outros True
                'VN_portaria': not portaria and not resultado_portaria  # Verdadeiro Negativo: ambos False

            
            })

            print(f"...Sucesso")
            workbook = openpyxl.load_workbook('teste_dourada_2.xlsx')
            sheet = workbook.active
            sheet.append([nome_arquivo,possui_outros, condenacao,resultado_outros,resultado_condenacao,
                          possui_outros and resultado_outros,possui_outros and not resultado_outros,
                          not possui_outros and resultado_outros,not possui_outros and not resultado_outros,
                          condenacao and resultado_condenacao,condenacao and not resultado_condenacao,
                          not condenacao and resultado_condenacao,not condenacao and not resultado_condenacao,
                          medicamentos and resultado_medicamentos,medicamentos and not resultado_medicamentos,
                          not medicamentos and resultado_medicamentos,not medicamentos and not resultado_medicamentos,
                          portaria and resultado_portaria,portaria and not resultado_portaria,
                          not portaria and resultado_portaria, not portaria and not resultado_portaria])
            workbook.save('teste_dourada_2.xlsx')
    else:
        nome_arquivo = ArqSeleciona
        print(f"Iniciando análise de {nome_arquivo}...")
        linha = df[df['nome do arquivo'] == nome_arquivo].iloc[0]
        possui_outros = str(linha['Possui outros alem de medicamentos'])
        condenacao = str(linha['Condenação honorários sucumbenciais (acima de 1500)'])
        
        possui_outros = True if possui_outros.strip().lower().startswith('sim') else False
        condenacao = True if condenacao.strip().lower().startswith('sim') else False

        # Supondo que as funções verifica_condenacao e verifica_outros já estão definidas
        caminho_completo = os.path.join(os.getcwd(), "uploads", nome_arquivo)
        #pdb.set_trace()
        resultado = AnalisePortaria(caminho_completo, Robot, Verbose)
        if resultado == None:
            print(f"...Erro")
            
        resultado_condenacao = resultado['condenacao_honorarios']
        
        resultado_outros = resultado['possui_outros']

        resultados.append({
            'Nome do Arquivo': nome_arquivo,
            'Possui Outros Além de Medicamentos': possui_outros,
            'Condenação Honorários Sucumbenciais (acima de 1500)': condenacao,
            'Resultado Outros': resultado_outros,
            'Resultado Condenação': resultado_condenacao,
            'VP_outros': possui_outros and resultado_outros,  # Verdadeiro Positivo: ambos True
            'FN_outros': possui_outros and not resultado_outros,  # Falso Negativo: possui_outros True, resultado_outros False
            'FP_outros': not possui_outros and resultado_outros,  # Falso Positivo: possui_outros False, resultado_outros True
            'VN_outros': not possui_outros and not resultado_outros,  # Verdadeiro Negativo: ambos False
            'VP_honorarios': condenacao and resultado_condenacao,  # Verdadeiro Positivo: ambos True
            'FN_honorarios': condenacao and not resultado_condenacao,  # Falso Negativo: possui_outros True, resultado_outros False
            'FP_honorarios': not condenacao and resultado_condenacao,  # Falso Positivo: possui_outros False, resultado_outros True
            'VN_honorarios': not condenacao and not resultado_condenacao  # Verdadeiro Negativo: ambos False
        })
    
        print(f"...Sucesso")
     
    if not Seleciona:    
        # Converter a lista de resultados em um DataFrame e salvar em um arquivo Excel
        resultados_df = pd.DataFrame(resultados)
        # Suponha que 'resultados_df' é o DataFrame que você quer salvar
        resultados_df.to_excel('testes_dourada.xlsx', index=False, engine='openpyxl')


#caminho_completo = os.path.join(os.getcwd(), "uploads", "sentenca_II_8.pdf")
#roda_teste(Seleciona=False, Verbose=False, MedRobot=True)

caminho_completo = os.path.join(os.getcwd(), "uploads", "sentenca_I_9.pdf")

#caminho_completo = r'H:\Meu Drive\Trabalhos\2023\projetos\UNIFOR\prosaude\robo_portaria_v6\uploads\sentenca_I_9.pdf'

models = {
    "honorarios" : "gpt-3.5-turbo", 
    "outros" : None, 
    "medicamentos" : "gpt-3.5-turbo"
}
AnalisePortaria(caminho_completo, models, Verbose=True, MedRobot=False)


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