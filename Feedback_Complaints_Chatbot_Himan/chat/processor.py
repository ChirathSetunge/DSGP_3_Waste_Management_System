from .document_processor import DocumentProcessor
from .llm_handler import LLMHandler
from .intent_classifier import IntentClassifier
from .intent_database import UserIntent
from shared import db
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import os
from Feedback_Complaints_Chatbot_Himan.config import Config
import uuid
import re


class ChatProcessor:
    def __init__(self):
        self.doc_processor = DocumentProcessor(
            knowledge_base_path=os.getenv('KNOWLEDGE_BASE_PATH', Config.KNOWLEDGE_BASE_PATH),
            vector_store_path=os.getenv('VECTOR_STORE_PATH', Config.VECTOR_STORE_PATH)
        )
        self.llm_handler = LLMHandler()
        self.vector_store = self.initialize_vector_store()
        self.qa_chain = self.setup_qa_chain()
        self.intent_classifier = IntentClassifier()

    def initialize_vector_store(self):
        vector_store = self.doc_processor.load_vector_store()
        if not vector_store:
            vector_store = self.doc_processor.process_and_store()
        return vector_store

    def setup_qa_chain(self):
        prompt_template = """You are a knowledgeable waste management assistant for the EcoChat application. 
                Use the following context to answer the question. If you can't find the answer in the context, provide a general response based on 
                common waste management practices.

                Context: {context}
                Question: {question}

                Guidelines for response:
                - Provide a clear and direct answer
                - Be concise and to the point
                - Avoid unnecessary elaboration or filler content
                - Focus on delivering practical, actionable information
                - Use a professional and conversational tone
                - Do not start with words like 'Answer:' or 'Response:'
                - Speak directly to the user in a friendly manner
                """
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        return RetrievalQA.from_chain_type(
            llm=self.llm_handler.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            ),
            chain_type_kwargs={"prompt": PROMPT}
        )

    def is_waste_management_related(self, message):
        classification_prompt = f"""
        Task: Determine if the following question is related to waste management, recycling, garbage disposal, 
        or environmental sustainability.

        Question: "{message}"

        Respond with ONLY "YES" if it's related to waste management or "NO" if it's not related.
        """
        try:
            response = self.llm_handler.generate_response(classification_prompt)
            return "YES" in response.strip().upper()
        except Exception as e:
            print(f"Error in classification: {e}")
            return True

    def classify_intent(self, message, session_id=None):
        intent, confidence = self.intent_classifier.predict_intent(message)
        if intent != "unknown":
            try:
                user_intent = UserIntent(
                    user_message=message,
                    predicted_intent=intent,
                    confidence=confidence,
                    session_id=session_id
                )
                db.session.add(user_intent)
                db.session.commit()
                print(f"Intent saved: {intent} (confidence: {confidence:.2f})")
            except Exception as e:
                print(f"Error saving intent to database: {e}")
                db.session.rollback()
        return intent, confidence

    def _clean_response(self, response):
        response = re.sub(r'-{3,}', '', response)
        response = re.sub(r'(\*{1,2}|_{1,2})', '', response)
        response = re.sub(r'^\d+\.\s*', '', response, flags=re.MULTILINE)
        response = response.strip('"').strip("'")
        response = ' '.join(response.split())
        return response

    def process_message(self, message, session_id=None):
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            if self._is_greeting(message):
                self.classify_intent(message, session_id)
                return ("Hello! I'm your waste management assistant. How can I help you today with waste management, "
                        "recycling, or disposal questions?")

            if not self.is_waste_management_related(message):
                self.classify_intent(message, session_id)
                return ("I'm specifically designed to help with waste management questions. Could you please ask me "
                        "something related to waste disposal, recycling, or environmental sustainability?")

            intent, confidence = self.classify_intent(message, session_id)
            response = self.qa_chain.run(message)

            if len(response.split()) < 10:
                enhancement_prompt = f"""
                The user asked about: "{message}"

                Your initial response was: "{response}"

                Please enhance this response to be more helpful, but remain concise. 
                Provide direct, practical advice relevant to waste management. 
                Avoid unnecessary details or filler content.
                """
                response = self.llm_handler.generate_response(enhancement_prompt)

            response = self._clean_response(response)

            return response

        except Exception as e:
            print(f"Error processing message: {e}")
            return "I apologize, but I encountered an error. Please try again with your waste management question."

    def _is_greeting(self, message):
        greetings = ['hello', 'hi', 'hey', 'greetings', 'howdy', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in message.lower() for greeting in greetings)