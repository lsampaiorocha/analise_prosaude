from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

from dotenv import load_dotenv

#importa as funções de análise dos demais módulos
from ModulosAnalise.PreProcessamento import *
from ModulosAnalise.RobosConsultasMedicamentos import *
from ModulosAnalise.AnaliseMedicamentos import *
from ModulosAnalise.AnaliseOutros import *
from ModulosAnalise.AnaliseHonorarios import *
from ModulosAnalise.AnaliseAlimentares import *
from ModulosAnalise.AnaliseInternacao import *
from ModulosAnalise.AnaliseConsultasProcedimentos import *
from ModulosAnalise.ResumoDocumentos import *

import os
import tempfile
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename





class TipoDocumentoIndeterminadoException(Exception):
    pass

# Define o caminho base como o diretório atual onde o script está sendo executado
base_directory = os.getcwd()

load_dotenv()  # Carrega as variáveis de ambiente de .env

#verifica se a chave do GPT foi encontrada
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise RuntimeError("OPENAI_API_KEY não está definida")

embeddings = OpenAIEmbeddings()


#Inicialização do dicionário que irá conter as respostas a serem devolvidas pela API
def inicializa_dicionario():
  dados = {
    #Resumo do documento
    "resumo": "",
    #Resumo da análise (para debug)
    "resumo_analise": "",
    #Tipo de documento
    "tipo_documento": "",
    #Se houve ou não pedido de indenização por danos morais e materiais
    "indenizacao": False,
    #Se houve ou não condenação de honorários acima de R$1500
    "condenacao_honorarios": None,
    #Se houve pedido de internação em leito hospitalar, UTI ou UCE
    "internacao": None,
    #Se houve pedido de consulta exame ou procedimento
    "possui_consulta": None,
    #Se há outros itens além de medicamentos
    "possui_outros": None,
    #Se há custeio de conta de energia elétrica
    "possui_custeio": None,
    #Se há outros itens proibidos
    "possui_outros_proibidos": None,
    #Se os laudos dos autos são públicos ou privados
    "laudo_publico": None,
    #Se respeita o valor total do tratamento
    "respeita_valor_teto": None,
    #valor total do tratamento
    "valor_teto": None,
    #houve extinção do processo
    'houve_extincao': False,
    #é uma decisão de cumprimento de sentença
    'cumprimento_de_sentenca': False,
    #houve o bloqueio de recursos ou contas
    'bloqueio_de_recursos': False,
    #é uma decisão monocrática
    'monocratica': False,
    #medicamentos contidos na sentença
    "lista_medicamentos": [],
    #itens que não são medicamentos contidos na sentença...
    "lista_outros": [],
    #itens que não são medicamentos contidos na sentença...
    "lista_outros_proibidos": [],
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
    #tokens dos LLMs utilizados no processo
    "tokensllm": (0, 0),
  }
  return dados


#Função principal da API, que recebe o caminho de um arquivo contendo uma sentença ou petição inicial
#e retorna um dicionário com todas informações relacionadas à aplicação da portaria 01/2017
#MedRobot controla se o robô de consultas no google e anvisa será utilizado (há uma maior demora)
#Os tipos de documento possíveis são: "Petição Inicial", "Decisão Interlocutória" (interlocutória), "Sentença" e "Indeterminado"
def AnalisePortaria(entrada, models, pdf_filename, Verbose=False, MedRobot=True, TipoDocumento="Indeterminado", Resumo=True):
    
    # Verifica se a entrada é um arquivo (FileStorage) ou um caminho existente
    if isinstance(entrada, FileStorage):
               
        # Define uma pasta temporária apropriada
        pasta_destino = "/tmp"  # Diretório seguro para arquivos temporários
        
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino, exist_ok=True)
        
        # Define o caminho final do arquivo
        caminho_arquivo = os.path.join(pasta_destino, pdf_filename)

        # Salva o arquivo
        entrada.save(caminho_arquivo)

        # Verifica se o arquivo foi salvo corretamente
        if os.path.exists(caminho_arquivo) and os.path.getsize(caminho_arquivo) == 0:
            raise ValueError("O arquivo salvo está vazio.")

        caminho = caminho_arquivo
    else:
        # A entrada já é um caminho para o arquivo
        caminho = entrada
    
    if Verbose:
        print("Modo verbose ativado.")    
        if MedRobot:
            print("MedRobot está ativado.")
    
    # Realiza o preprocessamento e filtragem das páginas do PDF
    (filtered_pages, tipo_documento, custoresumo) = preprocessamento(caminho, models, Verbose=Verbose, TipoDocumento=TipoDocumento, Resumo=Resumo)        
    
    if tipo_documento == "Indeterminado":
        raise TipoDocumentoIndeterminadoException("Não foi possível determinar o tipo de documento para a Análise")
  
    try:
        if Verbose:    
            print(f"Número de páginas após pré-processamento: {len(filtered_pages)}\n")
            print(f"Tipo de Documento em Análise: {tipo_documento}\n")

        # Garante que IDs das páginas são strings para compatibilidade com ChromaDB
        ids = [str(i) for i in range(1, len(filtered_pages) + 1)]

        # Inicializa embeddings da OpenAI
        embeddings = OpenAIEmbeddings()

        # Cria índice no ChromaDB para busca vetorial
        docsearch = Chroma.from_documents(
            filtered_pages, embeddings, ids=ids, collection_metadata={"hnsw:M": 1024}
        )
        
        # Aplica o pipeline de análise apropriado
        resposta = AnalisePipeline(
            filtered_pages, docsearch, models, Verbose, MedRobot, TipoDocumento=tipo_documento, Resumo=Resumo, CustoResumo=custoresumo
        )
    
        # Apaga os IDs criados no ChromaDB, se existirem
        if docsearch and hasattr(docsearch, "_collection"):
            docsearch._collection.delete(ids=ids)
        
        return resposta
    
    except IndexError:
        print(f"Erro: Índice inválido ao analisar o arquivo {os.path.basename(caminho)}.")
        return {"error": "Você tentou acessar um índice inválido ao analisar o arquivo"}
        
    except Exception as e:
        print(f"Erro ao processar o arquivo {os.path.basename(caminho)}: {e}")
        return {"error": f"Erro ao processar o arquivo {os.path.basename(caminho)}: {e}"}


# Realiza o passo a passo da análise necessária para elaborar o relatório e recomendar ou não a aplicação da portaria
# retorna um dicionário com as informações obtidas
def AnalisePipeline(pages, docsearch, models, Verbose=False, MedRobot=True, TipoDocumento="Sentença", Resumo=True, CustoResumo=None):

    #inicialização do dicionário de resposta
    resposta = inicializa_dicionario()
    
    #armazena na resposta o resumo
    resposta["resumo"] = pages[0].page_content
    
    
    #armazena na resposta o tipo de documento identificado
    if TipoDocumento == "Decisão":
        resposta["tipo_documento"] = "Decisão Interlocutória"
    else:
        resposta["tipo_documento"] = TipoDocumento

    #Verifica se houve extinção do processo, cumprimento de sentença ou bloqueio de recursos
    regex_extincao = r"\*\*Houve a extinção do processo:\*\*\s*'?\s*(Sim|Não)\s*'?"
    regex_cumprimento_sentenca = r"\*\*Trata-se de uma decisão de cumprimento de sentença:\*\*\s*'?\s*(Sim|Não)\s*'?"
    regex_bloqueio_recursos = r"\*\*Trata-se de uma decisão de bloqueio de recursos ou contas:\*\*\s*'?\s*(Sim|Não)\s*'?"
    regex_monocratica = r"\*\*Trata-se de um documento intitulado decisão monocrática:\*\*\s*'?\s*(Sim|Não)\s*'?"

    # Buscar valores no resumo
    extincao = re.search(regex_extincao, resposta["resumo"])
    cumprimento_sentenca = re.search(regex_cumprimento_sentenca, resposta["resumo"])
    bloqueio_recursos = re.search(regex_bloqueio_recursos, resposta["resumo"])
    monocratica = re.search(regex_monocratica, resposta["resumo"])

    # Converter os resultados em booleanos
    resposta['houve_extincao'] = extincao.group(1) == "Sim" if extincao else False
    resposta['cumprimento_de_sentenca'] = cumprimento_sentenca.group(1) == "Sim" if cumprimento_sentenca else False
    resposta['bloqueio_de_recursos'] = bloqueio_recursos.group(1) == "Sim" if bloqueio_recursos else False
    resposta['monocratica'] = monocratica.group(1) == "Sim" if monocratica else False


    if TipoDocumento == "Sentença":
        
        #analisa se existe condenação por honorários na sentença
        (honor, chonor) = AnaliseHonorarios(docsearch, model=models['honorarios'], Verbose=Verbose, Resumo=Resumo)
        
        
        #analisa se existe pedido de internação em UTI
        (interna, cinterna) = AnaliseInternacao(docsearch, model=models['internacao'], Verbose=Verbose, Resumo=Resumo)
        
        print(f"Houve internação: {interna}")
        
        #analisa se existe realizacao de consultas exames ou procedimentos
        (consultas, cconsultas) = AnaliseConsultasProcedimentos(docsearch, model=models['internacao'], Verbose=Verbose, Resumo=Resumo)
        

        # Detecta (usando REGEX) se existe outros itens alem de medicamentos na sentença
        # é feita uma diferenciação entre itens proibidos e itens permitidos para aplicação da portaria
        # itens que ainda não são analisados pelo robô são tratados como proibidos, embora estejam na portaria 01/2017
        #cdoutros=0
        cdoutros=None
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
        
        #lista contendo os nomes de compostos alimentares obtidos da sentença
        (lalim, calim) = AnaliseAlimentares(docsearch, model=models['alimentares'], Verbose=Verbose, Resumo=Resumo)
        
        
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

        
        
        #preenche se houve condenação por honorários e se há outros itens além de medicamentos
        resposta['condenacao_honorarios'] = honor 
        resposta['internacao'] = interna
        resposta['possui_consulta'] = consultas
        resposta['possui_outros'] = outros
        resposta['possui_outros_proibidos'] = outrosregex_proibidos
        
        
        resposta['respeita_valor_teto'] = teto
        resposta['valor_teto'] = "R$ {:.2f}".format(total)
    
    
        #acrescenta as palavras chave encontradas.
        resposta['lista_outros'] = listaoutros
        resposta['lista_outros_proibidos'] = listaoutrosregex_proibidos
        
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
            
        
        #adiciona as informações de alimentos obtidas
        for (nome, qtd, duracao) in lalim:
            resposta['lista_compostos'].append({
            "nome": nome,
            "quantidade": qtd,
            "duracao": duracao
            })          
        
        
        #resultado da aplicação da portaria em seus 6 incisos
        
        if resposta['respeita_valor_teto'] and not resposta['condenacao_honorarios'] and not resposta['possui_outros_proibidos']:
            resposta['aplicacao_incisos'] = [False,
                (resposta['internacao'] or resposta['possui_consulta']),
                bool(resposta['lista_compostos']),
                False,
                bool(resposta['lista_outros']),
                False]
        else:
            resposta['aplicacao_incisos'] = (False, False, False, False, False, False)

        #custo total com LLMs
        soma_prompt = sum([cdoutros[0], cmeds[0], calim[0], chonor[0], CustoResumo[0], cinterna[0], cconsultas[0]])
        soma_completion = sum([cdoutros[1], cmeds[1], calim[1],  chonor[1], CustoResumo[1], cinterna[1], cconsultas[1]])
        resposta['custollm'] = CustoGpt4o(soma_prompt, soma_completion)
        resposta['tokensllm'] = (soma_prompt, soma_completion)
        
        resposta['resumo_analise'] = str(resposta) 

        if Verbose:
            exibe_dados(resposta)
    
    #Caso seja Decisão Interlocutória ou Petição Inicial
    else:
        
        #analisa se existe condenação por honorários na sentença
        (honor, chonor) = (False, (0, 0))
        
        #analisa se existe pedido de internação em UTI
        (interna, cinterna) = AnaliseInternacao(docsearch, model=models['internacao'], Verbose=Verbose, Resumo=Resumo)
        
        #analisa se existe realizacao de consultas exames ou procedimentos
        (consultas, cconsultas) = AnaliseConsultasProcedimentos(docsearch, model=models['internacao'], Verbose=Verbose, Resumo=Resumo)
        

        # Detecta (usando REGEX) se existe outros itens alem de medicamentos na sentença
        # é feita uma diferenciação entre itens proibidos e itens permitidos para aplicação da portaria
        # itens que ainda não são analisados pelo robô são tratados como proibidos, embora estejam na portaria 01/2017
        #cdoutros=0
        cdoutros=None
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
        
        
        #lista contendo os nomes de compostos alimentares obtidos da petição inicial ou decisão
        (lalim, calim) = AnaliseAlimentares(docsearch, model=models['alimentares'], Verbose=Verbose, Resumo=Resumo)

        
        #lista contendo os nomes de medicamentos obtidos da petição inicial ou decisão
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

        
        
        #preenche se houve condenação por honorários e se há outros itens além de medicamentos
        resposta['condenacao_honorarios'] = honor 
        resposta['internacao'] = interna
        resposta['possui_consulta'] = consultas
        resposta['possui_outros'] = outros
        resposta['possui_outros_proibidos'] = outrosregex_proibidos
        
        
        resposta['respeita_valor_teto'] = teto
        resposta['valor_teto'] = "R$ {:.2f}".format(total)
    
    
        #acrescenta as palavras chave encontradas.
        resposta['lista_outros'] = listaoutros
        resposta['lista_outros_proibidos'] = listaoutrosregex_proibidos
        
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
        
        #adiciona as informações de alimentos obtidas
        for (nome, qtd, duracao) in lalim:
            resposta['lista_compostos'].append({
            "nome": nome,
            "quantidade": qtd,
            "duracao": duracao
            })    
        
        #resultado da aplicação da portaria em seus 6 incisos
        
        if not resposta['possui_outros_proibidos']:
            resposta['aplicacao_incisos'] = [False,
                (resposta['internacao'] or resposta['possui_consulta']),
                bool(resposta['lista_compostos']),
                False,
                bool(resposta['lista_outros']),
                False]
        else:
            resposta['aplicacao_incisos'] = (False, False, False, False, False, False)


        #custo total com LLMs
        soma_prompt = sum([cdoutros[0], cmeds[0], calim[0], chonor[0], CustoResumo[0], cinterna[0],cconsultas[0]])
        soma_completion = sum([cdoutros[1], cmeds[1], calim[1], chonor[1], CustoResumo[1], cinterna[1],cconsultas[1]])
        resposta['custollm'] = CustoGpt4o(soma_prompt, soma_completion)
        resposta['tokensllm'] = (soma_prompt, soma_completion)
        
        exibe_dados(resposta)
        
        resposta['resumo_analise'] = str(resposta)
        
        

        if Verbose:
            exibe_dados(resposta)
            #print(f"Custo com LLMs para Resumo: {"$ {:.4f}".format(CustoGpt4o(CustoResumo[0],CustoResumo[1]))}")
            #print(f"Custo com LLMs para extração de medicamentos: {"$ {:.4f}".format(CustoGpt4o(cmeds[0],cmeds[1]))}")
            #print(f"Custo com LLMs para detecção de outros itens: {"$ {:.4f}".format(CustoGpt4o(cdoutros[0],cdoutros[1]))}")
            #print(f"Custo com LLMs para detecção de condenação por honorários: {"$ {:.4f}".format(CustoGpt4o(chonor[0],chonor[1]))}")
            #print(f"Custo com LLMs para detecção de internação: {"$ {:.4f}".format(CustoGpt4o(cinterna[0],cinterna[1]))}")
            #print(f"Custo total com LLMs: {"$ {:.4f}".format(resposta['custollm'])}")
    
    return resposta


#Função para exibição de uma resposta na saída padrão
def exibe_dados(dados):
    print("Resumo da Decisão Judicial:\n")
    print(f"Tipo de documento: {dados['tipo_documento']}")
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
    print(f"Tokens Total dos LLMs: {dados['tokensllm']}")


def CustoGpt4o(prompt_tokens, completion_tokens):
    # Custos durante o horário de pico
    custo_input = 5.00 / 1_000_000
    custo_output = 15.00 / 1_000_000
    
    # Calculando o custo
    custo_pico = (prompt_tokens * custo_input) + (completion_tokens * custo_output)
    
    return custo_pico




