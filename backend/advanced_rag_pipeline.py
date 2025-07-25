from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import Document
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain
import os
import json
import re
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedRAGPipeline:
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.models = self.setup_models()
        self.current_model = "llama-3.1-8b-instant"
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10  # Remember last 10 exchanges
        )
        self.setup_prompts()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def setup_models(self):
        """Setup multiple AI models for different use cases"""
        return {
            "llama-3.1-8b-instant": {
                "model": ChatGroq(model="llama-3.1-8b-instant", temperature=0.1, max_tokens=1000),
                "description": "Fast and efficient for general Q&A",
                "use_case": "general"
            },
            "llama-3.1-70b-versatile": {
                "model": ChatGroq(model="llama-3.1-70b-versatile", temperature=0.1, max_tokens=1500),
                "description": "More powerful for complex analysis",
                "use_case": "analysis"
            },
            "mixtral-8x7b-32768": {
                "model": ChatGroq(model="mixtral-8x7b-32768", temperature=0.2, max_tokens=2000),
                "description": "Creative and detailed responses",
                "use_case": "creative"
            }
        }
    
    def setup_prompts(self):
        """Setup advanced prompt templates"""
        self.qa_prompt = ChatPromptTemplate.from_template("""
You are an advanced AI assistant with expertise in document analysis and question answering.
Use the provided context to answer questions accurately, providing detailed insights when possible.

Context: {context}
Chat History: {chat_history}
Question: {question}

Instructions:
1. Provide comprehensive answers based on the context
2. Reference specific sections or pages when relevant
3. If the question builds on previous conversation, acknowledge the context
4. Highlight key insights and implications
5. If information is insufficient, suggest what additional context might help

Answer:""")
        
        self.analysis_prompt = ChatPromptTemplate.from_template("""
Perform a detailed analysis of the following document content:

Content: {content}

Provide:
1. Key themes and topics
2. Important insights and findings
3. Main arguments or conclusions
4. Relevant statistics or data points
5. Potential implications or applications

Analysis:""")
        
        self.summary_prompt = ChatPromptTemplate.from_template("""
Create a comprehensive summary of the following document:

Content: {content}

Provide:
1. Executive summary (2-3 sentences)
2. Main points (bullet format)
3. Key conclusions
4. Important details or statistics

Summary:""")
        
        self.entity_extraction_prompt = ChatPromptTemplate.from_template("""
Extract and categorize important entities from the following text:

Text: {text}

Extract:
1. People (names, roles, organizations)
2. Places (locations, addresses, countries)
3. Dates and times
4. Numbers and statistics
5. Key concepts and terms
6. Organizations and institutions

Format as JSON with categories.

Entities:""")

    def switch_model(self, model_name: str):
        """Switch to a different AI model"""
        if model_name in self.models:
            self.current_model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        return False

    def get_available_models(self):
        """Get list of available models with descriptions"""
        return {name: {"description": info["description"], "use_case": info["use_case"]} 
                for name, info in self.models.items()}

    def advanced_search(self, query: str, filters: Dict[str, Any] = None, k: int = 10) -> List[Document]:
        """Advanced search with filters and ranking"""
        try:
            # Basic similarity search
            docs = self.vector_db.similarity_search(query, k=k*2)  # Get more for filtering
            
            # Apply filters if provided
            if filters:
                docs = self.apply_filters(docs, filters)
            
            # Re-rank results based on relevance
            docs = self.rerank_documents(docs, query)
            
            return docs[:k]
        except Exception as e:
            logger.error(f"Error in advanced search: {str(e)}")
            return []

    def apply_filters(self, docs: List[Document], filters: Dict[str, Any]) -> List[Document]:
        """Apply various filters to search results"""
        filtered_docs = docs
        
        # Filter by document type
        if 'file_type' in filters:
            file_types = filters['file_type'] if isinstance(filters['file_type'], list) else [filters['file_type']]
            filtered_docs = [doc for doc in filtered_docs 
                           if any(doc.metadata.get('source', '').endswith(f'.{ft}') for ft in file_types)]
        
        # Filter by date range
        if 'date_range' in filters:
            # Implementation would depend on how dates are stored in metadata
            pass
        
        # Filter by document size
        if 'min_length' in filters:
            min_len = filters['min_length']
            filtered_docs = [doc for doc in filtered_docs if len(doc.page_content) >= min_len]
        
        # Filter by keywords
        if 'keywords' in filters:
            keywords = filters['keywords'] if isinstance(filters['keywords'], list) else [filters['keywords']]
            filtered_docs = [doc for doc in filtered_docs 
                           if any(keyword.lower() in doc.page_content.lower() for keyword in keywords)]
        
        return filtered_docs

    def rerank_documents(self, docs: List[Document], query: str) -> List[Document]:
        """Re-rank documents based on advanced relevance scoring"""
        query_terms = query.lower().split()
        
        def calculate_relevance_score(doc):
            content = doc.page_content.lower()
            score = 0
            
            # Term frequency scoring
            for term in query_terms:
                score += content.count(term) * 2
            
            # Boost for exact phrase matches
            if query.lower() in content:
                score += 10
            
            # Boost for title/header matches (if available)
            if 'title' in doc.metadata:
                title = doc.metadata['title'].lower()
                for term in query_terms:
                    if term in title:
                        score += 5
            
            # Penalize very short or very long chunks
            length = len(content)
            if 100 < length < 2000:
                score += 2
            elif length < 50:
                score -= 3
            
            return score
        
        # Sort by relevance score
        scored_docs = [(doc, calculate_relevance_score(doc)) for doc in docs]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in scored_docs]

    async def analyze_document_async(self, document_content: str) -> Dict[str, Any]:
        """Asynchronous document analysis"""
        try:
            model = self.models[self.current_model]["model"]
            
            # Run analysis tasks concurrently
            tasks = [
                self.extract_entities(document_content),
                self.generate_summary(document_content),
                self.perform_analysis(document_content)
            ]
            
            entities, summary, analysis = await asyncio.gather(*tasks)
            
            return {
                "entities": entities,
                "summary": summary,
                "analysis": analysis,
                "word_count": len(document_content.split()),
                "char_count": len(document_content),
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error in document analysis: {str(e)}")
            return {"error": str(e)}

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text"""
        try:
            model = self.models[self.current_model]["model"]
            chain = self.entity_extraction_prompt | model | StrOutputParser()
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                lambda: chain.invoke({"text": text[:2000]})  # Limit text length
            )
            
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(result)
            except:
                return {"raw_entities": result}
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return {"error": str(e)}

    async def generate_summary(self, content: str) -> str:
        """Generate document summary"""
        try:
            model = self.models[self.current_model]["model"]
            chain = self.summary_prompt | model | StrOutputParser()
            
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                self.executor,
                lambda: chain.invoke({"content": content[:3000]})
            )
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"

    async def perform_analysis(self, content: str) -> str:
        """Perform detailed document analysis"""
        try:
            model = self.models[self.current_model]["model"]
            chain = self.analysis_prompt | model | StrOutputParser()
            
            loop = asyncio.get_event_loop()
            analysis = await loop.run_in_executor(
                self.executor,
                lambda: chain.invoke({"content": content[:3000]})
            )
            return analysis
        except Exception as e:
            logger.error(f"Error performing analysis: {str(e)}")
            return f"Error performing analysis: {str(e)}"

    def conversational_query(self, question: str, document_ids: List[str] = None, 
                           session_id: str = None) -> Dict[str, Any]:
        """Enhanced query with conversation memory"""
        try:
            # Retrieve relevant documents
            documents = self.advanced_search(question, k=8)
            
            if not documents:
                return {
                    'answer': "I don't have any relevant documents to answer your question.",
                    'sources': [],
                    'confidence': 0.0,
                    'model_used': self.current_model
                }
            
            # Format context with enhanced information
            context = self.format_enhanced_context(documents)
            
            # Get chat history for this session
            chat_history = self.memory.chat_memory.messages if session_id else []
            
            # Generate answer with conversation context
            model = self.models[self.current_model]["model"]
            chain = self.qa_prompt | model | StrOutputParser()
            
            answer = chain.invoke({
                "context": context,
                "question": question,
                "chat_history": self.format_chat_history(chat_history)
            })
            
            # Update memory
            if session_id:
                self.memory.chat_memory.add_user_message(question)
                self.memory.chat_memory.add_ai_message(answer)
            
            # Extract enhanced sources
            sources = self.extract_enhanced_sources(documents)
            
            # Calculate confidence with multiple factors
            confidence = self.calculate_enhanced_confidence(documents, question, answer)
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence,
                'model_used': self.current_model,
                'context_length': len(context),
                'documents_used': len(documents),
                'session_id': session_id
            }
        
        except Exception as e:
            logger.error(f"Error processing conversational query: {str(e)}")
            return {
                'answer': f"I encountered an error: {str(e)}",
                'sources': [],
                'confidence': 0.0,
                'model_used': self.current_model,
                'error': str(e)
            }

    def format_enhanced_context(self, documents: List[Document]) -> str:
        """Format context with enhanced metadata"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', 'N/A')
            chunk_id = doc.metadata.get('chunk_id', 'N/A')
            
            context_part = f"""
Document {i} (Source: {source}, Page: {page}, Chunk: {chunk_id}):
{doc.page_content}
---
"""
            context_parts.append(context_part)
        
        return "\n".join(context_parts)

    def format_chat_history(self, messages) -> str:
        """Format chat history for context"""
        if not messages:
            return "No previous conversation."
        
        history_parts = []
        for msg in messages[-6:]:  # Last 6 messages
            role = "Human" if hasattr(msg, 'content') and msg.type == "human" else "Assistant"
            content = msg.content if hasattr(msg, 'content') else str(msg)
            history_parts.append(f"{role}: {content}")
        
        return "\n".join(history_parts)

    def extract_enhanced_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract enhanced source information"""
        sources = []
        for doc in documents:
            source_info = {
                'filename': doc.metadata.get('source', 'Unknown'),
                'page': doc.metadata.get('page', 'N/A'),
                'chunk_id': doc.metadata.get('chunk_id', 'N/A'),
                'preview': doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                'word_count': len(doc.page_content.split()),
                'relevance_indicators': self.extract_relevance_indicators(doc.page_content)
            }
            sources.append(source_info)
        
        return sources

    def extract_relevance_indicators(self, content: str) -> List[str]:
        """Extract indicators of content relevance"""
        indicators = []
        
        # Look for numbers/statistics
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', content)
        if numbers:
            indicators.append(f"Contains {len(numbers)} numerical values")
        
        # Look for dates
        dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}\b', content)
        if dates:
            indicators.append(f"Contains {len(dates)} date references")
        
        # Look for key phrases
        key_phrases = ['important', 'significant', 'key', 'main', 'primary', 'essential']
        found_phrases = [phrase for phrase in key_phrases if phrase in content.lower()]
        if found_phrases:
            indicators.append(f"Contains key terms: {', '.join(found_phrases[:3])}")
        
        return indicators

    def calculate_enhanced_confidence(self, documents: List[Document], query: str, answer: str) -> float:
        """Calculate confidence with multiple factors"""
        if not documents:
            return 0.0
        
        # Base confidence from document count
        doc_confidence = min(len(documents) / 8.0, 1.0)
        
        # Query term matching
        query_terms = query.lower().split()
        term_matches = 0
        total_possible = len(query_terms) * len(documents)
        
        for doc in documents:
            content_lower = doc.page_content.lower()
            for term in query_terms:
                if term in content_lower:
                    term_matches += 1
        
        term_confidence = term_matches / total_possible if total_possible > 0 else 0
        
        # Answer quality indicators
        answer_confidence = 0.5  # Base
        if len(answer) > 100:  # Detailed answer
            answer_confidence += 0.2
        if any(word in answer.lower() for word in ['specifically', 'according to', 'based on']):
            answer_confidence += 0.1
        if 'I don\'t' in answer or 'unclear' in answer.lower():
            answer_confidence -= 0.3
        
        # Combine confidences
        final_confidence = (doc_confidence * 0.4 + term_confidence * 0.4 + answer_confidence * 0.2)
        return min(max(final_confidence, 0.0), 1.0)

    def get_conversation_summary(self, session_id: str) -> str:
        """Get summary of conversation for a session"""
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return "No conversation history."
            
            # Create summary of conversation
            conversation_text = self.format_chat_history(messages)
            
            summary_prompt = ChatPromptTemplate.from_template("""
            Summarize the following conversation between a user and an AI assistant:
            
            Conversation:
            {conversation}
            
            Provide a brief summary of:
            1. Main topics discussed
            2. Key questions asked
            3. Important information provided
            
            Summary:
            """)
            
            model = self.models[self.current_model]["model"]
            chain = summary_prompt | model | StrOutputParser()
            
            summary = chain.invoke({"conversation": conversation_text})
            return summary
        except Exception as e:
            logger.error(f"Error generating conversation summary: {str(e)}")
            return f"Error generating summary: {str(e)}"

    def clear_memory(self, session_id: str = None):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info(f"Cleared conversation memory for session: {session_id}")

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        return {
            "current_model": self.current_model,
            "available_models": len(self.models),
            "memory_messages": len(self.memory.chat_memory.messages),
            "executor_threads": self.executor._max_workers,
            "timestamp": datetime.now().isoformat()
        }