
TEMPLATE_SENTENCA_UNIFICADA = {
    "header": "# Modelo para elaboração de sentença judicial sobre concessão de cirurgias, exames ou consultas médicas.",
    "instructions": [
        "Este template unificado abrange sentenças para concessão de cirurgias, exames e consultas médicas.",
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Sentença' refere-se à primeira seção da sentença.",
        "Identifique automaticamente o tipo de sentença com base nos dados fornecidos e ajuste o texto conforme o contexto.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore um despacho a respeito de uma sentença para concessão de cirurgias, exames ou consultas médicas, "
                "baseando-se nos dados fornecidos e na estrutura descrita abaixo. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura da Sentença:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Julgue procedente ou parcialmente procedente o pleito autoral com resolução de mérito.
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA."
        3. Especificação:
           - Ajuste conforme o tipo de sentença:
             - *Para cirurgias*: Informe o procedimento a ser realizado e quaisquer detalhes relevantes.
               - Exemplo: "REALIZAÇÃO DE [nome do procedimento cirúrgico]."
             - *Para exames*: Informe os exames a serem realizados e quaisquer detalhes relevantes.
               - Exemplo: "DETERMINA-SE O FORNECIMENTO DE EXAMES LABORATORIAIS, [informar os exames encontrados]."
             - *Para consultas*: Especificar a especialidade médica e qualquer detalhe relevante.
               - Exemplo: "CONSULTA MÉDICA [especialidade médica]."
        4. Danos Morais:
           - Indicar se há ou não pedido de condenação por danos morais.
           - Exemplo: "AUSÊNCIA DE PEDIDO DE DANOS MORAIS."
        5. Condenação por honorários:
           - Verificar se existe condenação por honorários, e em caso positivo seguir conforme o exemplo 1, caso contrário, seguir o Exemplo 2.
           - Exemplo 1: "Houve condenação por honorários sucumbenciais"
           - Exemplo 2: "Não houve condenação por sucumbenciais"
        5. Aplicação de Normativas Específicas:
           - Verificar se existe aplicação de portaria, caso seja aplicável ao caso, seguir conforme o exemplo 1, caso não, seguir o Exemplo 2.
           - Exemplo 1: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II."
           - Exemplo 2: "NÃO APLICAÇÃO DA PORTARIA 01/2017."
        6. Direcionamentos Finais:
           - Se existe aplicação de portaria, seguir conforme o exemplo 1, caso não, seguir o Exemplo 2.
           - Exemplo 1: "VERIFICAR A NECESSIDADE DE ENCAMINHAR OFÍCIO À SESA, E APÓS, ARQUIVAR A PASTA."
           - Exemplo 2: "Encaminhe-se para análise e elaboração de contestação e recurso."
        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Detecte automaticamente o tipo de sentença com base nos dados fornecidos e ajuste o texto conforme o tipo identificado.
        - Utilize o modelo acima como base para criar sentenças adequadas ao caso apresentado.
        """
            ]
        }
    }
}


'''
TEMPLATE_sentenca_CONSULTAS_EXAMES_PROCEDIMENTOS = {
    "header": "# Modelo para elaboração de despacho judicial para concessão de consultas, exames, procedimentos e tratamentos multidisciplinares.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção do despacho.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore um despacho judicial para concessão de consultas, exames, procedimentos (cirúrgicos ou não) "
                "e tratamentos multidisciplinares, baseando-se nas informações fornecidas no contexto. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura do Despacho:
        1. Identificação do Despacho:
           Inicie com a abreviação "R.H." para indicar a abertura do despacho.
        2. Sentença e Mérito:
           - Avalie se há sentença do mérito e decisão procedente sobre o pleito autoral.
           - Descreva a determinação da sentença.
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO."
        3. Determinação de Consultas, Exames e Procedimentos:
           - Indique o tipo de consulta, exame ou procedimento requerido, incluindo cirúrgicos ou não.
           - Exemplo: "DETERMINA A REALIZAÇÃO DE EXAME DE RESSONÂNCIA MAGNÉTICA E CONSULTA COM ESPECIALISTA."
        4. Tratamentos Multidisciplinares:
           - Caso aplicável, indique que foi solicitado tratamento multidisciplinar.
           - Exemplo: "DETERMINA O INÍCIO DE TRATAMENTO MULTIDISCIPLINAR INCLUINDO SESSÕES DE FONOAUDIOLOGIA E PILATES."
        5. Danos Morais:
           - Indique se há ou não condenação em danos morais.
           - Exemplo: "AUSÊNCIA DE CONDENAÇÃO EM DANOS MORAIS."
        6. Custas e Honorários:
           - Especifique, de acordo com os dados de contexto, a existência ou não de custas e honorários.
           - Exemplo Negativo: "SEM CUSTAS NEM HONORÁRIOS."
           - Exemplo Positivo: "HOUVE CONDENAÇÂO POR HONORÁRIOS."
        7. Aplicação de Normativas Específicas:
           - Inclua que aqui, de acordo com os dados de contexto, se foi verificada a aplicação da PORTARIA 01/2017, ART. 1º, artigo II. Sem justificar.
           - Exemplo positivo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II."
           - Exemplo negativo: "NÃO SE APLICA A PORTARIA 01/2017."
        8. Direcionamentos Finais:
           - Apenas escrever: "VERIFICAR A NECESSIDADE DE ENCAMINHAR OFÍCIO À SESA, E APÓS, ARQUIVAR A PASTA."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize uma linguagem formal e técnica adequada para um contexto jurídico.
        """
            ]
        }
    }
}
'''


TEMPLATE_MEDICAMENTO = {
    "header": "# Modelo para elaboração de despacho.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção. Exemplo: '1. Identificação do Tipo de Decisão' significa a primeira seção.",
        "Cada número seguido de um ponto é uma subseção. Exemplo: '2.1 Objeto da Decisão' significa a primeira subseção da seção 2.",
        "Implemente subsubseções se necessário."
    ],
    "template": {
        "Texto Completo": {
            "description": "Crie um despacho judicial para a concessão de medicamentos, baseando-se nos dados fornecidos e nos  seguintes exemplos fornecidos de decisões anteriores, o texto não deve ter tópicos e dever ser fornecido em um único parágrafo.O texto não pode vir com todas as letras em maíusculo.",
            "elements": [
                """Exemplos:
                        1. R.H. TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA. FORNECIMENTO DOS MEDICAMENTOS QUETIAPINA 100MG, PRAMIPEXOL 0,75MG E CARBAMAZEPINA CR 200 MG AO PACIENTE. FÁRMACOS REGISTRADOS NA ANVISA, CUJO CUSTO ANUAL NÃO SUPERA O TETO DE 60 SALÁRIOS-MÍNIMOS (CERCA DE R$7.500,00). AUSÊNCIA DE DANO MORAL. LAUDO PÚBLICO. SEM CUSTAS NEM HONORÁRIOS. CONFORME PRECEDENTE DESTA SETORIAL (0202503-31.2022.8.06.0055), FOI CONCEDIDA A DISPENSA DE APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO PELO GABINETE NESSES CASOS EM QUE O CUSTO DO TRATAMENTO ANUAL ENQUADRA-SE NO TETO DOS JUIZADOS DA FAZENDA PÚBLICA. APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, I. OPINO PELA NÃO INTERPOSIÇÃO DO RECURSO EM TESE CABÍVEL. OFICIAR A SESA PARA CONHECIMENTO DE SENTENÇA E COMPROVAR CUMPRIMENTO DIRETAMENTE NOS AUTOS. APÓS, CONFORME ORIENTAÇÃO DA CHEFIA, ARQUIVAR A PASTA.
                        2. R.H. TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA. FORNECIMENTO DO MEDICAMENTO DULOXETINA. CUSTO ANUAL DO TRATAMENTO: CERCA DE R$ 1.300,00 (ABAIXO DO TETO DO RPV). FÁRMACO REGISTRADO NA ANVISA. AUSÊNCIA DE DANO MORAL. LAUDO PÚBLICO. SEM CUSTAS. HONORÁRIOS EXCLUSIVAMENTE EM DESFAVOR DO MUNICÍPIO. MEDICAÇÃO COM CUSTO ANUAL INFERIOR AO VALOR ESTIPULADO PARA EXPEDIÇÃO DE REQUISIÇÃO DE PEQUENO VALOR. APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, I. EMBORA SEJA CABÍVEL A INTERPOSIÇÃO DE RECURSO FUNDADO NO TEMA 793, OPINO PELA NÃO INTERPOSIÇÃO EM RAZÃO DO BAIXO CUSTO DO MEDICAMENTO PLEITEADO. OFICIAR A SESA PARA CONHECIMENTO DE SENTENÇA E COMPROVAR CUMPRIMENTO DIRETAMENTE NOS AUTOS. APÓS, AO ARQUIVO CONFORME ORIENTAÇÃO DO PROCURADOR RESPONSÁVEL.
                        3. R.H. TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA. FORNECIMENTO DO MEDICAMENTO XARELTO À PACIENTE. FÁRMACO REGISTRADO NA ANVISA. AUSÊNCIA DE DANO MORAL. SEM CUSTAS NEM HONORÁRIOS. APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, I. OPINO PELA NÃO INTERPOSIÇÃO DO RECURSO EM TESE CABÍVEL. OFICIAR A SESA PARA CONHECIMENTO DE SENTENÇA E COMPROVAR CUMPRIMENTO DIRETAMENTE NOS AUTOS. APÓS, TRAMITAR À CHEFIA.
                        4. R.H. TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA. FORNECIMENTO DO MEDICAMENTO RITUXIMABE. FÁRMACO REGISTRADO NA ANVISA, MAS NÃO PREVISTO NA RENAME. CUSTO ANUAL DO TRATAMENTO INFERIOR AO TETO DE 60 SALÁRIOS MÍNIMOS, CONFORME RELATÓRIO APRESENTADO PELO NATJUS - ID 62701067. AUSÊNCIA DE DANO MORAL. LAUDO PÚBLICO. SEM CUSTAS E SEM HONORÁRIOS (AUSÊNCIA DE FIXAÇÃO). APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, I. EMBORA SEJA CABÍVEL A INTERPOSIÇÃO DE RECURSO FUNDADO NO TEMA 793, OPINO PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO EM RAZÃO DO BAIXO CUSTO DO MEDICAMENTO PLEITEADO, NOS TERMOS DO PRECEDENTE Nº 0202503-31.2022.8.06.0055. DISPENSA DE ATUAÇÃO PARA MEDICAMENTOS NÃO INCORPORADOS COM CUSTO ANUAL NO PATAMAR DE 60 SALÁRIOS MÍNIMOS. OFICIAR A SESA PARA CONHECER SENTENÇA E COMPROVAR CUMPRIMENTO DIRETAMENTE NOS AUTOS. APÓS, AO ARQUIVO, CONFORME ORIENTAÇÃO DA CHEFIA.


                        Informaçoes que devem estar no despacho a ser gerado:
                        1. Identificação do Despacho
                        2. Decisão sobre o Pleito
                        3. Especificação do Medicamento
                        4. Danos Morais
                        6. Aplicação de Normativas Específicas
                        7. Direcionamentos Finais

                        Utilize uma linguagem formal e técnica adequada para um contexto jurídico, incorporando os elementos e o estilo dos exemplos dados para criar um novo despacho judicial simulado."""
            ]
        }
    }
}


TEMPLATE_SENTENCA_MEDICAMENTO = {
    "header": "# Modelo para elaboração de sentença judicial sobre fornecimento de medicamentos.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Sentença' refere-se à primeira seção da sentença.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Sentença' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma sentença judicial para concessão de medicamentos, "
                "baseando-se nos dados fornecidos e na estrutura descrita abaixo. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo. Não fornecer nomes das pessoas envolvidas."
            ),
            "elements": [
                """
        Estrutura da Sentença:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Julgue procedente ou improcedente o pleito autoral com resolução de mérito.
           - Ratifique ou não a decisão antecipatória de tutela previamente concedida.
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA."
        3. Especificação do Medicamento:
           - Informe o medicamento e detalhes relevantes.
           - Exemplo: "PARA O FORNECIMENTO DO MEDICAMENTO QUETIAPINA 100MG, REGISTRADO NA ANVISA."
        4. Aplicação de Normativas Específicas:
           - Informar que a portaria não é aplicável nesse caso.
           - Exemplo: "NÃO SE APLICA A PORTARIA 01/2017."
        5. Danos Morais:
           - Indicar se há ou não pedido de indenização por danos morais.
           - Exemplo: "AUSÊNCIA DE DANO MORAL."
        6. Direcionamentos Processuais:
           - Definir medidas processuais, como não interposição de recurso ou direcionamento para órgão responsável.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE RECURSO."
        7. Direcionamentos Finais:
           - Encerrar o processo com as ações necessárias, conforme o texto de exemplo.
           - Exemplo: "ARQUIVAR A PASTA."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize o modelo acima como base para criar sentenças adequadas ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_SENTENCA_CONSULTA = {
    "header": "# Modelo para elaboração de sentença judicial sobre realização de consultas médicas.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Sentença' refere-se à primeira seção da sentença.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Sentença' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma sentença judicial para concessão de consultas médicas, "
                "baseando-se nos dados fornecidos e na estrutura descrita abaixo. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo.  Não fornecer nomes das pessoas envolvidas."
            ),
            "elements": [
                """
        Estrutura da Sentença:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Julgue procedente ou parcialmente procedente o pleito autoral com resolução de mérito.
           - Especificar a especialidade médica.
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, DETERMINANDO A REALIZAÇÃO DE CONSULTA MÉDICA COM [ESPECIALIDADE]."
        3. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 02/2018, ART. 3º, INCISO IV."
        4. Danos Morais:
           - Indicar se há ou não pedido de indenização por danos morais, conforme exemplo.
           - Exemplo: "SEM CONDENAÇÃO EM DANOS MORAIS."
        5. Direcionamentos Processuais:
           - Definir medidas processuais, como não interposição de recurso ou direcionamento para órgãos responsáveis.
           - Exemplo: "RECOMENDA-SE A NÃO INTERPOSIÇÃO DE RECURSO."
        6. Direcionamentos Finais:
           - Encerrar o processo com as ações necessárias, conforme o texto de exemplo.
           - Exemplo: "ARQUIVAR O PROCESSO."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize o modelo acima como base para criar sentenças adequadas ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_SENTENCA_INTERNACAO = {
    "header": "# Modelo para elaboração de sentença judicial sobre concessão de internação hospitalar.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Sentença' refere-se à primeira seção da sentença.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Sentença' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma sentença judicial para concessão de internação hospitalar, "
                "baseando-se nos dados fornecidos e na estrutura descrita abaixo. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo. Não fornecer nomes das pessoas envolvidas."
            ),
            "elements": [
                """
        Estrutura da Sentença:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Julgue procedente ou parcialmente procedente o pleito autoral com resolução de mérito.
           - Informe o tipo de internação ou leito determinado 
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, CONFIRMANDO A TUTELA ANTECIPATÓRIA PARA [tipo de internação]."
        3. Danos Morais:
           - Indicar se há ou não pedido de condenação por danos morais.
           - Exemplo: "SEM CONDENAÇÃO EM DANOS MORAIS."
        4. Custas e Honorários:
           - Indicar se há isenção ou obrigação de pagamento de custas e honorários.
           - Exemplo: "SEM CUSTAS NEM HONORÁRIOS ADVOCATÍCIOS."
        5. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, INCISO II."
        6. Direcionamentos Finais:
           - Encerrar o processo com as ações necessárias.
           - Exemplo: "ARQUIVAR O PROCESSO."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize o modelo acima como base para criar sentenças adequadas ao caso apresentado.
        """
            ]
        }
    }
}

TEMPLATE_SENTENCA_EXAMES = {
    "header": "# Modelo para elaboração de sentença judicial sobre concessão de exames médicos.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Sentença' refere-se à primeira seção da sentença.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Sentença' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma sentença judicial para concessão de exames médicos, "
                "baseando-se nos dados fornecidos e na estrutura descrita abaixo. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo. Não fornecer nomes das pessoas envolvidas."
            ),
            "elements": [
                """
        Estrutura da Sentença:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Julgue procedente ou parcialmente procedente o pleito autoral com resolução de mérito.
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA."
        3. Especificação dos Exames Médicos:
           - Informe os exames a serem realizados e quaisquer detalhes relevantes.
           - Exemplo: "DETERMINA-SE O FORNECIMENTO DE EXAMES LABORATORIAIS, INCLUINDO HEMOGRAMA COMPLETO E FUNÇÃO RENAL."
        4. Danos Morais:
           - Indicar se há ou não pedido de condenação por danos morais.
           - Exemplo: "AUSÊNCIA DE DANO MORAL."
        5. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, I."
        6. Direcionamentos Finais:
           - Definir medidas processuais, como não interposição de recurso ou direcionamento para órgãos responsáveis.
           - Exemplo: "ARQUIVAR O PROCESSO."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize o modelo acima como base para criar sentenças adequadas ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_SENTENCA_CIRURGIA = {
    "header": "# Modelo para elaboração de sentença judicial sobre concessão de cirurgias.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Sentença' refere-se à primeira seção da sentença.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Sentença' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma sentença judicial para concessão de cirurgias, "
                "baseando-se nos dados fornecidos e na estrutura descrita abaixo. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo. Não fornecer nomes das pessoas envolvidas."
            ),
            "elements": [
                """
        Estrutura da Sentença:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Julgue procedente ou parcialmente procedente o pleito autoral com resolução de mérito.
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO, RATIFICANDO A DECISÃO ANTECIPATÓRIA DE TUTELA ANTERIORMENTE CONCEDIDA."
        3. Especificação da Cirurgia:
           - Informe a cirurgia a ser realizada e quaisquer detalhes relevantes.
           - Exemplo: "REALIZAÇÃO DE CIRURGIA BARIÁTRICA."
        4. Danos Morais:
           - Indicar se há ou não pedido de condenação por danos morais.
           - Exemplo: "AUSÊNCIA DE PEDIDO DE DANOS MORAIS."
        5. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II."
        6. Direcionamentos Finais:
           - Definir medidas processuais, como arquivamento ou outras providências necessárias.
           - Exemplo: "ARQUIVAR O PROCESSO."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize o modelo acima como base para criar sentenças adequadas ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_DECISAO_INTERNACAO = {
    "header": "# Modelo para elaboração de decisão interlocutória sobre fornecimento de leitos de UTI.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção da decisão.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma decisão interlocutória para concessão de internação hospitalar, "
                "baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura da Decisão:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Mencione a concessão da antecipação dos efeitos da tutela. Não precisa justificar, nem mesmo mostrar processos anteriores. Não mencionar nada sobre laudos.
           - Exemplo: "TRATA-SE DE DECISÃO INTERLOCUTÓRIA CONCEDENDO A ANTECIPAÇÃO DOS EFEITOS DA TUTELA JURISDICIONAL PARA DETERMINAR O FORNECIMENTO DE LEITO DE UTI."
        3. Detalhes do Caso:
           - Informe o tipo de prioridade (I, II ou III), a ausência ou presença de pedido de condenação em danos morais.
        4. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II C/C ART. 2º I E II."
        5. Direcionamentos Processuais:
           - Sugira medidas processuais como não interposição de defesa/recurso.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO."
        6. Direcionamentos Finais:
           - Encerrar o processo, conforme o texto de exemplo.
           - Exemplo: "ARQUIVAR A PASTA"

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize exemplos como modelo para criar novos despachos adequados ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_DECISAO_MEDICAMENTO = {
    "header": "# Modelo para elaboração de decisão interlocutória sobre fornecimento de medicamentos.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção da decisão.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma decisão interlocutória para concessão de medicamentos, "
                "baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura da Decisão:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Mencione a concessão da antecipação dos efeitos da tutela para fornecimento de medicamentos. Não precisa justificar ou mencionar processos anteriores ou laudos.
           - Informe o medicamento e quais são eles. Não precisa informar valores.
           - Exemplo: "TRATA-SE DE DECISÃO INTERLOCUTÓRIA CONCEDENDO A ANTECIPAÇÃO DOS EFEITOS DA TUTELA JURISDICIONAL PARA DETERMINAR O FORNECIMENTO DE MEDICAMENTO [nome do medicamento]."
        3. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, I C/C ART. 2º, I E II."
        4. Danos Morais:
           - Indicar se há ou não pedido de condenação por danos morais.
           - Exemplo: "AUSÊNCIA DE DANO MORAL."
        5. Direcionamentos Processuais:
           - Sugira medidas processuais como não interposição de defesa/recurso.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO."
        6. Direcionamentos Finais:
           - Encerrar o processo, conforme o texto de exemplo.
           - Exemplo: "ARQUIVAR A PASTA."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize exemplos como modelo para criar novos despachos adequados ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_DECISAO_EXAME = {
    "header": "# Modelo para elaboração de decisão interlocutória sobre realização de exames médicos.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção da decisão.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma decisão interlocutória para a realização de exames médicos, "
                "baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura da Decisão:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Mencione a concessão da antecipação dos efeitos da tutela para a realização dos exames médicos requeridos. Não precisa justificar ou mencionar processos anteriores ou laudos.
           - Informe os exames a serem realizados e quaisquer detalhes relevantes.
           - Exemplo: "TRATA-SE DE DECISÃO INTERLOCUTÓRIA CONCEDENDO A ANTECIPAÇÃO DOS EFEITOS DA TUTELA JURISDICIONAL PARA DETERMINAR A REALIZAÇÃO De EXAME [especificar o exame]."
        3. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II C/C ART. 2º, I E II."
        4. Danos Morais:
           - Indicar se há ou não pedido de indenização por danos morais.
           - Exemplo: "AUSÊNCIA DE PEDIDO DE INDENIZAÇÃO POR DANOS MORAIS."
        5. Direcionamentos Processuais:
           - Sugira medidas processuais como não interposição de defesa/recurso.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO."
        6. Direcionamentos Finais:
           - Encerrar o processo, conforme o texto de exemplo.
           - Exemplo: "ARQUIVAR A PASTA."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize exemplos como modelo para criar novos despachos adequados ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_DECISAO_CIRURGIA = {
    "header": "# Modelo para elaboração de decisão interlocutória sobre realização de cirurgia.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção da decisão.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma decisão interlocutória para a realização de cirurgia, "
                "baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura da Decisão:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Mencione a concessão ou indeferimento da antecipação dos efeitos da tutela para realização de cirurgia. Não precisa justificar ou mencionar processos anteriores ou laudos.
           - Informe o procedimento específico e quaisquer detalhes relevantes.
           - Exemplo: "TRATA-SE DE DECISÃO INTERLOCUTÓRIA CONCEDENDO A ANTECIPAÇÃO DOS EFEITOS DA TUTELA JURISDICIONAL PARA DETERMINAR A REALIZAÇÃO DE CIRURGIA [NOME DA CIRURGIA]."
        3. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II C/C ART. 2º, I E II."
        4. Danos Morais:
           - Indicar se há ou não pedido de indenização por danos morais.
           - Exemplo: "AUSÊNCIA DE PEDIDO DE INDENIZAÇÃO POR DANOS MORAIS."
        5. Direcionamentos Processuais:
           - Sugira medidas processuais como não interposição de defesa/recurso.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO."
        6. Direcionamentos Finais:
           - Encerrar o processo, conforme o texto de exemplo.
           - Exemplo: "ARQUIVAR A PASTA."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize exemplos como modelo para criar novos despachos adequados ao caso apresentado.
        """
            ]
        }
    }
}

TEMPLATE_DECISAO_CONSULTA = {
    "header": "# Modelo para elaboração de decisão interlocutória sobre realização de consultas médicas.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção da decisão.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma decisão interlocutória para a realização de consultas médicas, "
                "baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura da Decisão:
        1. Identificação do Despacho:
           - Inicie com "R.H.".
        2. Decisão sobre o Pleito:
           - Mencione a concessão da antecipação dos efeitos da tutela para realização da consulta médica solicitada. Não precisa justificar ou mencionar processos anteriores ou laudos.
           - Informe a especialidade da consulta e qualquer detalhe adicional relevante.
           - Exemplo: "TRATA-SE DE DECISÃO INTERLOCUTÓRIA CONCEDENDO A ANTECIPAÇÃO DOS EFEITOS DA TUTELA JURISDICIONAL PARA DETERMINAR A REALIZAÇÃO DE CONSULTA MÉDICA [CONSULTA COM NEUROLOGISTA OFERECIDA PELO SUS]."
        3. Aplicação de Normativas Específicas:
           - Informar portaria aplicável ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II C/C ART. 2º, I E II."
        4. Danos Morais:
           - Indicar se há ou não pedido de indenização por danos morais.
           - Exemplo: "AUSÊNCIA DE PEDIDO DE INDENIZAÇÃO POR DANOS MORAIS."
        5. Direcionamentos Processuais:
           - Sugira medidas processuais como não interposição de defesa/recurso.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO."
        6. Direcionamentos Finais:
           - Encerrar o processo, conforme o texto de exemplo.
           - Exemplo: "ARQUIVAR A PASTA."

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize exemplos como modelo para criar novos despachos adequados ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_DECISAO_INTERNACAO_Semportaria = {
    "header": "# Modelo para elaboração de decisão interlocutória sobre fornecimento de leitos de UTI.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção da decisão.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma decisão interlocutória para concessão de internação hospitalar, "
                "baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo. Não se deve mencionar o nome de nenhuma pessoa envolvida, ao longo do texto."
            ),
            "elements": [
                """
        Estrutura da Decisão:
        
        1. Identificação do Despacho:
           - Inicie com "R.H." ou diretamente com a frase "TRATA-SE DE DECISÃO INTERLOCUTÓRIA..."
        2. Decisão sobre o Pleito:
           - Mencione a concessão da antecipação dos efeitos da tutela e o objetivo da decisão.
           - Exemplo: "TRATA-SE DE DECISÃO INTERLOCUTÓRIA CONCEDENDO A ANTECIPAÇÃO DOS EFEITOS DA TUTELA JURISDICIONAL PARA DETERMINAR O FORNECIMENTO DE LEITO DE UTI."
        3. Detalhes do Caso:
           - Informe o tipo de prioridade (I, II ou III), a ausência ou presença de pedido de condenação em danos morais.
           - Exemplo: "AUSÊNCIA DE PEDIDO DE CONDENAÇÃO EM DANOS MORAIS."
        3. Direcionamentos Processuais:
           - Sugira medidas processuais como não interposição de defesa/recurso e destinação do processo.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO."
        4. Aplicação de portaria:
            -Escrever que aqui não se tem aplicação da portaria. Escrever portanto conforme exemplo.
            - Exemplo: "Não se aplica a portaria 01/2017."
        5. Direcionamentos Finais:
           - Determine ações de encerramento ou encaminhamento do processo.
           - Exemplo: Encaminhe-se para análise e elaboração de contestação e recurso."

        Orientações Gerais:
        
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize uma linguagem formal e técnica adequada para um contexto jurídico.
        """
            ]
        }
    }
}


TEMPLATE_sentenca_INTERNACAO_semportaria = {
    "header": "# Modelo para elaboração de despacho judicial para concessão de internação hospitalar.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção do despacho.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore um despacho judicial para concessão de internação hospitalar, "
                "baseando-se nos dados fornecidos e em exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo.Não se deve mencionar o nome de nenhuma pessoa envolvida, ao longo do texto."
            ),
            "elements": [
                """
        Estrutura do Despacho:
        1. Identificação do Despacho:
           Inicie com a abreviação "R.H." para indicar a abertura do despacho.
        2. Sentença e Mérito:
           - Avalie se há sentença do mérito e decisão procedente sobre o pleito autoral.
           - Descrever a determinação da sentença.
           - Não é necessário mencionar a questao de ratificar a decisao antecipatoria de tutela
           - Exemplo: "TRATA-SE DE SENTENÇA JULGANDO PROCEDENTE O PLEITO AUTORAL, COM RESOLUÇÃO DO MÉRITO."
        3. Determinação da Internação:
           - Caso explicitado, informe o tipo de leito ou internação. 
           - Não há necessidade de mencioanar medicamentos
           - Exemplo: "DETERMINA A INTERNAÇÃO EM LEITO HOSPITALAR TERCIÁRIO."
        4. Danos Morais:
           - Indique se há ou não condenação em danos morais.
           - Exemplo: "AUSÊNCIA DE CONDENAÇÃO EM DANOS MORAIS."
        5. Custas e Honorários:
           - Especifique a existência ou não de custas e honorários.
           - Exemplo: "SEM CUSTAS NEM HONORÁRIOS."
        6. Aplicação de portaria:
            - Escrever que aqui não se tem aplicação da portaria. Escrever portanto conforme exemplo.
            - Exemplo: "Não se aplica a portaria 01/2017."
        7. Direcionamentos Finais:
           - Apenas escrever: "Encaminhe-se para análise e elaboração de contestação e recurso."
        

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize uma linguagem formal e técnica adequada para um contexto jurídico.
        """
            ]
        }
    }
}

TEMPLATE_DECISAO_INTERNACAO3 = {
    "header": "# Modelo para elaboração de decisão interlocutória sobre fornecimento de leitos de UTI.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção principal. Exemplo: '1. Identificação do Tipo de Decisão' refere-se à primeira seção da decisão.",
        "Cada número seguido de um ponto refere-se a uma subseção. Exemplo: '2.1 Objeto da Decisão' indica a primeira subseção da seção 2.",
        "Use subsubseções quando necessário para detalhar informações complementares.",
        "Siga rigorosamente a estrutura apresentada, mantendo o tom formal e técnico esperado em um contexto jurídico."
    ],
    "template": {
        "Texto Completo": {
            "description": (
                "Elabore uma decisão interlocutória para concessão de internação hospitalar, "
                "baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. "
                "O texto deve ser apresentado em um único parágrafo, sem tópicos enumerados. "
                "Evite o uso de todas as letras em maiúsculo."
            ),
            "elements": [
                """
        Estrutura da Decisão:
        1. Identificação do Despacho:
           - Inicie com "R.H." ou diretamente com a frase "TRATA-SE DE DECISÃO INTERLOCUTÓRIA..."
        2. Decisão sobre o Pleito:
           - Mencione a concessão da antecipação dos efeitos da tutela e o objetivo da decisão.
           - Exemplo: "TRATA-SE DE DECISÃO INTERLOCUTÓRIA CONCEDENDO A ANTECIPAÇÃO DOS EFEITOS DA TUTELA JURISDICIONAL PARA DETERMINAR O FORNECIMENTO DE LEITO DE UTI."
        3. Detalhes do Caso:
           - Informe o tipo de prioridade (I, II ou III), a ausência ou presença de pedido de condenação em danos morais e o local do laudo médico.
           - Exemplo: "AUSÊNCIA DE PEDIDO DE CONDENAÇÃO EM DANOS MORAIS."
        4. Aplicação de Normativas Específicas:
           - Inclua referência a normativas ou portarias aplicáveis ao caso.
           - Exemplo: "APLICAÇÃO DA PORTARIA 01/2017, ART. 1º, II C/C ART. 2º I E II."
        5. Direcionamentos Processuais:
           - Sugira medidas processuais como não interposição de defesa/recurso e destinação do processo.
           - Exemplo: "OPINA-SE PELA NÃO APRESENTAÇÃO/INTERPOSIÇÃO DE DEFESA/RECURSO."
        6. Direcionamentos Finais:
           - Apenas escrever: "VERIFICAR A NECESSIDADE DE ENCAMINHAR OFÍCIO À SESA, E APÓS, ARQUIVAR A PASTA"

        Orientações Gerais:
        - Redija o texto utilizando uma linguagem formal e técnica, preservando a clareza e coerência.
        - Utilize exemplos como modelo para criar novos despachos adequados ao caso apresentado.
        """
            ]
        }
    }
}


TEMPLATE_SENTENCA_COMPOSTO_ALIMENTAR= {
    "header": "# Modelo para elaboração de despacho para concessão de composto alimentar.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção. Exemplo: '1. Identificação do Tipo de Decisão' significa a primeira seção.",
        "Cada número seguido de um ponto é uma subseção. Exemplo: '2.1 Objeto da Decisão' significa a primeira subseção da seção 2.",
        "Implemente subsubseções se necessário."
    ],
    "template": {
        "Texto Completo": {
            "description": "Crie um despacho judicial para a concessão de composto alimentar, baseando-se nos dados fornecidos e nos exemplos de decisões anteriores. O texto deve ser estruturado em um único parágrafo, sem todas as letras em maiúsculo.",
            "elements": [
                """Exemplos:
1. R.H. Trata-se de sentença julgando procedente o pleito autoral, com resolução do mérito, ratificando a decisão antecipatória de tutela anteriormente concedida. Fornecimento de composto alimentar de comercialização autorizada no país. Ausência de apreciação do pedido de dano moral. Sem custas nem honorários. Laudo público. Aplicação da Portaria 01/2017, art. 1º, III. Opino pela não interposição do recurso em tese cabível. Oficiar a SESA para conhecimento de sentença e comprovar cumprimento diretamente nos autos. Após, à chefia para ratificação e arquivar a pasta.
                
2. R.H. Trata-se de sentença julgando procedente o pleito autoral, com resolução do mérito, ratificando a decisão antecipatória de tutela anteriormente concedida. Fornecimento de composto alimentar de comercialização autorizada no país. Ausência de dano moral. Sem custas nem honorários. Aplicação da Portaria 01/2017, art. 1º, III. Opino pela não interposição do recurso em tese cabível.

3. R.H. Trata-se de sentença julgando procedente o pleito autoral, com resolução do mérito, ratificando a decisão antecipatória de tutela anteriormente concedida. Fornecimento de composto alimentar de comercialização autorizada no país. Ausência de dano moral. Sem custas nem honorários. Laudo público. Aplicação da Portaria 01/2017, art. 1º, III. Opino pela não interposição do recurso em tese cabível. Oficiar a SESA para conhecimento de sentença e comprovar cumprimento diretamente nos autos. Após, tendo em vista anterior ratificação, arquivar.

4. R.H. Trata-se de sentença julgando procedente o pleito autoral, com resolução do mérito, ratificando a decisão antecipatória de tutela anteriormente concedida. Fornecimento de composto alimentar, materiais para administrar a dieta e insumos de atenção básica (fraldas descartáveis). Ausência de pedido de danos morais. Aplicação da Portaria 01/2017, art. 1º, III e V. Sem honorários. Opino pela não interposição do recurso em tese cabível. Arquivar a pasta.

Informaçoes que devem estar no despacho a ser gerado:
1. Identificação do Despacho: "Número do processo, natureza da ação, e contexto jurídico.",
2. Decisão sobre o Pleito: "Conclusão favorável ou desfavorável ao autor, com base em provas e fundamentação legal.",
3. Especificação do Composto Alimentar: "Nome, fabricante, e registros oficiais que comprovem a autorização para comercialização.",
4. Danos Morais: "Indicação da existência ou ausência de pedidos de danos morais, com justificativa.",
6. Aplicação de Normativas Específicas: "Normas, portarias, e leis aplicáveis ao caso concreto.",
7. Direcionamentos Finais: "Instruções sobre ofícios a serem enviados, comprovações, e arquivamento."

Utilize uma linguagem formal e técnica adequada para um contexto jurídico, incorporando os elementos e o estilo dos exemplos dados para criar um novo despacho judicial simulado."""
            ]
        }
    }
}


TEMPLATE_DECISAO_COMPOSTO_ALIMENTAR= {
    "header": "# Modelo para elaboração de despacho.",
    "instructions": [
        "Cada número abaixo corresponde a uma seção. Exemplo: '1. Identificação do Tipo de Decisão' significa a primeira seção.",
        "Cada número seguido de um ponto é uma subseção. Exemplo: '2.1 Objeto da Decisão' significa a primeira subseção da seção 2.",
        "Implemente subsubseções se necessário."
    ],
    "template": {
        "Texto Completo": {
            "description": "Crie um despacho judicial para a concessão de composto alimentar, baseando-se nos dados fornecidos e nos seguintes exemplos fornecidos de decisões anteriores, o texto deve ser em um único parágrafo. O texto não pode vir com todas as letras em maiúsculo.",
            "elements": [
                """Exemplos:
1. R.H. Trata-se de decisão interlocutória concedendo a antecipação dos efeitos da tutela jurisdicional para determinar o fornecimento de composto alimentar de comercialização autorizada no país. Ausência de dano moral. Laudo público (HUWC). Aplicação da Portaria 01/2017, art. 1º, III c/c art. 2º, I e II. Opino pela não apresentação/interposição de defesa/recurso.

2. R.H. Trata-se de decisão interlocutória concedendo a antecipação dos efeitos da tutela jurisdicional para determinar o fornecimento de composto alimentar de comercialização autorizada no país, bem como materiais para administrá-lo, e os seguintes insumos: cadeira de rodas adaptada, óleo de girassol, pomada nistatina, sonda de aspiração, gazes e um aparelho aspirador-inalador. Ausência de dano moral. Laudo público (Santa Casa de Misericórdia de Fortaleza). Aplicação da Portaria 01/2017, art. 1º, III e V c/c art. 2º, I e II. Opino pela não apresentação/interposição de defesa/recurso. À chefia para ratificação, após arquivar a pasta.

3. R.H. Trata-se de decisão interlocutória concedendo a antecipação dos efeitos da tutela jurisdicional para determinar o fornecimento de composto alimentar. Custo do tratamento anual é inferior a 60 salários mínimos. Ausência de dano moral. Laudo público (HIAS). Aplicação da Portaria 01/2017, art. 1º, III c/c art. 2º, I e II. De acordo com os precedentes recentes desta PGE (exemplo: 0202503-31.2022.8.06.0055), opino pela não apresentação/interposição de defesa/recurso. Conforme orientação da chefia, arquivar a pasta.

4. R.H. Trata-se de decisão interlocutória concedendo a antecipação dos efeitos da tutela jurisdicional para determinar o fornecimento de composto alimentar de comercialização autorizada no país e materiais para administrá-lo, bem como os seguintes insumos: cama e colchão hospitalares, fraldas geriátricas descartáveis 'G'. Custo anual do tratamento não supera o teto de 60 salários mínimos. Ausência de dano moral. Laudo público (Prefeitura de Fortaleza). Conforme precedente desta setorial (0202503-31.2022.8.06.0055), foi concedida a dispensa de apresentação/interposição de defesa/recurso pelo gabinete nesses casos em que o custo do tratamento anual enquadra-se no teto dos Juizados da Fazenda Pública. Aplicação da Portaria 01/2017, art. 1º, III c/c art. 2º, I e II. Opino pela não apresentação/interposição de defesa/recurso. Conforme orientação da chefia, arquivar a pasta.


Informaçoes que devem estar no despacho a ser gerado:
1. Identificação do Despacho
2. Decisão sobre o Pleito
3. Especificação do Composto Alimentar e Insumos
4. Danos Morais
5. Aplicação de Normativas Específicas
6. Direcionamentos Finais

Utilize uma linguagem formal e técnica adequada para um contexto jurídico, incorporando os elementos e o estilo dos exemplos dados para criar um novo despacho judicial simulado."""
            ]
        }
    }
}





