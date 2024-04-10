# LAB 03 : Caracterizando a Atividade de Code Review no GitHub

## Enunciado:

A prática de code review tornou-se uma constante nos processos de desenvolvimento agéis. Em linhas gerais, ela consiste na interação entre desenvolvedores e revisores visando inspecionar o código produzido antes de integrá-lo à base principal. Assim, garante-se a qualidade do código integrado, evitando-se também a inclusão de defeitos. No contexto de sistemas open source, mais especificamente dos desenvolvidos através do GitHub, as atividades de code review acontecem a partir da avaliação de contribuições submetidas por meio de Pull Requests (PR). Ou seja, para que se integre um código na branch principal, é necessário que seja realizada uma solicitação de pull, que será avaliada e discutida por um colaborador do projeto. Ao final, a solicitação de merge pode ser aprovada ou rejeitada pelo revisor. Em muitos casos, ferramentas de verificação estática realizam uma primeira análise, avaliando requisitos de estilo de programação ou padrões definidos pela organização.

Neste contexto, o objetivo deste laboratório é analisar a atividade de code review desenvolvida em repositórios populares do GitHub, identificando variáveis que influenciam no merge de um PR, sob a perspectiva de desenvolvedores que submetem código aos repositórios selecionados. 

## Integrantes do grupo:

* Bruno Gomes Ferreira
* João Pedro Mairinque de Azevedo
* Matheus Vieira dos Santos
* Marcio Lucas Machado

## Execução

### Pré-requisitos
* Docker instalado e rodando na máquina

### Rodar
* `make run`

## Artefatos:

* [Relatório](docs/README.md)
* [Scripts](scripts)
* [Resultado](scripts/output_csv_repos/repos.csv)
* [Conjunto de dados](scripts/dataset)
