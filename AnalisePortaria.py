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

#importa as funções de análise dos demais módulos
from RobosConsultasMedicamentos import *
from AnaliseMedicamentos import *
from AnaliseOutros import *
from AnaliseHonorarios import *
from AnaliseAlimentares import *
from AnaliseInternacao import *
from AnaliseConsultaExameProcedimentoInternacao import *
from ResumoDocumentos import *


# Define o caminho base como o diretório atual onde o script está sendo executado
base_directory = os.getcwd()

# Configuração da chave da API GPT
env_path = os.path.join(base_directory, 'ambiente.env')
load_dotenv(env_path)  # Carrega as variáveis de ambiente de .env

#verifica se a chave do GPT foi encontrada
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise RuntimeError("OPENAI_API_KEY não está definida")

embeddings = OpenAIEmbeddings()

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
    "aplicacao_incisos": [False, False, False, False, False, False] ,
    #custo dos LLMs utilizados no processo
    "custollm": 0, 
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
        print(f"  Inciso {i}: {True if aplicado else False}")
        
    print(f"Custo Total dos LLMs: {dados['custollm']}")

#Função principal da API, que recebe o caminho de um arquivo contendo uma sentença ou petição inicial
#e retorna um dicionário com todas informações relacionadas à aplicação da portaria 01/2017
#MedRobot controla se o robô de consultas no google e anvisa será utilizado (há uma maior demora)
#Decisao indica se trata-se de sentença ou decisão, ou se trata-se da petição inicial
def AnalisePortaria(caminho, models, Verbose=False, MedRobot=True, TipoDocumento="Sentença", Resumo=True):
    
    if Verbose:
        print("Modo verbose ativado.")    
        if MedRobot:
            print("MedRobot está ativado.")
            
    #realiza o preprocessamento e filtragem das paginas do pdf
    (filtered_pages, custoresumo) = preprocessamento(caminho, models, Verbose, TipoDocumento, Resumo=Resumo)
  
    try:
        if Verbose:    
            print(f"Número de páginas após pré-processamento: {len(filtered_pages)}\n")
            #for page in filtered_pages:
            #    print(f"Página {page.metadata['page']}")
            #    print(f"Página {page.page_content}")

        # cria ids para as páginas, o que vai ser útil para gerenciar o banco de dados de vetores
        ids = [str(i) for i in range(1, len(filtered_pages) + 1)]

        #utiliza embeddings da OpenAI para o banco de vetores Chroma
        embeddings = OpenAIEmbeddings()
        docsearch = Chroma.from_documents(filtered_pages, embeddings, ids=ids, collection_metadata={"hnsw:M": 1024}) #essa opção "hnsw:M": 1024 é importante para não ter problemas
            
        #aplica o pipeline de análise apropriado ao tipo de documento
        resposta = AnalisePipeline(filtered_pages, docsearch, models, Verbose, MedRobot, TipoDocumento=TipoDocumento, Resumo=Resumo, CustoResumo=custoresumo)

        #apaga as entradas criadas no Chroma
        docsearch._collection.delete(ids=ids)
        
        return resposta
    
    except IndexError:
        print(f"Erro: Você tentou acessar um índice inválido ao analisar o arquivo {caminho.split()[-1]}.")
        return None
        
    except Exception as e:
        print(f"Erro ao processar o arquivo {caminho.split()[-1]}: {e}")
        return None

# Carrega o pdf, inclusive caso seja non-searchable
# Caso Resumo esteja desabilitado, pré-processa para eliminar páginas desnecessárias para análise
# Caso Resumo esteja habilitado, aplica LLM para resumir as principais informações necessárias
def preprocessamento(caminho, models, Verbose=False, Mode="Sentença", Resumo=True):
    
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
        
    if Resumo:
        print(f'Valor de models: {models}')
        
        (resumo, custo) = GeraResumo(pages, models['resumo'], api_key, Verbose=Verbose)
        
        ''' EXEMPLO DE RESUMO (para testes)
        resumo = """
        **Resumo do Documento**

        **Itens a serem fornecidos:**
        - Medicamento: Denosumabe
        - Dosagem: Não especificada
        - Quantidade: Uma dose a cada seis meses
        - Duração do tratamento: Enquanto necessário, conforme indicação médica

        **Internação ou Transferência:**
        - Não há solicitação ou obrigação de internação ou transferência para Unidade de Terapia Intensiva (UTI) ou Unidade de Cuidados Especiais (UCE).

        **Indenização por Danos Morais:**
        - Não há solicitação de indenização por danos morais.

        **Condenação por Danos Morais:**
        - Não há condenação por danos morais.

        **Condenação por Honorários:**
        - Não há condenação por honorários.

        **Condenação por Multa ou Bloqueio de Recursos:**
        - Há determinação de bloqueio de verba pública para efetivo cumprimento da ordem judicial, caso o Estado do Ceará não forneça o medicamento Denosumabe no prazo de 10 dias.

        **Detalhes Adicionais:**
        - A ação foi ajuizada por Maria da Silva Ferreira contra o Estado do Ceará, solicitando o fornecimento do medicamento Denosumabe devido ao diagnóstico de osteoporose grave.
        - A decisão defere o pedido de antecipação de tutela, determinando o fornecimento do medicamento a cada seis meses, com renovação dos laudos médicos a cada três meses.
        - O processo tramita na 11ª Vara da Fazenda Pública da Comarca de Fortaleza, sob o número 3006163-31.2022.8.06.0001, com valor da causa de R$ 2.240,00.     
        - A ação é pública e a requerente tem direito à justiça gratuita."""
        '''
        
        filtered_pages = []
        filtered_pages.append(Document(page_content=resumo, metadata={"page": 0, "source": caminho}))
        
    elif Mode == "Sentença":
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

        #garante que as duas ultimas paginas estarao presentes
        #if pages[-2] not in filtered_pages:
        #    filtered_pages.append(pages[-2])
        #if pages[-1] not in filtered_pages:
        #    filtered_pages.append(pages[-1])
        
            
    elif Mode == "Decisão":
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
        if pages[1] not in filtered_pages:
            filtered_pages.append(pages[0])
            if Verbose:
                print(f"\nPágina {pages[1].metadata['page'] + 1} adicionada sem que houvessem palavras-chaves")
                print(f"Conteúdo da página:\n{pages[1].page_content}\n")

        #garante que as ultimas paginas estarao presentes
        #if pages[-2] not in filtered_pages:
        #    filtered_pages.append(pages[-2])
        #if pages[-1] not in filtered_pages:
        #    filtered_pages.append(pages[-1])
        

    return (filtered_pages, custo)

# Realiza o passo a passo da análise necessária para elaborar o relatório e recomendar ou não a aplicação da portaria
# retorna um dicionário com as informações obtidas
def AnalisePipeline(pages, docsearch, models, Verbose=False, MedRobot=True, TipoDocumento="Sentença", Resumo=True, CustoResumo=0):


    if TipoDocumento == "Sentença":
        #analisa se existe condenação por honorários na sentença
        (honor, chonor) = AnaliseHonorarios(docsearch, model=models['honorarios'], Verbose=Verbose, Resumo=Resumo)
        

        # Detecta (usando REGEX) se existe outros itens alem de medicamentos na sentença
        # é feita uma diferenciação entre itens proibidos e itens permitidos para aplicação da portaria
        # itens que ainda não são analisados pelo robô são tratados como proibidos, embora estejam na portaria 01/2017
        coutros=0
        cdoutros=0
        (outrosregex_permitidos, listaoutrosregex_permitidos, outrosregex_proibidos, listaoutrosregex_proibidos) = AnaliseOutrosRegex(pages, Verbose)
                
        #por enquanto os proibidos e permitidos ainda são tradados de forma unificada, porém deve-se modificar isto
        outrosregex = outrosregex_permitidos or outrosregex_proibidos
        listaoutros = listaoutrosregex_permitidos + listaoutrosregex_proibidos
        
        #detecta (usando LLM) se existem outros itens além de medicamentos na sentença
        (doutrosllm, cdoutros) = DetectaOutrosLLM(docsearch, model=models['doutros'], Verbose=Verbose, Resumo=Resumo) 
        
        
        # detecção de outros itens, que combina o REGEX e LLM
        # Caso seja detectado por LLM, verifica-se o REGEX para decidir pela detecção
        outros=False
        if doutrosllm:
            #TODO: pensar uma dinamica para distinguir os outros proibidos e os aceitaveis
            if outrosregex:
                outros = True   
        
        #lista contendo os nomes de medicamentos obtidos da sentença
        (lm, cmeds) = AnaliseMedicamentos(docsearch, model=models['medicamentos'], Verbose=Verbose, Resumo=Resumo)

        lm_busca = []
        lm_final = []

        #verifica se robô de consulta está habilitado e se existe algum item na lista
        if MedRobot == True and lm:
            lm_busca = RoboGoogleAnvisa(lm)
            lm_final = ConsultaCMED(lm_busca,lm)
        #caso não se esteja utilizando o robô, não será possível coletar as informações sobre os medicamentos
        #assim, para cada medicamento extraído iremos preencher com informações vazias
        elif lm:
            for med in lm:
                lm_busca.append((None, None, None, None, None, None,None))
                lm_final.append((None, None, "000000000", 0))
        #caso não hajam medicamentos, as listas serão vazias
        else:
            lm_busca = []
            lm_final = []

        if Verbose:
            print(f"Lista lm_busca: {lm_busca}\n")
            print(f"Lista lm_final: {lm_final}\n")
        
        #verifica se o teto está respeitado:
        (teto, total) =  VerificaTeto(lm_final)
        
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
        resposta['lista_outros'] = listaoutros
        
        if Verbose:
            print(f"Lista de Outros: {listaoutros}\n")
        
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
        
        
        #resultado da aplicação da portaria em seus 6 incisos
        resposta['aplicacao_incisos'] = [resposta['lista_medicamentos'] and resposta['respeita_valor_teto'] and not resposta['condenacao_honorarios'] and not resposta['possui_outros'],
            False,
            False,
            False,
            False,
            False]


        #custo total com LLMs
        resposta['custollm'] = cdoutros+coutros+cmeds+chonor+CustoResumo

        if Verbose:
            exibe_dados(resposta)
            print(f"Custo com LLMs para Resumo: {"$ {:.4f}".format(CustoResumo)}")
            print(f"Custo com LLMs para extração de medicamentos: {"$ {:.4f}".format(cmeds)}")
            print(f"Custo com LLMs para detecção de outros itens: {"$ {:.4f}".format(cdoutros)}")
            print(f"Custo com LLMs para extração de outros itens: {"$ {:.4f}".format(coutros)}")
            print(f"Custo com LLMs para detecção de condenação por honorários: {"$ {:.4f}".format(chonor)}")
            
            print(f"Custo total com LLMs: {"$ {:.4f}".format(cdoutros+coutros+cmeds+chonor+CustoResumo)}")
        
    if TipoDocumento == "Decisão" or TipoDocumento == "Petição Inicial":
        
        #analisa se existe condenação por honorários na sentença
        (honor, chonor) = AnaliseHonorarios(docsearch, model=models['honorarios'], Verbose=Verbose, Resumo=Resumo)
        

        # Detecta (usando REGEX) se existe outros itens alem de medicamentos na sentença
        # é feita uma diferenciação entre itens proibidos e itens permitidos para aplicação da portaria
        # itens que ainda não são analisados pelo robô são tratados como proibidos, embora estejam na portaria 01/2017
        coutros=0
        cdoutros=0
        (outrosregex_permitidos, listaoutrosregex_permitidos, outrosregex_proibidos, listaoutrosregex_proibidos) = AnaliseOutrosRegex(pages, Verbose)
                
        #por enquanto os proibidos e permitidos ainda são tradados de forma unificada, porém deve-se modificar isto
        outrosregex = outrosregex_permitidos or outrosregex_proibidos
        listaoutros = listaoutrosregex_permitidos + listaoutrosregex_proibidos
        
        #detecta (usando LLM) se existem outros itens além de medicamentos na sentença
        (doutrosllm, cdoutros) = DetectaOutrosLLM(docsearch, model=models['doutros'], Verbose=Verbose, Resumo=Resumo) 
        
        
        # detecção de outros itens, que combina o REGEX e LLM
        # Caso seja detectado por LLM, verifica-se o REGEX para decidir pela detecção
        outros=False
        if doutrosllm:
            #TODO: pensar uma dinamica para distinguir os outros proibidos e os aceitaveis
            if outrosregex:
                outros = True   
        
        #lista contendo os nomes de medicamentos obtidos da sentença
        (lm, cmeds) = AnaliseMedicamentos(docsearch, model=models['medicamentos'], Verbose=Verbose, Resumo=Resumo)

        lm_busca = []
        lm_final = []

        #verifica se robô de consulta está habilitado e se existe algum item na lista
        if MedRobot == True and lm:
            lm_busca = RoboGoogleAnvisa(lm)
            lm_final = ConsultaCMED(lm_busca,lm)
        #caso não se esteja utilizando o robô, não será possível coletar as informações sobre os medicamentos
        #assim, para cada medicamento extraído iremos preencher com informações vazias
        elif lm:
            for med in lm:
                lm_busca.append((None, None, None, None, None, None,None))
                lm_final.append((None, None, "000000000", 0))
        #caso não hajam medicamentos, as listas serão vazias
        else:
            lm_busca = []
            lm_final = []

        if Verbose:
            print(f"Lista lm_busca: {lm_busca}\n")
            print(f"Lista lm_final: {lm_final}\n")
        
        #verifica se o teto está respeitado:
        (teto, total) =  VerificaTeto(lm_final)
        
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
        resposta['lista_outros'] = listaoutros
        
        if Verbose:
            print(f"Lista de Outros: {listaoutros}\n")
        
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
        
        
        #resultado da aplicação da portaria em seus 6 incisos
        resposta['aplicacao_incisos'] = [resposta['lista_medicamentos'] and resposta['respeita_valor_teto'] and not resposta['condenacao_honorarios'] and not resposta['possui_outros'],
            False,
            False,
            False,
            False,
            False]


        if Verbose:
            exibe_dados(resposta)
            print(f"Custo com LLMs para Resumo: {"$ {:.4f}".format(CustoResumo)}")
            print(f"Custo com LLMs para extração de medicamentos: {"$ {:.4f}".format(cmeds)}")
            print(f"Custo com LLMs para detecção de outros itens: {"$ {:.4f}".format(cdoutros)}")
            print(f"Custo com LLMs para extração de outros itens: {"$ {:.4f}".format(coutros)}")
            print(f"Custo com LLMs para detecção de condenação por honorários: {"$ {:.4f}".format(chonor)}")
            
            print(f"Custo total com LLMs: {"$ {:.4f}".format(cdoutros+coutros+cmeds+chonor+CustoResumo)}")
        
        #custo total com LLMs
        resposta['custollm'] = cdoutros+coutros+cmeds+chonor
    
    
    
    return resposta


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






