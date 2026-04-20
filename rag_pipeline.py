# IMPORTAÇÃO DE BIBLIOTECAS
import os # Usado para acessar variáveis de ambiente (.env)
import re # Regula as expressões geradas pelo LLM para extrair códigos de parâmetros e falhas.
import streamlit as st # Streamlit é usado para criar a interface web e acessar as credenciais de forma segura.
from langchain_community.document_loaders import PyPDFLoader # Carrega PDFs e os converte em documentos para processamento.
from langchain_text_splitters import RecursiveCharacterTextSplitter # Divide o texto em chunks ou segmentos menores para ajudar na vetorização.
from langchain_huggingface import HuggingFaceEmbeddings # Modelo de vetorização para transformar texto em vetores numéricos.
from langchain_community.vectorstores import FAISS # Biblioteca da META para criar um índice de vetores e realizar buscas eficientes.
from langchain_groq import ChatGroq # Importa o modelo de linguagem da Groq, usado para gerar respostas e extrair informações do texto.
import pymupdf4llm # Biblioteca que transforma o conteúdo de PDFs em texto Markdown, usado para ler tabelas de forma mais estruturada.
from langchain_text_splitters import MarkdownTextSplitter # Biblioteca para dividir o Markdown em pedaços, necessário pra processar tabelas grandes.
from langchain_core.documents import Document # Cria objetos sobre os textos divididos, facilitando a manipulação e vetorização.

def obter_credencial(chave):
    return os.getenv(chave) or st.secrets.get(chave) # Busca as credenciais primeiro no ambiente local e depois no Secrets do Streamlit.

class RAGPipeline:
    def __init__(self):
        
        # MODELOS (Embeddings e LLMs)
        
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2") # Modelo de embeddings leve e eficiente da Hugging Face.
        
        # LLM de uso geral (Para conversas e consultas gerais - DESCONTINUADO NO PROTÓTIPO MAS PRESENTE CASO HAJA NECESSIDADE DE USO FUTURO)
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",  # LLM da META usado no projeto, consegue lidar com contextos técnicos.
            temperature=0.3, # Temperatura baixa porém não zerada permite respostas mais criativas sem perder a precisão técnica.
            groq_api_key=obter_credencial("GROQ_API_KEY") # Pega a chave API da Groq de forma segura para autenticar o acesso ao modelo.    
        )
        
        # LLM de uso especializado (Para Parâmetros e Falhas - Zero Criatividade, Zero Alucinação)
        self.llm_strict = ChatGroq(
            model_name="llama-3.3-70b-versatile", # LLM da META usado no projeto.
            temperature=0.0, # Temperatura zerada é importante para ler tabelas.
            groq_api_key=obter_credencial("GROQ_API_KEY") # Obtém a chave API da Groq para autenticar o acesso ao modelo.
        )

    # PROCESSAMENTO DE DOCUMENTOS E VETORIZAÇÃO
    def load_pdf(self, file_path): 
        # Lê o PDF inteiro e converte TUDO (incluindo tabelas) para texto Markdown
        texto_markdown = pymupdf4llm.to_markdown(file_path)
        
        # Divide o texto Markdown, em pedaços de até 2000 caracteres com sobreposição máxima de 150 para manter o contexto.
        splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=150)
        textos_divididos = splitter.split_text(texto_markdown)
        
        docs = [Document(page_content=t) for t in textos_divididos]
        return docs

    def create_vectorstore(self, docs): # Cria o índice de vetores usando o PDF processado e a vetorização definida.
        return FAISS.from_documents(docs, self.embeddings) # FAISS é usado pra criar um índice de vetores, tornando a busca por similaridade rápida.

    def retrieve(self, vectorstore, query): 
        # O "k" é o número de resultados que são retornados para o user, o "fetch_k" é o número de resultados analisados pelo modelo.
        return vectorstore.max_marginal_relevance_search(query, k=6, fetch_k=21)

    # EXTRATORES DE INTENÇÃO (PARA BUSCA EXATA)
    def extract_parameter_code(self, query): # Extrai códigos de parâmetros como P0270, P1234 da pergunta do usuário.
        prompt = f"Extraia o código do parâmetro da pergunta. Ex: P0270. Retorne SÓ o código ou 'Nenhum'. Pergunta: {query}" # Projeção clara do que se espera do modelo.
        res = self.llm_strict.invoke(prompt).content.strip().upper() # O invoke faz a chamada para a LLM, passando o prompt e recebendo a resposta.
        match = re.search(r'P\s?\d{3,4}', res) # Busca por padrões que comecem com "P" seguido de 3 ou 4 dígitos.
        return match.group(0).replace(" ", "") if match else "Nenhum" # Retorna ou o código encontrado ou "Nenhum" se não achar nada.

    def extract_fault_code(self, query): # Extrai códigos de falhas ou alarmes como F022, A015 da pergunta do usuário.
        prompt = f"Extraia o código de falha/alarme da pergunta. Ex: F022, F0239, A015. Retorne SÓ o código ou 'Nenhum'. Pergunta: {query}"
        res = self.llm_strict.invoke(prompt).content.strip().upper()
        
        match = re.search(r'[FA]\s?\d{2,4}', res) # Busca por padrões que comecem com "F" ou "A" seguido de 2 a 4 dígitos.
        
        return match.group(0).replace(" ", "") if match else "Nenhum" # Retorna ou o código encontrado ou "Nenhum" se não achar nada.

    # AGENTES GERADORES ESPECIALIZADOS PARA DIMINUIR ALUCINAÇÕES DA LLM.
    def generate_parameter_answer(self, context, query): # Agente focado em responder perguntas sobre parâmetros.
        prompt = f"""
        Você é um Assistente Técnico. Sua ÚNICA tarefa é buscar parâmetros nas tabelas Markdown abaixo.
        REGRAS:
        1. NÃO INVENTE VALORES. Use apenas os dados do contexto.
        2. Se a informação não estiver clara no contexto, responda: "Parâmetro não encontrado no trecho analisado."
        3. Formate a resposta de forma limpa: Nome, Função, Padrão de Fábrica e Faixa de Ajuste.
        
        CONTEXTO (Tabelas do Manual):
        {context}
        
        PERGUNTA:
        {query}
        """
        # LLM restrito (temp=0)
        return self.llm_strict.invoke(prompt).content

    def generate_fault_answer(self, context, query): # Agente focado em responder perguntas sobre falhas e alarmes.
        prompt = f"""
        Você é um Especialista em Manutenção. Busque o código de falha ou alarme no contexto abaixo.
        REGRAS:
        1. NÃO INVENTE CAUSAS. Retorne EXATAMENTE o que o manual diz.
        2. Formate a resposta com: [Código] - [Nome da Falha] | Causas Mais Prováveis | Como Solucionar.
        3. Se não encontrar, diga: "Código de falha não listado no contexto atual."
        
        CONTEXTO (Manual de Diagnóstico):
        {context}
        
        PERGUNTA:
        {query}
        """
        return self.llm_strict.invoke(prompt).content

    # GERAÇÃO GERAL E EXTRAÇÃO DE GRAFOS
    def generate_answers(self, context, query): # def generate_answers é usado para gerar 2 respostas que se complementam, usando a LLM de pesquisa geral.
        prompt = f"""
        Gere exatamente 2 respostas diferentes, coerentes e complementares para a pergunta.
        Contexto: {context}
        Pergunta: {query}
        Retorne APENAS as duas respostas separadas por uma linha com três hifens (---).
        """
        resposta_bruta = self.llm.invoke(prompt).content # A resposta bruta é o texto completo gerado pela LLM.
        respostas_lista = [r.strip() for r in resposta_bruta.split('---')] # A resposta lista é a divisão (usand hífens) da resposta bruta.
        
        while len(respostas_lista) < 2: # Enquanto a LLM não gerar 2 respostas, preenche o restante com uma mensagem padrão para evitar erros de índice.
            respostas_lista.append("O modelo não gerou uma segunda resposta válida.")
            
        return respostas_lista[:2] # Retorna apenas as 2 primeiras respostas, garantindo que sempre haja 2 opções para o usuário escolher.
    
    def select_best(self, answers): # A função select_best recebe as respostas geradas e pede para a LLM escolher a melhor, retornando apenas o texto da resposta escolhida.
        respostas_formatadas = "\n\n".join([f"Opção {i+1}: {resp}" for i, resp in enumerate(answers)]) 
        prompt = f"Escolha a melhor resposta:\n{respostas_formatadas}\nRetorne APENAS o texto da melhor." # Pede para escolher a melhor resposta e retornar só o texto, sem explicações ou formatações.
        return self.llm.invoke(prompt).content # Retorna a resposta escolhida pela LLM como a melhor opção, que será exibida para o usuário.

    def extract_keywords(self, text): # A função recebe um texto e pede para a LLM extrair as palavras-chave.
        prompt = f"Extraia palavras-chave principais separadas por vírgula:\n{text}"
        return self.llm.invoke(prompt).content # Retorna as palavras-chave extraídas, elas podem ser usadas depois para enriquecer o grafo.

    def extract_triples(self, text): # A função recebe um texto e pede para LLM extrair as triplas no formato JSON.
        prompt = f"""
        Extraia as principais relações do texto abaixo no formato de triplas.
        Você DEVE retornar APENAS um array JSON válido e estrito.
        Formato: [["sujeito", "relação", "objeto"], ["sujeito", "relação", "objeto"]]
        Texto: {text}
        """
        resultado = self.llm.invoke(prompt).content
        match = re.search(r'\[.*\]', resultado, re.DOTALL) # A regular expression busca por um array JSON que tenha colchetes, garante que seja o formato esperado de triplas.
        return match.group(0) if match else "[]" # Retorna o array JSON encontrado ou um array vazio se não encontrar nada.
