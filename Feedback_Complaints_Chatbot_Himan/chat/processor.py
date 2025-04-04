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
            print("Vector store not found or empty. Creating new vector store...")
            vector_store = self.doc_processor.process_and_store()
        else:
            print("Vector store loaded successfully")
        return vector_store

    def setup_qa_chain(self):
        prompt_template = """You are a knowledgeable waste management assistant for the EcoChat application. 
                Use the following context to answer the question about waste management. 

                Context: {context}
                Question: {question}

                Guidelines for response:
                - If the information exists in the context, provide that EXACT information
                - For collection schedules, always provide the specific day and time from the context
                - Do not make up or infer information that isn't in the context
                - If the information isn't in the context, state clearly that you don't have that specific information
                - Use a professional and conversational tone
                - Speak directly to the user in a friendly manner
                - Do not start with words like 'Answer:' or 'Response:'
                """
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        return RetrievalQA.from_chain_type(
            llm=self.llm_handler.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 5}
            ),
            chain_type_kwargs={"prompt": PROMPT}
        )

    def is_waste_management_related(self, message):
        if self._is_feedback(message) or self._is_greeting(message) or self._is_thanks(message):
            return True

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
        verified_intent = self._verify_intent_with_llm(message, intent)
        if verified_intent != intent:
            intent = verified_intent
            confidence = 0.85
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

    def _verify_intent_with_llm(self, message, original_intent):
        available_intents = [
            "Complaints", "Feedback", "3R Tips", "Public Awareness Tips",
            "Waste Collection Schedules", "Greetings", "Unknown"
        ]
        intent_prompt = f"""
        Task: Classify the following message into one of these EXACT intent categories:
        - Complaints: User is making a complaint about waste services
        - Feedback: User is providing feedback or suggestions
        - 3R Tips: User is asking about Reduce, Reuse, Recycle tips
        - Public Awareness Tips: User is asking about waste management awareness
        - Waste Collection Schedules: User is asking about collection times or dates
        - Greetings: User is just saying hello or starting conversation
        - Unknown: Message doesn't fit any other category

        Message: "{message}"

        Original classification: {original_intent}

        Return ONLY the intent category name from the list above - exactly as written.
        Choose the most appropriate category based on the message content.
        """

        try:
            response = self.llm_handler.generate_response(intent_prompt)
            verified_intent = response.strip().split('\n')[0].strip()

            for intent in available_intents:
                if intent.lower() in verified_intent.lower():
                    return intent

            return original_intent
        except Exception as e:
            print(f"Error in intent verification: {e}")
            return original_intent

    def _clean_response(self, response):
        response = re.sub(r'^(Answer:|Response:|Based on the provided information, )\s*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'-{3,}', '', response)
        response = re.sub(r'(\*{1,2}|_{1,2})', '', response)
        response = re.sub(r'^\d+\.\s*', '', response, flags=re.MULTILINE)
        response = response.strip('"').strip("'")
        response = ' '.join(response.split())
        return response

    def test_retrieval(self, query):
        documents = self.vector_store.similarity_search(query, k=5)
        print(f"Retrieved {len(documents)} documents for query: '{query}'")
        for i, doc in enumerate(documents):
            print(f"Document {i + 1} content: {doc.page_content}")
            print(f"Document {i + 1} metadata: {doc.metadata}")
            print("-" * 50)
        return documents

    def get_schedule_from_knowledge_base(self, waste_type=None):
        query = "waste collection schedule"
        if waste_type:
            query = f"{waste_type} waste collection schedule"

        documents = self.vector_store.similarity_search(query, k=5)

        schedule_info = ""
        for doc in documents:
            if "collection" in doc.page_content.lower() and "schedule" in doc.page_content.lower():
                schedule_info += doc.page_content + "\n"

        return schedule_info

    def _is_schedule_query(self, message):
        schedule_keywords = ["schedule", "collection", "pickup", "pick up", "collect",
                             "garbage day", "trash day", "when", "what day", "what time",
                             "organic waste", "inorganic waste", "e-waste"]

        return any(keyword in message.lower() for keyword in schedule_keywords)

    def _is_greeting(self, message):
        greetings = ['hello', 'hi', 'hey', 'greetings', 'howdy', 'good morning', 'good afternoon', 'good evening']
        return any(greeting in message.lower() for greeting in greetings)

    def _is_feedback(self, message):
        feedback_keywords = ['feedback', 'suggestion', 'improve', 'better', 'thanks', 'thank you', 'grateful',
                             'appreciate', 'good job', 'well done', 'helpful', 'service', 'experience']
        return any(keyword in message.lower() for keyword in feedback_keywords)

    def _is_thanks(self, message):
        thanks_keywords = ['thanks', 'thank you', 'appreciated', 'grateful', 'appreciate', 'valuable']
        return any(keyword in message.lower() for keyword in thanks_keywords)

    def _is_complaint(self, message):
        complaint_keywords = ['complaint', 'issue', 'problem', 'not working', 'broken', 'failed', 'poor',
                              'disappointed', 'unhappy', 'dissatisfied', 'bad', 'terrible', 'horrible']
        return any(keyword in message.lower() for keyword in complaint_keywords)

    def process_message(self, message, session_id=None):
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            intent, confidence = self.classify_intent(message, session_id)

            if self._is_greeting(message):
                return ("Hello! I'm your waste management assistant. How can I help you today with waste management, "
                        "recycling, or disposal questions?")

            if self._is_thanks(message) or (intent == "Feedback" and self._is_feedback(message)):
                print("Detected feedback/thanks, providing acknowledgment")
                return (
                    "Thank you for your feedback! I'm glad I could be of assistance with your waste management needs. "
                    "Is there anything else I can help you with regarding waste disposal, recycling, or sustainability?")

            if intent == "Complaints" or self._is_complaint(message):
                print("Detected complaint, providing specialized response")
                documents = self.vector_store.similarity_search(message, k=5)
                solution_found = False

                for doc in documents:
                    if any(keyword in doc.page_content.lower() for keyword in
                           ["solution", "resolve", "fix", "address"]):
                        solution_found = True
                        solution_prompt = f"""
                        The user has submitted this complaint: "{message}"

                        Here is information that might help address it:
                        {doc.page_content}

                        Please create a response that:
                        1. Acknowledges the issue with empathy
                        2. Provides the solution based ONLY on the information above
                        3. Apologizes appropriately
                        4. Maintains a professional tone
                        """
                        return self._clean_response(self.llm_handler.generate_response(solution_prompt))

                if not solution_found:
                    return (
                        "I apologize for the issue you're experiencing. I don't have a specific solution in my knowledge base "
                        "for this particular problem. To help you better, would you mind providing your contact details? "
                        "Our waste management team will reach out to you directly to address your concern.")

            if not self.is_waste_management_related(message):
                return ("I'm specifically designed to help with waste management questions. Could you please ask me "
                        "something related to waste disposal, recycling, or environmental sustainability?")

            if intent == "Waste Collection Schedules" or self._is_schedule_query(message):
                print("Detected schedule query, searching knowledge base directly")

                waste_type = None
                if "organic" in message.lower():
                    waste_type = "organic"
                elif "inorganic" in message.lower():
                    waste_type = "inorganic"
                elif "e-waste" in message.lower() or "electronic" in message.lower():
                    waste_type = "e-waste"

                schedule_info = self.get_schedule_from_knowledge_base(waste_type)

                if schedule_info:
                    print(f"Found schedule info: {schedule_info}")
                    response_prompt = f"""
                    The user asked: "{message}"

                    Here is the collection schedule information:
                    {schedule_info}

                    Please provide a clear and helpful response based ONLY on this information.
                    If specific days or times are mentioned in the information, include those exact details.
                    Format the schedule clearly for the user.
                    """
                    return self._clean_response(self.llm_handler.generate_response(response_prompt))

            print("Using standard QA chain for response")
            response = self.qa_chain.run(message)

            if len(response.split()) < 10:
                print("Response too short, enhancing...")
                enhancement_prompt = f"""
                The user asked about: "{message}"

                Your initial response was: "{response}"

                Please enhance this response to be more helpful, but remain concise. 
                Provide direct, practical advice relevant to waste management. 
                Avoid unnecessary details or filler content.
                """
                response = self.llm_handler.generate_response(enhancement_prompt)

            print(f"Raw response: {response}")
            response = self._clean_response(response)
            print(f"Cleaned response: {response}")

            return response

        except Exception as e:
            print(f"Error processing message: {e}")
            return "I apologize, but I encountered an error. Please try again with your waste management question."