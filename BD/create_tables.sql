-- scm_robo_intimacao.tb_medicamentos definition

-- Drop table

-- DROP TABLE scm_robo_intimacao.tb_medicamentos;

CREATE TABLE scm_robo_intimacao.tb_medicamentos (
	id serial4 NOT NULL,
	id_analiseportaria int4 NULL,
	data_analise timestamp NULL,
	nome_principio varchar NULL,
	nome_comercial varchar NULL,
	dosagem numeric(10, 2) NULL,
	qtde int4 NULL,
	possui_anvisa bool NULL,
	registro_anvisa varchar NULL,
	fornecido_sus bool NULL,
	valor numeric(10, 2) NULL,
	CONSTRAINT tb_medicamentos_pkey PRIMARY KEY (id)
);


-- scm_robo_intimacao.tb_analiseportaria definition

-- Drop table

-- DROP TABLE scm_robo_intimacao.tb_analiseportaria;

CREATE TABLE scm_robo_intimacao.tb_analiseportaria (
	id serial4 NOT NULL,
	fk_autosprosaude int4 NULL,
	numerounico varchar(50) NULL,
	caminho varchar(255) NULL,
	base varchar(50) NULL,
	dt_processado timestamp NULL,
	marcado_analisar bool NULL,
	analisado bool NULL,
	id_documento_analisado varchar(50) NULL,
	dt_analisado timestamp NULL,
	tipo_documento varchar(255) NULL,
	aplica_portaria bool NULL,
	despacho_gerado varchar NULL,
	possui_medicamentos bool NULL,
	possui_internacao bool NULL,
	possui_consultas_exames_procedimentos bool NULL,
	possui_insulina bool NULL,
	possui_insumos bool NULL,
	possui_multidisciplinar bool NULL,
	possui_custeio bool NULL,
	possui_compostos bool NULL,
	possui_condenacao_honorarios bool NULL,
	valor_condenacao_honorarios numeric(10, 2) NULL,
	possui_danos_morais bool NULL,
	lista_outros varchar(255) NULL,
	input_tokens int4 NULL,
	completion_tokens int4 NULL,
	custo_analise numeric(10, 2) NULL,
	resumo text NULL,
	avaliacao_analise varchar(255) NULL,
	pagina_analisada int4 NULL,
	resumo_analise varchar NULL,
	confirma_analise bool NULL,
	possui_outros_impeditivos bool NULL,
	respeita_valor_teto bool NULL,
	possui_outros bool NULL,
	status varchar NULL,
	avisadonoportal bool NULL,
	houve_extincao bool NULL,
	cumprimento_de_sentenca bool NULL,
	bloqueio_de_recursos bool NULL,
	monocratica bool NULL,
	lista_outros_impeditivos varchar NULL,
	CONSTRAINT tb_analiseportaria_pkey PRIMARY KEY (id)
);


-- scm_robo_intimacao.tb_compostos definition

-- Drop table

-- DROP TABLE scm_robo_intimacao.tb_compostos;

CREATE TABLE scm_robo_intimacao.tb_compostos (
	id serial4 NOT NULL,
	id_analiseportaria int4 NULL,
	data_analise timestamp NULL,
	nome_composto varchar NULL,
	qtde int4 NULL,
	duracao int4 NULL,
	possui_anvisa bool NULL,
	registro_anvisa varchar(15) NULL,
	valor numeric(10, 2) NULL,
	CONSTRAINT tb_compostos_pkey PRIMARY KEY (id)
);


-- scm_robo_intimacao.tb_documentosautos definition

-- Drop table

-- DROP TABLE scm_robo_intimacao.tb_documentosautos;

CREATE TABLE scm_robo_intimacao.tb_documentosautos (
	id serial4 NOT NULL,
	numerounico varchar(50) NULL,
	id_documento varchar(15) NULL,
	dt_assinatura timestamp NULL,
	nome varchar NULL,
	tipo varchar NULL,
	id_analiseportaria int4 NULL,
	CONSTRAINT tb_documentosautos_pkey PRIMARY KEY (id)
);


-- scm_robo_intimacao.tb_analiseportaria foreign keys

ALTER TABLE scm_robo_intimacao.tb_analiseportaria ADD CONSTRAINT tb_analiseportaria_fk_autosprosaude_fkey FOREIGN KEY (fk_autosprosaude) REFERENCES scm_robo_intimacao.tb_autosprocessos(id);


-- scm_robo_intimacao.tb_compostos foreign keys

ALTER TABLE scm_robo_intimacao.tb_compostos ADD CONSTRAINT tb_compostos_id_analiseportaria_fkey FOREIGN KEY (id_analiseportaria) REFERENCES scm_robo_intimacao.tb_analiseportaria(id);


-- scm_robo_intimacao.tb_documentosautos foreign keys

ALTER TABLE scm_robo_intimacao.tb_documentosautos ADD CONSTRAINT fk_analiseportaria FOREIGN KEY (id_analiseportaria) REFERENCES scm_robo_intimacao.tb_analiseportaria(id);