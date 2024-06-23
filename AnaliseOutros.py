import re

#Recebe um conjunto de páginas e verifica se ocorre alguma das palavras proibitivas
def AnaliseOutros(pages, Verbose=False):
    
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

