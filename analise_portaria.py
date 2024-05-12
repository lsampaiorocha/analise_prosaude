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


from dotenv import load_dotenv


#OCRIZACAO
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Ajuste o caminho
import fitz  # PyMuPDF
from PIL import Image
import io




llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2)
embeddings = OpenAIEmbeddings()

# Define your desired data structure.
class Meds(BaseModel):
    meds: list[str] = Field(description="Lista de medicamentos presentes na sentença")
    
# Define your desired data structure.
class Outr(BaseModel):
    outr: list[str] = Field(description="Lista de itens que não são medicamentos presentes na sentença")


def analisar_portaria(caminho, incisos):
  
  #Carrega o pdf dado pelo caminho
  loader = PyPDFLoader(caminho)
  pages = loader.load_and_split()

  # cria ids para as páginas, o que vai ser útil para gerenciar o banco de dados de vetores
  ids = [str(i) for i in range(1, len(pages) + 1)]

  #utiliza embeddings da OpenAI para o banco de vetores Chroma
  embeddings = OpenAIEmbeddings()
  docsearch = Chroma.from_documents(pages, embeddings, ids=ids)
  
  
  #prompt do robô - context vai ser preenchido pela retrieval dos documentos
  system_prompt = (
    "Você é um assessor jurídico analisando um documento que contém uma decisão judicial."
    "Utilize o contexto para responder à pergunta. "
    "Seja conciso nas respostas, entregando apenas as informações solicitadas"
    "Contexto: {context}"
  )
  

  #prompt do chat
  prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
  )

  #cria uma chain de question and anwer
  question_answer_chain = create_stuff_documents_chain(llm, prompt)

  #cria uma chain de retrieval
  chain = create_retrieval_chain(docsearch.as_retriever(), question_answer_chain)
  
  #saida a ser apresentada na pagina
  r = ""
  
  #print(incisos)
  
  for i in incisos:
    match i:
        case "i1":
            [m, o] = inciso1(chain)
            
            #Função que irá normalizar os nomes de modo a ser buscado na tabela
            #recebe uma lista com pares (medicamento, dose_em_mg) e normaliza os nomes dos medicamentos 
            # de acordo com o princípio ativo e separando nomes compostos por ; como na planilha do Jonas
            m = normaliza_nomes(m)
            
            #Função que irá acrescentar informações sobre os medicamentos
            #recebe uma lista com pares (medicamento, dose_em_mg) e retorna tuplas 
            #(medicamento, dose_em_mg, nome_comercial, registro_anvisa, valor)
            m = busca_info(m)
            
            #se somente medicamentos
            if m and not o:
              if verifica_teto(m):
                if verifica_anvisa(m):
                  r = "\n".join([r, "Aplica-se a Portaria:", str(m)])
                return r
              
              else:
                r = "\n".join([r, "Os medicamentos violam o teto de 60 salários mínimos "])
                return r
                
            #senão
            else:
              r = "\n".join([r, "Existem outros itens que o robô ainda não é capaz de analisar : ", str(o)])
              return r
        case "i2":
            break
        case "i3":
            break
        case "i4":
            break
        case "i5":
            break
        case "i6":
            break
        case _:
            print("Valor fora do intervalo 1-6")


  docsearch._collection.delete(ids=ids)
  return r



#Recebe uma retrieval chain de uma sentença e retorna duas listas: 
# lista 1 medicamentos presentes -> pares (medicamento, dosagem_em_mg)
# lista 2 outros itens

def inciso1(chain):

    lm = [] #lista de medicamentos
    lo = [] #lista de outros itens


    #Aqui o objetivo dos prompts é listar os itens que são medicamentos

    q1 = """
        Você é um assessor jurídico analisando um documento que contém uma decisão judicial.
    
        Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou diagnosticar doenças. 
    
        Outros itens médicos ou de assistência, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos
        
        Sua tarefa é fornecer uma lista contendo apenas os itens que são medicamentos.
    """
    
    r1 = chain.invoke({"input": q1}).get('answer')

    parser = JsonOutputParser(pydantic_object=Meds)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos medicamentos.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser

    lm = chain2.invoke({"query": r1}).get("meds") 
    
    
    #Aqui o objetivo  dos prompts  é listar os itens que não são medicamentos (não está funcionando bem)
    
    q2 = """
        Você é um assessor jurídico analisando um documento que contém uma decisão judicial.
    
        Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou diagnosticar doenças. 
    
        Sua tarefa é fornecer uma lista contendo apenas os itens da sentença que são itens médicos ou de assistência, mas que não são medicamentos.
        
        Por exemplo: fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos.
    """
    
    r2 = chain.invoke({"input": q2}).get('answer')  
    
    parser = JsonOutputParser(pydantic_object=Outr)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos itens que não são medicamentos.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain3 = prompt | llm | parser

    lo = chain3.invoke({"query": r2}).get("outr") 
    
    lo = []
        
    return [lm, lo]


#Recebe como entrada uma string contendo uma lista de medicamentos e suas dosagens (em mg), separados por vírgula
#Por fazer
def analisar_medicamentos(medicamentos):
  #m = medicamentos
  #normaliza_nomes(m)
  #verifica_teto(m):
  #verifica_anvisa(m)
  #verifica_sus(m)
  return medicamentos


#recebe uma lista com pares (medicamento, dose_em_mg) e normaliza os nomes dos medicamentos de acordo com o princípio ativo
#Por fazer
def normaliza_nomes(m):
  return m

#Recebe uma lista com tuplas (medicamento, dose_em_mg, nome_comercial, registro_anvisa, valor)
#e verifica se respeita o limite de 60 salários mínimos
#Por fazer
def verifica_teto(m):
  return True

#Recebe uma lista com tuplas (medicamento, dose_em_mg, nome_comercial, registro_anvisa, valor)
#e verifica se todos estão registrados na anvisa
#Por fazer
def verifica_anvisa(m):
  return True


#Função que irá acrescentar informações sobre os medicamentos
#recebe uma lista com pares (medicamento, dose_em_mg) e retorna tuplas 
#(medicamento, dose_em_mg, nome_comercial, registro_anvisa)
#Por fazer
def busca_info(m):
  return m
                


#Verifica se o PDF é searchable tentando extrair texto de suas páginas.
def is_searchable(caminho):
    doc = fitz.open(caminho)
    searchable = True

    # Verifica todas as páginas, mas pode ser ruim para grandes documentos
    for page in doc:
        text = page.get_text().strip()
        if not text:
            searchable = False
            break  # Se qualquer página tiver texto, considera o documento como pesquisável
        
    doc.close()
    return searchable

#Extrai texto de um PDF usando OCR em cada página.
def ocr_pdf(caminho):
    doc = fitz.open(caminho)
    texto = []

    for page in doc:
        # Extrai a imagem da página
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Aplica OCR na imagem usando pytesseract
        page_text = pytesseract.image_to_string(img)
        texto.append(page_text)

    doc.close()
    return all_text
