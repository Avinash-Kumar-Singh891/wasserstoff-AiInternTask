# services/llm.py

import os
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate


import os
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
from langchain.prompts import PromptTemplate

load_dotenv()  # Load .env values

class DocumentQAAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "llama3-70b-8192"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            openai_api_base=os.getenv("GROQ_API_BASE"),
            openai_api_key=os.getenv("GROQ_API_KEY")
        )
        self.memory = ConversationBufferMemory(return_messages=True)
        
    def generate_answer_with_themes(self, question, contexts, metadata_list):
        context_with_metadata = []
        for i, (context, metadata) in enumerate(zip(contexts, metadata_list)):
            doc_info = f"[Document {metadata.get('doc_id', i)}] "
            doc_info += f"(Page: {metadata.get('page', 'N/A')}, Para: {metadata.get('paragraph', 'N/A')}) "
            doc_info += context
            context_with_metadata.append(doc_info)

        context_text = "\n\n".join(context_with_metadata)

        prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""
You are an expert research assistant analyzing documents to provide comprehensive answers with theme identification.

DOCUMENT EXCERPTS:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. First, provide individual document answers in this EXACT format:
   **Individual Document Responses:**
   | Document ID | Extracted Answer | Citation |
   |-------------|------------------|----------|
   | DOC_ID | Answer text | Page X, Para Y |

2. Then, identify and analyze common themes across documents.
   Write each theme in the format:

   **Theme Name:** [e.g., Scanned Document Handling]  
   Supporting Docs: DOC_ID1 (Page X, Para Y), DOC_ID2 (Page A, Para B)  
   Summary: Write a brief theme summary here.

3. Finally, write:
   **Synthesized Answer:** Your final conclusion here.
"""
        )

        system_message = SystemMessage(content="You are an expert document analysis assistant.")
        human_message = HumanMessage(content=prompt_template.format(
            context=context_text,
            question=question
        ))

        response = self.llm([system_message, human_message])
        return response.content

# Test
agent = DocumentQAAgent()
contexts = ["Penalty issued under Clause 49 of LODR", "Violation of SEBI listing guidelines"]
metadata_list = [
    {"doc_id": "DOC001", "page": 3, "paragraph": 2},
    {"doc_id": "DOC002", "page": 1, "paragraph": 1}
]
answer = agent.generate_answer_with_themes("What are the penalties mentioned?", contexts, metadata_list)
print(answer)
