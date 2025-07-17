from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document
import os
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.1,
            max_tokens=1000
        )
        self.setup_prompts()
    
    def setup_prompts(self):
        """Setup different prompt templates for various use cases"""
        self.qa_prompt = ChatPromptTemplate.from_template("""
You are a helpful AI assistant that answers questions based on the provided context.
Use the following pieces of context to answer the user's question accurately and concisely.

Rules:
1. Only use information from the provided context
2. If you cannot find the answer in the context, say "I don't have enough information to answer this question based on the provided documents."
3. Be specific and cite relevant parts of the context when possible
4. If the question is ambiguous, ask for clarification

Context:
{context}

Question: {question}

Answer:""")
        
        self.summary_prompt = ChatPromptTemplate.from_template("""
Provide a concise summary of the following document content:

Content:
{content}

Summary:""")
    
    def retrieve_documents(self, query: str, document_ids: List[str] = None, k: int = 5) -> List[Document]:
        """Retrieve relevant documents for a query"""
        try:
            if document_ids:
                # Filter by specific documents
                docs = self.vector_db.similarity_search_with_filter(query, document_ids, k=k)
            else:
                # Search all documents
                docs = self.vector_db.similarity_search(query, k=k)
            
            logger.info(f"Retrieved {len(docs)} documents for query: {query[:50]}...")
            return docs
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def format_context(self, documents: List[Document]) -> str:
        """Format retrieved documents into context string"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', 'N/A')
            context_parts.append(f"Document {i} (Source: {source}, Page: {page}):\n{doc.page_content}")
        
        return "\n\n".join(context_parts)
    
    def calculate_confidence(self, documents: List[Document], query: str) -> float:
        """Calculate confidence score based on document relevance"""
        if not documents:
            return 0.0
        
        # Simple confidence calculation based on number of relevant docs
        # In a real system, you'd use similarity scores
        base_confidence = min(len(documents) / 5.0, 1.0)  # Max confidence with 5+ docs
        
        # Boost confidence if query terms appear in retrieved docs
        query_terms = query.lower().split()
        term_matches = 0
        total_terms = len(query_terms)
        
        for doc in documents:
            content_lower = doc.page_content.lower()
            for term in query_terms:
                if term in content_lower:
                    term_matches += 1
        
        term_confidence = term_matches / (total_terms * len(documents)) if total_terms > 0 else 0
        
        return min((base_confidence + term_confidence) / 2, 1.0)
    
    def query(self, question: str, document_ids: List[str] = None) -> Dict[str, Any]:
        """Process a query and return response with sources"""
        try:
            # Retrieve relevant documents
            documents = self.retrieve_documents(question, document_ids)
            
            if not documents:
                return {
                    'answer': "I don't have any relevant documents to answer your question. Please upload some documents first.",
                    'sources': [],
                    'confidence': 0.0
                }
            
            # Format context
            context = self.format_context(documents)
            
            # Generate answer
            chain = self.qa_prompt | self.llm | StrOutputParser()
            answer = chain.invoke({
                "context": context,
                "question": question
            })
            
            # Extract sources
            sources = []
            for doc in documents:
                source_info = {
                    'filename': doc.metadata.get('source', 'Unknown'),
                    'page': doc.metadata.get('page', 'N/A'),
                    'chunk_id': doc.metadata.get('chunk_id', 'N/A'),
                    'preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                sources.append(source_info)
            
            # Calculate confidence
            confidence = self.calculate_confidence(documents, question)
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }
    
    def summarize_document(self, document_content: str) -> str:
        """Generate a summary of document content"""
        try:
            chain = self.summary_prompt | self.llm | StrOutputParser()
            summary = chain.invoke({"content": document_content})
            return summary
        except Exception as e:
            logger.error(f"Error summarizing document: {str(e)}")
            return "Unable to generate summary."