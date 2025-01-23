from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from ModulosAnalise.ResumoDocumentos import *

from dotenv import load_dotenv

#expressoes regulares
import re
import os

#OCRIZACAO
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Ajuste o caminho
import fitz  # PyMuPDF
from PIL import Image




# Carrega o pdf, inclusive caso seja non-searchable
# Caso Resumo esteja desabilitado, pré-processa para eliminar páginas desnecessárias para análise
# Caso Resumo esteja habilitado, aplica LLM para resumir as principais informações necessárias
def preprocessamento(caminho, models, Verbose=False, TipoDocumento="Indeterminado", Resumo=True):
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não está definida")
    
    #verifica se o pdf no caminho é searchable, e caso não seja, roda o ocr
    if Searchable(caminho):
        #Carrega o pdf dado pelo caminho
        loader = PyPDFLoader(caminho)
        pages = loader.load_and_split()
    else:
        pages = ExtraiOCR(caminho)
    
    if Verbose:    
        print(f"Número de páginas lidas do arquivo: {len(pages)}")
        
    #irá armazenar o custo com LLMs
    custo = 0
        
    if Resumo or TipoDocumento == "Indeterminado":
        #print(f'Valor de models: {models}')
        
        (resumo, custo) = GeraResumo(pages, models['resumo'], api_key, Verbose=Verbose)
        
        
        filtered_pages = []
        filtered_pages.append(Document(page_content=resumo, metadata={"page": 0, "source": caminho}))
        
        with open("resumo.txt", "w") as arquivo:
            arquivo.write(resumo)
        
        tipo_documento = ExtraiTipoDocumento(resumo)
        
        print(f"Tipo do documento {tipo_documento}")
       
        
    elif TipoDocumento == "Sentença":
        # Lista de palavras-chave que deseja filtrar - estas palavras tem sido usadas para detectar a página que contém a sentença
        palavras_filtro = ['julgo', 'julgar procedente', 'julgando procedente', 'condeno']

        # Construindo a expressão regular para filtrar apenas as páginas que contém a sentença
        # Usamos \b para garantir que estamos capturando palavras inteiras
        filtro_regex = re.compile(r'\b' + r'\b|\b'.join([re.escape(keyword) for keyword in palavras_filtro]) + r'\b', re.IGNORECASE)
        #filtro_regex = re.compile(r'(^|\b)' + r'(^|\b)|(^|\b)'.join([re.escape(keyword) for keyword in palavras_filtro]) + r'(^|\b)', re.IGNORECASE)
        
        # Filtrando páginas com base nas palavras-chave
        filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
        
        
        
        if Verbose:
            # Identificando as palavras-chave encontradas em cada página filtrada
            palavras_encontradas_por_pagina = []
            for page in filtered_pages:
                palavras_encontradas = [keyword for keyword in palavras_filtro if re.search(r'\b' + re.escape(keyword) + r'\b', page.page_content, re.IGNORECASE)]
                palavras_encontradas_por_pagina.append((page, palavras_encontradas))
                
            print(f"Número de páginas da Sentença filtradas por regex: {len(filtered_pages)}")
            #print(f"Páginas da inicial filtradas por regex: {filtered_pages}")
            for page, palavras_encontradas in palavras_encontradas_por_pagina:
                print(f"\nPágina {page.metadata['page'] + 1}:\nPalavras-chave encontradas: {', '.join(palavras_encontradas)}")
                print(f"Conteúdo da página:\n{page.page_content}\n") 
        
            
        #garante que a primeira pagina estará sempre presente
        if pages[0] not in filtered_pages:
            filtered_pages.append(pages[0])
            print(f"\nPágina {pages[0].metadata['page'] + 1} adicionada sem que houvessem palavras-chaves")
            print(f"Conteúdo da página:\n{pages[0].page_content}\n")

        tipo_documento = "Sentença"
        
        #garante que as duas ultimas paginas estarao presentes
        #if pages[-2] not in filtered_pages:
        #    filtered_pages.append(pages[-2])
        #if pages[-1] not in filtered_pages:
        #    filtered_pages.append(pages[-1])
        
            
    elif TipoDocumento == "Decisão Interlocutória":
        # Lista de palavras-chave que deseja filtrar - esta palavra tem sido suficiente para encontrar a página contendo a decisão
        palavras_filtro = ['defiro', 'indefiro', 'concedo', 'conceder', 'estão presentes os pressupostos para concessão']

        # Construindo a expressão regular para filtrar apenas as páginas que contém a decisão
        # Usamos \b para garantir que estamos capturando palavras inteiras
        filtro_regex = re.compile(r'\b' + r'\b|\b'.join([re.escape(keyword) for keyword in palavras_filtro]) + r'\b', re.IGNORECASE)
        
        # Filtrando páginas com base nas palavras-chave
        filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
        
        

        if Verbose:
            # Identificando as palavras-chave encontradas em cada página filtrada
            palavras_encontradas_por_pagina = []
            for page in filtered_pages:
                palavras_encontradas = [keyword for keyword in palavras_filtro if re.search(r'\b' + re.escape(keyword) + r'\b', page.page_content, re.IGNORECASE)]
                palavras_encontradas_por_pagina.append((page, palavras_encontradas))
            
            print(f"Número de páginas da Decisão filtradas por regex: {len(filtered_pages)}")
            #print(f"Páginas da inicial filtradas por regex: {filtered_pages}")
            for page, palavras_encontradas in palavras_encontradas_por_pagina:
                print(f"\nPágina {page.metadata['page'] + 1}:\nPalavras-chave encontradas: {', '.join(palavras_encontradas)}")
                print(f"Conteúdo da página:\n{page.page_content}...\n")  # Mostrando apenas os primeiros 500 caracteres para visualização
        
        #garante que a primeira pagina estara presente
        if pages[0] not in filtered_pages:
            filtered_pages.append(pages[0])
            if Verbose:
                print(f"\nPágina {pages[1].metadata['page'] + 1} adicionada sem que houvessem palavras-chaves")
                print(f"Conteúdo da página:\n{pages[1].page_content}\n")

        tipo_documento = "Decisão Interlocutória"
        
        #garante que as ultimas paginas estarao presentes
        #if pages[-2] not in filtered_pages:
        #    filtered_pages.append(pages[-2])
        #if pages[-1] not in filtered_pages:
        #    filtered_pages.append(pages[-1])
    
    elif TipoDocumento == "Petição Inicial":
        #Não foi implementado um mecanismo de filtragem das páginas para petições iniciais    
        filtered_pages = pages
        tipo_documento = "Petição Inicial"
    
    #situações de erro
    else:
        filtered_pages = pages
        tipo_documento = "Indeterminado"
    

    return (filtered_pages, tipo_documento, custo)

def ExtraiTipoDocumento(resumo):
    
    linhas = resumo.split('\n')
    for i, linha in enumerate(linhas):
        if re.search("Tipo", linha, re.IGNORECASE) and re.search("Documento", linha, re.IGNORECASE):
            break

    # Definindo os tipos de documentos possíveis
    tipos_possiveis = ["Petição Inicial", "Sentença", "Decisão"]
    
    # Lista para armazenar os tipos de documentos encontrados
    encontrados = []

    # Verificando cada tipo de documento no texto
    for t in tipos_possiveis:
        if re.search(t, linha, re.IGNORECASE):
            encontrados.append(t)
    # Se mais de um tipo de documento for encontrado, ou nenhum, retornar "Não determinado"
    if len(encontrados) > 1 or len(encontrados) == 0:
        tipo_identificado = "Indeterminado"
    elif len(encontrados) == 1:
        tipo_identificado = encontrados[0]
        
    return tipo_identificado



#Verifica se o PDF é searchable tentando extrair texto de suas páginas.
def Searchable(caminho):
    doc = fitz.open(caminho)
    searchable = True

    # Verifica todas as páginas, mas pode ser ruim para grandes documentos
    for page in doc:
        text = page.get_text().strip()
        if not text:
            searchable = False
            break  # Se qualquer página não tiver texto, considera o documento como não pesquisável
        
    doc.close()
    return searchable

#Extrai texto de um PDF usando OCR em cada página e gerando uma lista de Documents.
def ExtraiOCR(caminho):
    doc = fitz.open(caminho)
    
    #vai armazenar cada página extraída
    pages = []

    num_page  = 0
    for page in doc:
        # Extrai a imagem da página
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Aplica OCR na imagem usando pytesseract
        page_text = pytesseract.image_to_string(img, lang='por').encode('utf-8').decode('utf-8')
        
        #adiciona a página usando a classe Document
        pages.append(Document(page_content=page_text, metadata={"page": num_page, "source": caminho}))
        
        num_page += 1

    doc.close()
    return pages

