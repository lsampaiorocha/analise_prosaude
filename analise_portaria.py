from langchain_openai.chat_models import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document


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

#importa as funções de análise
from robo_consultas import *

import xlrd


# Define o caminho base como o diretório atual onde o script está sendo executado
base_directory = os.getcwd()

# Configuração da chave da API GPT
env_path = os.path.join(base_directory, 'ambiente.env')
load_dotenv(env_path)  # Carrega as variáveis de ambiente de .env

#verifica se a chave do GPT foi encontrada
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise RuntimeError("OPENAI_API_KEY não está definida")

#llm = ChatOpenAI(model_name="gpt-4", temperature=0)
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
embeddings = OpenAIEmbeddings()

# Define your desired data structure.
#class Meds(BaseModel):
#    meds: list[str] = Field(description="Lista de medicamentos presentes na sentença")
class Medicamento(BaseModel):
    nome: str = Field(default="N/A",description="Nome do medicamento")
    dose: int = Field(default=0,description="Dose do medicamento em miligramas")

class Medicamentos(BaseModel):
    meds: list[Medicamento] = Field(description="Lista de medicamentos com suas respectivas doses")
    
# Define your desired data structure.
class Inter(BaseModel):
    inter: list[str] = Field(description="Lista de itens que são consultas, exames, procedimentos clínicos e cirúrgicos")

# Define your desired data structure.
class Alim(BaseModel):
    alim: list[str] = Field(description="Lista de compostos alimentares presentes na sentença")

#Inicialização do dicionário que irá conter as respostas a serem devolvidas pela API
def inicializa_dicionario():
  dados = {
    #Se houve ou não pedido de indenização por danos morais e materiais
    "indenizacao": False,
    #Se houve ou não condenação de honorários acima de R$1500
    "condenacao_honorarios": None,
    #Se há outros itens além de medicamentos
    "possui_outros": None,
    #Se os laudos dos autos são públicos ou privados
    "laudo_publico": None,
    #valor total do tratamento
    "respeita_valor_teto": None,
    #valor total do tratamento
    "valor_teto": None,
    #medicamentos contidos na sentença
    "lista_medicamentos": [],
    #itens que não são medicamentos contidos na sentença...
    "lista_outros": [],
    #intervenções contidas na sentença: consultas, exames, procedimentos, internação em leito especializado, UTI...
    "lista_intervencoes": [],
    #compostos alimentares contidos na sentença
    "lista_compostos": [],
    #fornecimento de insulinas e insumos para aplicação e monitoramento do índice glicêmico
    "lista_glicemico": [],
    #fornecimento de insumos de atenção básica, como fraldas, cadeira de rodas, cama hospitalar e outros
    "lista_insumos": [],
    #tratamento multidisciplinar disponibilizado pelo SUS:, fisioterapia, fonoaudiologia, oxigênio domiciliar, embolização e oxigenoterapia hiperbárica...
    "lista_tratamento": [],
    #para cada inciso (1-6) indica se ele foi aplicado
    "aplicacao_incisos": [False, False, False, False, False, False]  
  }
  return dados


#Função para exibição de uma resposta na saída padrão
def exibe_dados(dados):
    print("Resumo da Decisão Judicial:\n")
    print(f"Pedido de Indenização por Danos: {'Sim' if dados['indenizacao'] else 'Não'}")
    print(f"Condenação de Honorários (acima de R$1500): {'Sim' if dados['condenacao_honorarios'] else 'Não'}")
    print(f"Outros Itens Além de Medicamentos: {'Sim' if dados['possui_outros'] else 'Não'}")
    print(f"Status dos Laudos: {'Públicos' if dados['laudo_publico'] else 'Privados'}")
    print(f"Respeita Valor Teto: {'Sim' if dados['respeita_valor_teto'] else 'Não'}")
    print(f"Valor Teto: R${dados['valor_teto'] if dados['valor_teto'] is not None else 'Não especificado'}")
    
    # Listas
    print("Medicamentos na Sentença:")
    if dados['lista_medicamentos']:
        for medicamento in dados['lista_medicamentos']:
            print(f"  - {medicamento}")
    else:
        print("  Nenhum")
        
    print("Outros itens na Sentença:")
    if dados['lista_outros']:
        for outro in dados['lista_outros']:
            print(f"  - {outro}")
    else:
        print("  Nenhuma")
    
    # Aplicação dos incisos
    print("Aplicação dos Incisos:")
    for i, aplicado in enumerate(dados['aplicacao_incisos'], start=1):
        print(f"  Inciso {i}: {'Aplicado' if aplicado else 'Não Aplicado'}")


#Função principal da API, que recebe o caminho de um arquivo contendo uma sentença ou petição inicial
#e retorna um dicionário com todas informações relacionadas à aplicação da portaria 01/2017
#MedRobot controla se o robô de consultas no google e anvisa será utilizado (há uma maior demora)
#Decisao indica se trata-se de sentença ou decisão, ou se trata-se da petição inicial
def portaria_prosaude(caminho, Verbose=False, MedRobot=True, Decisao=True):
  
    #verifica se o pdf no caminho é searchable, e caso não seja, roda o ocr
    if is_searchable(caminho):
        #Carrega o pdf dado pelo caminho
        loader = PyPDFLoader(caminho)
        pages = loader.load_and_split()
    else:
        pages = ocr_pdf(caminho)
    
    if Verbose:    
        print(f"Número de páginas lidas do arquivo: {len(pages)}")
    
    if Decisao:
        # Lista de palavras-chave que deseja filtrar - esta palavra tem sido suficiente para encontrar a página da sentença ou decisão
        palavras_filtro = ['julgo']

        # Construindo a expressão regular para filtrar apenas as páginas que contém a sentença ou decisão
        # Usamos \b para garantir que estamos capturando palavras inteiras
        filtro_regex = re.compile(r'\b' + r'\b|\b'.join([re.escape(keyword) for keyword in palavras_filtro]) + r'\b', re.IGNORECASE)
        
        # Filtrando páginas com base nas palavras-chave
        filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
        
        if Verbose:
            print(f"Número de páginas da decisão ou sentença filtradas por regex: {len(filtered_pages)}")
            print(f"Páginas da decisão ou sentença filtradas por regex: {filtered_pages}")
            
        #garante que a primeira pagina estara presente
        if pages[0] not in filtered_pages:
            filtered_pages.append(pages[0])

        #garante que a ultima pagina estara presente
        if pages[-1] not in filtered_pages:
            filtered_pages.append(pages[-1])
            
    else:
        # Lista de palavras-chave que deseja filtrar - esta palavra tem sido suficiente para encontrar a página da sentença ou decisão
        palavras_filtro = ['do pedido','dos pedidos', 'pedidos e requerimentos', 'síntese fática']

        # Construindo a expressão regular para filtrar apenas as páginas que contém a sentença ou decisão
        # Usamos \b para garantir que estamos capturando palavras inteiras
        filtro_regex = re.compile(r'\b' + r'\b|\b'.join([re.escape(keyword) for keyword in palavras_filtro]) + r'\b', re.IGNORECASE)
        
        # Filtrando páginas com base nas palavras-chave
        filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
        
        if Verbose:
            print(f"Número de páginas da inicial filtradas por regex: {len(filtered_pages)}")
            print(f"Páginas da inicial filtradas por regex: {filtered_pages}")
    try:
    
        

        if Verbose:    
            print(f"Número de páginas após filtragem inicial: {len(filtered_pages)}\n")
            for page in filtered_pages:
                print(f"Página {page.metadata['page']}")
                #print(f"Página {page.page_content}")
  

        # cria ids para as páginas, o que vai ser útil para gerenciar o banco de dados de vetores
        ids = [str(i) for i in range(1, len(filtered_pages) + 1)]

        #utiliza embeddings da OpenAI para o banco de vetores Chroma
        embeddings = OpenAIEmbeddings()
        docsearch = Chroma.from_documents(filtered_pages, embeddings, ids=ids, collection_metadata={"hnsw:M": 1024})
        #db = Chroma.from_documents(docs, embedding_model, persist_directory="./chroma_db_instance",collection_metadata={"hnsw:M": 1024,"hnsw:ef": 64})
            
        #prompt do robô - context vai ser preenchido pela retrieval dos documentos
        system_prompt = (
            "Você é um assessor jurídico analisando um documento que contém uma decisão judicial."
            "Utilize o contexto para responder às perguntas. "
            "Utilize apenas o contexto que se referir à decisão do juiz sobre o caso, em que é utilizado expressões como: sentença, julgo procedente, dispositivo, ratifico a decisão, "
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

        #cria uma chain de perguntas e respostas
        question_answer_chain = create_stuff_documents_chain(llm, prompt)

        #cria uma chain de retrieval para realizar as perguntas e respostas
        chain = create_retrieval_chain(docsearch.as_retriever(), question_answer_chain)

        #aplica o pipeline de análise
        resposta = analise_pipeline(chain, filtered_pages, Verbose, MedRobot)

        #apaga as entradas criadas no Chroma
        docsearch._collection.delete(ids=ids)
        
        return resposta
    
    except IndexError:
        print(f"Erro: Você tentou acessar um índice inválido ao analisar o arquivo {caminho.split()[-1]}.")
        return None
        
    except Exception as e:
        print(f"Erro ao processar o arquivo {caminho.split()[-1]}: {e}")
        return None


#Realiza todas as tarefas de análise necessárias para obtenção das informações
#retorna um dicionário com as informações obtidas
def analise_pipeline(chain, pages, Verbose=False, MedRobot=True):
    
    #analisa se existe condenação por honorários na sentença
    honor = analise_honorarios(chain)    
    
    #analisa se existe outros itens alem de medicamentos na sentença
    (outros, matches) = analise_outros(pages, Verbose)
    
    #lista contendo os nomes de medicamentos obtidos da sentença
    lm = analise_medicamentos(chain, Verbose)

    lm_busca = []
    lm_final = []

    if MedRobot == True:
        lm_busca = busca_medicamento(lm)
        lm_final = busca_CMED(lm_busca,lm)
    #caso não se esteja utilizando o robô, não será possível coletar as informações sobre os medicamentos
    elif lm:
        for med in lm:
            lm_busca.append((None, None, None, None, None, None,None))
            lm_final.append((None, None, "000000000", 0))
    #caso não hajam medicamentos, as listas serão vazias
    else:
        lm_busca = []
        lm_final = []

    #de toda forma faz a busca no CMED
    
    if Verbose:
        print(f"Lista lm_busca: {lm_busca}\n")
        print(f"Lista lm_final: {lm_final}\n")
    
    #verifica se o teto está respeitado:
    (teto, total) =  analise_teto(lm_final)
    
    if Verbose:
        print(f"Respeita teto: {teto}\n")
        print(f"Valor total: {total}\n")

    #inicialização do dicionário de resposta
    resposta = inicializa_dicionario()
    
    #preenche se houve condenação por honorários e se há outros itens além de medicamentos
    resposta['condenacao_honorarios'] = honor 
    resposta['possui_outros'] = outros
    
    
    resposta['respeita_valor_teto'] = teto
    resposta['valor_teto'] = "R$ {:.2f}".format(total)
   
   
    #acrescenta as palavras chave encontradas.
    resposta['lista_outros'] = matches
    
    if Verbose:
        print(f"Padrões de Outros: {matches}\n")
    
    #adiciona as informações de medicamentos obtidas
    for idx, (principio, nome_comercial, num_registro, preco) in enumerate(lm_final):
        resposta['lista_medicamentos'].append({
        "nome_extraido": lm[idx][0],
        "nome_principio": principio,
        "nome_comercial": nome_comercial,
        "dosagem": lm[idx][1],
        "registro_anvisa": num_registro,
        "oferta_SUS": None,
        "preco_PMVG": "R$ {:.2f}".format(preco),
        "preco_PMVG_max": None
        })
    

    if Verbose:
        exibe_dados(resposta)
    
    return resposta


#Recebe um conjunto de páginas e verifica se ocorre alguma das palavras proibitivas
def analise_outros(pages, Verbose=False):
    
    #palavras que tiveram que ser retiradas: procedimento, consulta, tratamento
    # Definindo palavras-chave importantes - OBS: Errar por excesso não é problema, o problema maior é não detectar
    palavras_filtro = ['aliment', 'enteral', 'dieta', 'Energy','sonda','frasco','fralda', 'álcool', 'atadura', 'tubo',
                       'gase', 'luvas', 'esparadrapo', 'algodão','cama', 'colchão', 'UTI', 'UCE', 'seringa', 'aspirador',
                       'terapia', 'exame', 'consulta médica', 'procedimento cirúrgico', 'cirurgia', 'cadeira de roda', 
                       'internação', 'sessão de laser', 'sessão de fisio', 'atendimento com médico',
                       'tratamento cirúrgico', 'equipo', 'suplementação alimentar', 'compostos alimentares',
                       'sensor de glicose', 'insulina', 'fonoaudiólogo', 'fisioterapia', 'CPAP', 
                       'aparelho', 'BIPAP', 'umidificador', 'mascara', 'psicopedagógico', 'psicólogo', 'psiquiatr']
    
    
    # Aplicando a função de normalização para lidar com acentos e assegurar espaço em branco no início
    regex_patterns = [r'\b' + normalize_regex(re.escape(keyword)).replace(r'\ ', r'\s+') + r'\b' for keyword in palavras_filtro]
    filtro_regex = re.compile('|'.join(regex_patterns), re.IGNORECASE)
    
    # Filtrando páginas com base nas palavras-chave
    filtered_pages = [page for page in pages if filtro_regex.search(page.page_content)]
    
    # Conjunto para armazenar palavras-chave únicas encontradas
    unique_keywords = set()

    # Analisando cada página para correspondências
    for page in pages:
        matches = filtro_regex.findall(page.page_content)
        if matches:
            # Adicionando correspondências ao conjunto, que automaticamente remove duplicatas
            unique_keywords.update([match.lower() for match in matches])  # Converte para lowercase para evitar duplicatas por case
    
    #necessário para apresentar onde foram identificados os padrões e que padrões foram identificados
    if Verbose:
        if len(filtered_pages) > 0:
            print("Correspondências encontradas na análise de Outros itens:")
            # Estrutura para capturar trechos correspondentes
            filtered_pages_with_matches = [
            (page, [match.group(0) for match in filtro_regex.finditer(page.page_content)])
            for page in pages
            if filtro_regex.search(page.page_content)
            ]
            # Agora filtered_pages_with_matches contém tuplas de página e lista de todos os trechos correspondentes
            for page, matches in filtered_pages_with_matches:
                print(f"Na página {page.metadata['page']}: Correspondências encontradas - {matches}")
    
    
    # Interpreta a resposta como 'Sim' ou 'Não' e converte para booleano
    possui_outros = True if len(filtered_pages) > 0 else False
    
    if Verbose:
        print(f"Possui outros itens: {possui_outros} Quais: {list(unique_keywords)}")

    # Retorna o resultado encapsulado no modelo Pydantic
    return (possui_outros, list(unique_keywords))

#Recebe uma retrieval chain de uma sentença e retorna Sim ou não se houve condenação do estado do ceará ao pagamento de honorários
def analise_honorarios(chain):
      
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




#Recebe uma retrieval chain de uma sentença e retorna uma lista de medicamentos presentes
# pares (medicamento, dosagem_em_mg)
def analise_medicamentos(chain, Verbose=False):

    lm = [] #lista de medicamentos

    #Aqui o objetivo dos prompts é listar os itens que são medicamentos

    q1 = """
        Você é um assessor jurídico analisando um documento que contém uma decisão judicial.
    
        Considere como medicamentos apenas substâncias ou compostos farmacêuticos usados exclusivamente para tratar, prevenir ou curar doenças. 
    
        Outros itens médicos ou de assistência, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros não são medicamentos
        
        Sua tarefa é fornecer uma lista contendo apenas os itens que são medicamentos na decisão judicial e a dosagem em miligramas(MG).
        
        Em hipótese alguma forneça na lista medicamentos que não estavam na decisão. Se não houverem medicamentos, apenas responda que não há medicamentos.
    """
    
    r1 = chain.invoke({"input": q1}).get('answer')
    
    
    if Verbose:
        print(f"Medicamentos presentes na sentença: {r1}")
    

    parser = JsonOutputParser(pydantic_object=Medicamentos)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos medicamentos e o valor da dosagem em miligramas (MG).\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser

    lm = chain2.invoke({"query": r1}).get("meds")

    if Verbose:
        print(f"Medicamentos extraidos da sentença: {lm}")  
    
    r = []
    
    #previne algumas situações chatas em que não é retornado no formato previsto
    for med in lm:
        if 'dose' not in med:
            med['dose'] = 0 
        if 'nome' not in med:
            med['nome'] = ""
        r.append((med['nome'], med['dose']))
    
    if Verbose:
        print(f"Medicamentos já dentro da estrutura: {r}") 
 
    return r

#Recebe uma retrieval chain de uma sentença e retorna uma lista de intervenções
# pares (medicamento, dosagem_em_mg)
def analise_intervencoes(chain):
    #Aqui o objetivo  dos prompts  é listar os itens que não são medicamentos (não está funcionando bem)
    
    q1 = """
        Você é um assessor jurídico analisando um documento que contém uma decisão judicial.
        
        Você deve limitar sua análise ao trecho da sentença, onde ele declara que julga procedente ou improcedente o pedido.
        
        Considere uma consulta médica como uma interação entre um paciente e um profissional de saúde, tipicamente um médico, para avaliação, diagnóstico e planejamento do tratamento de qualquer condição de saúde. 
        
        Considere como um exames médico um procedimento laboratorial ou de imagem que ajude a avaliar e diagnosticar problemas de saúde do paciente.
        
        Considere como procedimento clínicos ou cirúrgico uma intervenção terapêuticas para tratar doenças, lesões ou deformidades.
        
        Sua tarefar é identificar e extrair qualquer menção à realização de consultas, exames, e procedimentos clínicos e cirúrgicos na sentença.
        
        Sua resposta deve ser uma lista contendo os itens extraídos da sentença.
    """
    
    r1 = chain.invoke({"input": q1}).get('answer')  
    
    parser = JsonOutputParser(pydantic_object=Inter)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos itens que não são medicamentos.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain3 = prompt | llm | parser

    lo = chain3.invoke({"query": r1}).get("outr") 
        
    return lo


#Recebe uma retrieval chain de uma sentença e retorna uma lista de medicamentos presentes
# pares (medicamento, dosagem_em_mg)
def analise_alimentares(chain):

    la = [] #lista de compostos alimentares

    #Aqui o objetivo dos prompts é listar os itens que são compostos alimentares

    """
    Você é um assessor jurídico analisando um documento que contém uma decisão judicial.

    Considere como compostos alimentares apenas substâncias ou produtos alimentícios usados exclusivamente para nutrir, complementar a dieta ou fornecer benefícios à saúde, excluindo medicamentos e suplementos farmacêuticos.

    Outros itens não alimentares, como fraldas, seringas, luvas, oxímetro, leitos hospitalares ou termômetros, não são compostos alimentares.

    Sua tarefa é fornecer uma lista contendo apenas os itens que são compostos alimentares na decisão judicial.
    """

    
    r1 = chain.invoke({"input": q1}).get('answer')

    parser = JsonOutputParser(pydantic_object=Alim)

    prompt = PromptTemplate(
        template="Forneça apenas a lista com os nomes dos compostos alimentares.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain2 = prompt | llm | parser

    la = chain2.invoke({"query": r1}).get("meds") 
        
    return la


#Recebe uma lista com tuplas (medicamento, dose_em_mg, nome_comercial, registro_anvisa, valor)
#e verifica se respeita o limite de 60 salários mínimos
#Por fazer
def analise_teto(lm):
    
    
    total = 0
    res = True
    
    #adiciona as informações de medicamentos obtidas
    for idx, (principio, nome_comercial, num_registro, preco) in enumerate(lm):
        if preco != None:
            total += 12*preco
    
    if total > 1640*60:
        res = False
        
        
    return (res, total)


#Função que irá acrescentar informações sobre os medicamentos
#recebe uma lista com pares (principios ativos, dose_em_mg) e retorna tuplas 
#(principio ativo, dose_em_mg, nome_comercial, registro_anvisa, valor_PMVG)
def busca_info(lm):
    
    # Tabela de onde vão ser retiradas as infos dos medicamentos
    tabela_precos =  pd.read_excel('tabela_precos.xls',skiprows=52)
    
    #Lista que retorna no final da função
    infos_medicamentos = list()

    # Laço para pegar as informações de cada medicamento na tabela pmvg
    for medicamento, dose in lm:
        tabela_precos_2 = tabela_precos
        tabela_precos_2['SUBSTÂNCIA'] = tabela_precos_2['SUBSTÂNCIA'].fillna('')
        medicamento =  medicamento.split(' + ')
        for i in medicamento:
            padrao = re.compile(i, re.IGNORECASE)
            tabela_precos_2 =  tabela_precos_2[tabela_precos_2['SUBSTÂNCIA'].str.contains(padrao)]
    

        if tabela_precos_2.empty:
            infos_medicamentos.append((medicamento,dose,None,None,None))
        else:
            indice_maior_preco = tabela_precos_2['PMVG Sem Imposto'].idxmax()
            preco = tabela_precos_2.loc[indice_maior_preco,'PMVG Sem Imposto']
            dosagem  = tabela_precos_2.loc[indice_maior_preco,'APRESENTAÇÃO']
            num_registro = tabela_precos_2.loc[indice_maior_preco,'REGISTRO']
            nome_comercial = tabela_precos_2.loc[indice_maior_preco,'PRODUTO'] 
            substancia = tabela_precos_2.loc[indice_maior_preco,'SUBSTÂNCIA']
            infos_medicamentos.append((substancia,dosagem,nome_comercial,num_registro,preco))
    return infos_medicamentos    
                


#Verifica se o PDF é searchable tentando extrair texto de suas páginas.
def is_searchable(caminho):
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
def ocr_pdf(caminho):
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

# Criando uma função para substituir letras acentuadas por regex que aceita ambas as formas
def normalize_regex(keyword):
    replacements = {
        'á': '[aá]', 'é': '[eé]', 'í': '[ií]', 'ó': '[oó]', 'ú': '[uú]',
        'â': '[aâ]', 'ê': '[eê]', 'î': '[iî]', 'ô': '[oô]', 'û': '[uû]',
        'ã': '[aã]', 'õ': '[oõ]',
        'ç': '[cç]'
    }
    for accented, regex in replacements.items():
        keyword = re.sub(accented, regex, keyword)
    return keyword
