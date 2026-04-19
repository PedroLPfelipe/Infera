# Infera
[![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Neo4j](https://img.shields.io/badge/Database-Neo4j-blue)](https://neo4j.com/)
[![LangChain](https://img.shields.io/badge/Framework-LangChain-1C3C3C?style=flat&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![Groq](https://img.shields.io/badge/Inference-Groq-F55036?style=flat)](https://groq.com/)
[![pymupdf4llm](https://img.shields.io/badge/PDF_Markdown-pymupdf4llm-4A90D9?style=flat&logo=adobeacrobatreader&logoColor=white)](https://pymupdf4llm.readthedocs.io/)
[![HuggingFace](https://img.shields.io/badge/Embeddings-HuggingFace-FFD21E?style=flat&logo=huggingface&logoColor=black)](https://huggingface.co/)
[![FAISS](https://img.shields.io/badge/Vector_Store-FAISS-0467DF?style=flat&logo=meta&logoColor=white)](https://faiss.ai/)
[![Llama 3.3](https://img.shields.io/badge/LLM-Llama_3.3_70b-0467DF?style=flat&logo=meta&logoColor=white)](https://ai.meta.com/blog/meta-llama-3/)

# Sobre o protótipo
Este projeto é um protótipo **(POC)** que combina busca vetorial **(RAG)** com um banco de dados em grafos **(Neo4j)** para responder perguntas técnicas sobre manuais de equipamentos industriais em segundos. O protótipo foi desenvolvido como projeto de conclusão de um curso de IA Generativa, com o objetivo de demonstrar que é possível construir uma solução funcional para uma demanda real usando ferramentas gratuitas e os conceitos estudados em aula — RAG, engenharia de prompt e sistemas multi-agentes.

# Funcionamento
<h3>O sistema processa PDF e expõe duas interfaces especializadas:</h3>  

<h4>Agente de Parâmetros</h4>
Identifica códigos no formato P0270, busca os trechos relevantes do manual e retorna nome, função, valor padrão de fábrica e faixa de ajuste do parâmetro.
<h4>Agente de Falhas e Alarmes</h4>
Identifica códigos no formato F022 ou A015, recupera o contexto do manual e retorna o nome da falha, as causas mais prováveis e o procedimento de solução.

_____

A cada resposta gerada, o sistema extrai automaticamente triplas de conhecimento (sujeito → relação → objeto) e as grava no Neo4j, construindo progressivamente uma base de conhecimento estruturada sobre o equipamento consultado.

_____

# Pipeline

<h3>O processo de uma consulta é divido em duas etapas.</h3>  

![image alt](https://github.com/PedroLPfelipe/Infera/blob/6bc15647bde0720bb1a6bae1b825de0ada335bf6/images/FluxoConsulta.png)

# Arquitetura

<h3>Arquivos separados possuem aplicabilidades únicas que se integram para formar uma única aplicação funicional.</h3>  

<h4>app.py</h4>
Interface web (Streamlit), gerenciamento de sessão e orquestração do fluxo.

<h4>rag_pipeline.py</h4>
Processamento do PDF, vetorização, busca e geração de respostas.

<h4>graph_db.py</h4>
Conexão com Neo4j e operações de leitura e escrita no grafo.

# Elaborações sobre ferramentas
<h4>pymupdf4llm em vez de PyPDFLoader</h4>
Muitos manuais industriais são ricos em tabelas. O PyPDF convencional perde a estrutura tabular. 

<h4>MMR</h4>
max_marginal_relevance_search analisa os 21 chunks mais próximos e entrega os 6 mais variados ao LLM, evitando repetições e ampliando o contexto.

<h4>temperature=0</h4>
Ao realizar leituras de tabelas técnicas e diagnósticos de falhas, a criatividade se torna inimiga da precisão técnica necessária. O modelo é instruído a não inventar valores, se não encontrar a informação requisitada, deve dizer isso explicitamente para o usuário.

<h4>Neo4j Aura (gratuito)</h4>
Cada resposta gerada alimenta o grafo com novas triplas. Com o passar do tempo, o sistema acumula relações entre parâmetros, falhas e causas e forma uma base de conhecimento que cresce com base no uso da aplicação.

<h4>Groq</h4>
A empresa <b>Groq</b> desenvolveu um chip próprio chamado LPU (Language Processing Unit), projetado especificamente para executar modelos de linguagem, permitindo rodar modelos grandes com uma velocidade de geração de tokens muito superior à média do mercado. Além disso, O Groq oferece um plano gratuito com bons limites requisições diárias e hospeda o <b>Llama 3.3 70b</b>, um modelo de 70 bilhões de parâmetros desenvolvido pela <b>Meta</b> e disponibilizado como open-source.

# Requisitos para rodar o protótipo
- Python 3.10+
- Conta na plataforma Neo4j Aura e uma instância gratuita
- Chave API do Groq Cloud no plano gratuito
- Instalação das depêndencias presentes no requirements.txt
- Configuração das credenciais no arquivo .env
- Execução da interface web com <b>streamlit run app.py</b>
