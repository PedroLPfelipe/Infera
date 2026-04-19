# Infera
[![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Neo4j](https://img.shields.io/badge/Database-Neo4j-blue)](https://neo4j.com/)
[![LangChain](https://img.shields.io/badge/Framework-LangChain-1C3C3C?style=flat&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![Groq](https://img.shields.io/badge/Inference-Groq-F55036?style=flat)](https://groq.com/)

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

O processo de uma consulta é diivido em duas etapas.
