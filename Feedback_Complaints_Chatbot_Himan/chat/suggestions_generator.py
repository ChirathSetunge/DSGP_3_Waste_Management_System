from .llm_handler import LLMHandler
from .document_processor import DocumentProcessor
import os
from Feedback_Complaints_Chatbot_Himan.config import Config


class SuggestionsGenerator:
    def __init__(self):
        self.llm_handler = LLMHandler()
        self.doc_processor = DocumentProcessor(
            knowledge_base_path=os.getenv('KNOWLEDGE_BASE_PATH', Config.KNOWLEDGE_BASE_PATH),
            vector_store_path=os.getenv('VECTOR_STORE_PATH', Config.VECTOR_STORE_PATH)
        )
        self.vector_store = self.doc_processor.load_vector_store()
        if not self.vector_store:
            print("Vector store not found. Creating new vector store...")
            self.vector_store = self.doc_processor.process_and_store()

    def generate_suggestions(self, user_input, bot_response, max_suggestions=3):
        reduce_docs = self.vector_store.similarity_search("reduce waste tips advice", k=3)
        reuse_docs = self.vector_store.similarity_search("reuse items tips advice", k=3)
        recycle_docs = self.vector_store.similarity_search("recycling tips advice", k=3)

        kb_context = ""
        for doc in reduce_docs + reuse_docs + recycle_docs:
            kb_context += doc.page_content + "\n"

        prompt = f"""
        You are a waste management assistant specialized in providing 3R (Reduce, Reuse, Recycle) tips.

        Current conversation:
        User: {user_input}
        Assistant: {bot_response}

        Knowledge base information on 3R practices:
        {kb_context}

        Based on the conversation and the knowledge base information above, generate exactly {max_suggestions} 
        specific, actionable follow-up suggestions related to 3R practices that would be helpful for this user.

        Requirements:
        1. Each suggestion must be directly related to Reduce, Reuse, or Recycle practices
        2. Each suggestion must be based ONLY on information from the knowledge base excerpts provided above
        3. Each suggestion should be phrased as a question (ending with '?')
        4. Keep each suggestion under 10 words
        5. Make each suggestion specific and practical
        6. Include at least one suggestion for each R (Reduce, Reuse, Recycle) if possible
        7.Please provide a clear, complete, meaningful suggestions

        Format your response as plain text with exactly {max_suggestions} suggestions, one per line, without numbering or bullet points.
        Do NOT use any formatting like bold, italics, quotes, or numbering.
        """

        try:
            response = self.llm_handler.generate_response(prompt)
            suggestions = [
                self._clean_suggestion(line.strip())
                for line in response.split('\n')
                if line.strip() and '?' in line
            ]
            verified_suggestions = []
            for suggestion in suggestions:
                if self._is_valid_suggestion(suggestion):
                    verified_suggestions.append(suggestion)

            if len(verified_suggestions) < max_suggestions:
                default_suggestions = self._generate_default_3r_suggestions(
                    max_suggestions - len(verified_suggestions)
                )
                verified_suggestions.extend(default_suggestions)

            return verified_suggestions[:max_suggestions]

        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return self._generate_default_3r_suggestions(max_suggestions)

    def _clean_suggestion(self, suggestion):
        for char in ['*', '_', '`', '"', "'", '1.', '2.', '3.', '-']:
            suggestion = suggestion.replace(char, '').strip()

        if not suggestion.endswith('?'):
            suggestion += '?'

        return suggestion

    def _is_valid_suggestion(self, suggestion):
        suggestion_lower = suggestion.lower()

        is_question = '?' in suggestion

        is_3r_related = any(term in suggestion_lower for term in [
            'reduce', 'reuse', 'recycle', 'waste', 'trash', 'garbage',
            'compost', 'environment', 'sustainable', 'eco', 'green',
            'plastic', 'paper', 'glass', 'metal', 'organic'
        ])

        return is_question and is_3r_related and len(suggestion.split()) <= 12

    def _generate_default_3r_suggestions(self, count):
        try:
            reduce_query = self.vector_store.similarity_search("practical reduce waste tips", k=2)
            reuse_query = self.vector_store.similarity_search("practical reuse items tips", k=2)
            recycle_query = self.vector_store.similarity_search("practical recycling guidelines", k=2)

            context = ""
            for doc in reduce_query + reuse_query + recycle_query:
                context += doc.page_content + "\n"

            prompt = f"""
            Based on this waste management knowledge base information:
            {context}

            Generate exactly {count} questions about 3R (Reduce, Reuse, Recycle) practices.
            Each question should:
            - Be directly based on the knowledge base content above
            - Be 10 words or less
            - End with a question mark
            - Be specific and actionable

            Provide exactly {count} questions, one per line.
            """

            response = self.llm_handler.generate_response(prompt)
            suggestions = [
                self._clean_suggestion(line.strip())
                for line in response.split('\n')
                if line.strip() and '?' in line
            ]

            if suggestions and len(suggestions) >= count:
                return suggestions[:count]

        except Exception as e:
            print(f"Error generating default suggestions: {e}")

        fallback_suggestions = [
            "How to reduce food waste at home?",
            "What items can I recycle in my area?",
            "How to reuse plastic containers?",
            "Tips for composting kitchen waste?",
            "How to reduce plastic use daily?"
        ]

        return fallback_suggestions[:count]