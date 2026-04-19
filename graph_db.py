# IMPORTAÇÃO DE BIBLIOTECAS
import os # Usado para acessar variáveis de ambiente (.env).
import streamlit as st
from neo4j import GraphDatabase # Driver oficial do Neo4j para Python.
from dotenv import load_dotenv # Usado para carregar variáveis de ambiente (.env).
# o import "os" e "load_dotenv" funcionam respectivamente para acessar e carregar as credenciais do banco de dados.

load_dotenv() # Carrega as credenciais locais do ".env".

def obter_credencial(chave): # Define uma função para conseguir as credenciais, busca primeiro no ".env" local e depois no Streamlit Secrets.
    return os.getenv(chave) or st.secrets.get(chave)

# Classe responsável por gerenciar a conexão e as operações no banco Neo4j Aura
class Neo4jClient:
    def __init__(self):
        # Inicializa driver com as credenciais (híbridas)
        try:
            self.driver = GraphDatabase.driver( # conecta ao banco usando as credenciais obtidas pela função "obter_credencial".
                obter_credencial("NEO4J_URI"), 
                auth=(obter_credencial("NEO4J_USER"), obter_credencial("NEO4J_PASSWORD"))
            )
        except Exception as e:
            print(f"⚠️ Erro crítico ao conectar com o Neo4j: {e}")
            self.driver = None

    def close(self):
        # Fecha a conexão com o banco para liberar memória
        if self.driver:
            self.driver.close()

    # ESCRITA NO GRAFO (COM BATCH INSERTION)
    def insert_triples(self, triples): # Define uma função para inserir triplas no banco.
        if not triples or not self.driver:
            return False

        # Formata a lista de triplas em uma lista de dicionários para o Neo4j ler
        dados_triplas = [
            {"subj": subj.strip(), "rel": rel.strip(), "obj": obj.strip()} # "subj": "Entidade A", "rel": "Relacionamento", "obj": "Entidade B"
            for subj, rel, obj in triples 
        ]

        # Tratamento de erro adicionado para evitar travamento do Streamlit
        try:
            with self.driver.session() as session:
                session.run( # Forma de inserir triplas usando "UNWIND", processa a lista de dicionários e criar os nós e relacionamentos no Neo4j.
                    """
                    UNWIND $dados_triplas AS tripla
                    MERGE (a:Entity {name: tripla.subj})
                    MERGE (b:Entity {name: tripla.obj})
                    MERGE (a)-[:RELATION {type: tripla.rel}]->(b)
                    """,
                    dados_triplas=dados_triplas # Associa a variável "dados_triplas" do Cypher com a lista de dicionários formatada em Python.
                )
            return True
        except Exception as e:
            print(f"❌ Erro ao inserir triplas no Neo4j: {e}")
            return False
            # o "$" é usado em "$dados_triplas" como um placeholder para a variável passada no método "session.run()".
            # O Neo4j processa a consulta Cypher e substitui pela lista de triplas formatada, obtida na variável "dados_triplas" do Python.

    # LEITURA NO GRAFO / RECUPERAÇÃO DE CONTEXTO
    def query_graph(self, keywords): #Busca relacionamentos que envolvam as palavras-chave fornecidas.
        if not keywords or not self.driver:
            return [] # Retorna uma lista vazia se não houver keywords ou se a conexão com o banco falhou. Evitando erros no Streamlit.

        try: # Busca no Neo4j por relacionamentos entre nós que envolvam as palavras-chave fornecidas através de uma consulta Cypher.
            with self.driver.session() as session:
                result = session.run( # A consulta usa WHERE para filtrar nós que contenham palavras-chave fornecidas.
                    """
                    MATCH (a:Entity)-[r:RELATION]->(b:Entity)
                    WHERE a.name IN $keywords OR b.name IN $keywords
                    RETURN a.name AS a, r.type AS rel, b.name AS b
                    LIMIT 20
                    """,
                    keywords=keywords # Associa a variável "keywords" do Cypher com a lista de palavras-chave passada no método "session.run()".
                )
                # Retorna lista de strings formatadas de relacionamentos encontrados, no formato "Entidade A - Relacionamento - Entidade B".
                return [f"{record['a']} - {record['rel']} - {record['b']}" for record in result]
        except Exception as e: # Exceção é capturada para evitar erros que travam o Streamlit, uma mensagem de erro também é exibida no console.
            print(f"❌ Erro ao realizar busca no Neo4j: {e}")
            return []
