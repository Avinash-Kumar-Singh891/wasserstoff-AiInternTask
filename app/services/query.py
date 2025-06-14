
# services/query.py
from .vector_store import FAISSVectorStore
from .llm import DocumentQAAgent

class QueryProcessor:
    def __init__(self):
        self.vector_store = FAISSVectorStore()
        self.qa_agent = DocumentQAAgent()
        
    def process_query(self, question, k=10):
        """Process a query and return structured results"""
        # Get relevant documents
        contexts, metadata_list = self.vector_store.search(question, k=k)
        
        if not contexts:
            return {
                'individual_answers': [],
                'themes': [],
                'synthesized_answer': "No relevant documents found for your query."
            }
        
        # Generate answer with themes using LangChain agent
        agent_response = self.qa_agent.generate_answer_with_themes(
            question, contexts, metadata_list
        )
        
        # Parse the response (you might want to make this more robust)
        individual_answers = self._extract_individual_answers(agent_response, contexts, metadata_list)
        themes = self._extract_themes(agent_response)
        synthesized_answer = self._extract_synthesized_answer(agent_response)
        
        return {
            'individual_answers': individual_answers,
            'themes': themes,
            'synthesized_answer': synthesized_answer,
            'raw_response': agent_response
        }
    
    def _extract_individual_answers(self, response, contexts, metadata_list):
        """Extract individual document answers from LLM response"""
        individual_answers = []
        for i, (context, metadata) in enumerate(zip(contexts, metadata_list)):
            individual_answers.append({
                'document_id': metadata.get('doc_id', f'DOC{i:03d}'),
                'answer': context[:200] + "..." if len(context) > 200 else context,
                'citation': f"Page {metadata.get('page', 'N/A')}, Para {metadata.get('paragraph', 'N/A')}",
                'relevance_score': metadata.get('score', 0.0)
            })
        return individual_answers
    
    def _extract_themes(self, response):
        """Extract themes from LLM response"""
        
        themes = []
        lines = response.split('\n')
        current_theme = None
        
        for line in lines:
            if 'Theme' in line and ':' in line:
                if current_theme:
                    themes.append(current_theme)
                current_theme = {
                    'name': line.strip(),
                    'summary': '',
                    'supporting_docs': []
                }
            elif current_theme and line.strip():
                if 'Supporting Documents:' in line:
                    # Extract document IDs
                    current_theme['supporting_docs'] = line.replace('Supporting Documents:', '').strip()
                elif 'Summary:' in line:
                    current_theme['summary'] = line.replace('Summary:', '').strip()
                elif current_theme['summary']:
                    current_theme['summary'] += ' ' + line.strip()
        
        if current_theme:
            themes.append(current_theme)
            
        return themes
    
    def _extract_synthesized_answer(self, response):
        """Extract synthesized answer from LLM response"""
        # Simple extraction - look for content after themes
        lines = response.split('\n')
        synthesized_start = False
        synthesized_lines = []
        
        for line in lines:
            if 'synthesized' in line.lower() or 'conclusion' in line.lower():
                synthesized_start = True
                continue
            if synthesized_start and line.strip():
                synthesized_lines.append(line.strip())
        
        return ' '.join(synthesized_lines) if synthesized_lines else response
