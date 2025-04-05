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
        prompt_template = """You are a waste management assistant. 
                    Use the following context to answer about waste management.

                    Context: {context}
                    Question: {question}

                    Guidelines:
                    - Provide ONLY the specific information requested
                    - Maximum 20-70 words
                    - Please provide a clear, complete, meaningful sentences
                    - NO introductions or explanatory phrases
                    - Be conversational and human-friendly
                    - Start with the direct answer
                    - Only include contact information if explicitly requested
                    - Include contact information only if explicitly requested
                    - For collection schedules, only state the specific day and time
                    - Answer directly without phrases like "Based on..." or "According to..." or "The answer is..." or "Answer: " or "Response: "
                    - NO extra details unless requested
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
        if self._is_feedback(message) or self._is_greeting(message) or self._is_thanks(message) or self._is_complaint(
                message):
            return True

        classification_prompt = f"""
        Task: Determine if the following question or message is related to waste management or environmental sustainability.

        It may fall under one or more of the following categories:
        - Waste management complaints (e.g., missed garbage pickup, overflowing bins)
        - Feedback or suggestions related to recycling or garbage disposal services
        - 3R (Reduce, Reuse, Recycle) tips or advice
        - Public awareness tips for sustainable or eco-friendly behavior
        - Waste collection schedules and timing inquiries
        - Greetings or general engagement messages related to waste or the environment

        Question: "{message}"

        Respond with ONLY "YES" if it's related to waste management or environmental sustainability in any of the above forms, otherwise respond with "NO".
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
        - Complaints: User is making a complaint about waste services (missed collections, poor service, etc.)
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
        prefixes = [
            "Answer: ",
            "Response: ",
            "Based on the information,",
            "According to the information,",
        ]

        for prefix in prefixes:
            if response.strip().startswith(prefix):
                response = response[len(prefix):].strip()

        response = re.sub(r'(\*{1,2}|_{1,2}|-{3,}|#{1,6}\s)', '', response)
        response = re.sub(r'^\d+\.\s*|\•\s*|\-\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'^[\'"]+|[\'"]+$', '', response)
        response = ' '.join(response.split())

        if response and len(response) > 0:
            response = response[0].upper() + response[1:]

        return response

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
        return any(greeting in message.lower() for greeting in greetings) and len(message.split()) < 5

    def _is_feedback(self, message):
        feedback_keywords = ['feedback', 'suggestion', 'improve', 'better', 'thanks', 'thank you', 'grateful',
                             'appreciate', 'good job', 'well done', 'helpful', 'service', 'experience']
        return any(keyword in message.lower() for keyword in feedback_keywords)

    def _is_thanks(self, message):
        thanks_keywords = ['thanks', 'thank you', 'appreciated', 'grateful', 'appreciate', 'valuable']
        return any(keyword in message.lower() for keyword in thanks_keywords) and len(message.split()) < 7

    def _is_complaint(self, message):
        complaint_keywords = ['complaint', 'issue', 'problem', 'not working', 'broken', 'failed', 'poor', 'missed',
                              'miss', 'disappointed', 'unhappy', 'dissatisfied', 'bad', 'terrible', 'horrible',
                              'didn\'t collect', 'didn\'t pick up', 'skipped', 'forgot', 'neglected']
        return any(keyword in message.lower() for keyword in complaint_keywords)

    def _check_relevance(self, query, document_content):
        query_terms = set(re.findall(r'\b\w{3,}\b', query.lower()))
        doc_terms = set(re.findall(r'\b\w{3,}\b', document_content.lower()))

        overlap = query_terms.intersection(doc_terms)

        waste_keywords = {'waste', 'recycle', 'trash', 'garbage', 'collect', 'bin'}
        important_overlap = overlap.intersection(waste_keywords)

        return len(overlap) >= 2 or len(important_overlap) >= 1

    def _validate_response_completeness(self, response, message):
        if not response.strip().endswith((".", "!", "?")):
            print("Response appears incomplete, attempting to complete it...")

            completion_prompt = f"""
            Original question: "{message}"

            Incomplete response: "{response}"

            Please complete this response in 1-2 sentences. Focus only on finishing
            what was being explained. Do not repeat information already given.
            """

            try:
                completion = self.llm_handler.generate_response(completion_prompt)

                last_fragment = response.split()[-3:] if len(response.split()) > 3 else response.split()
                last_fragment_text = " ".join(last_fragment).lower()

                completion_parts = completion.split()
                attach_point = 0
                for i in range(len(completion_parts) - len(last_fragment) + 1):
                    check_fragment = " ".join(completion_parts[i:i + len(last_fragment)]).lower()
                    if check_fragment == last_fragment_text:
                        attach_point = i + len(last_fragment)
                        break

                if attach_point > 0 and attach_point < len(completion_parts):
                    complete_response = f"{response} {' '.join(completion_parts[attach_point:])}"
                else:
                    complete_response = f"{response} {completion}"

                return self._clean_response(complete_response)
            except Exception as e:
                print(f"Error completing response: {e}")

        return response

    def process_message(self, message, session_id=None):
        try:
            if not session_id:
                session_id = str(uuid.uuid4())

            intent, confidence = self.classify_intent(message, session_id)

            if self.is_waste_management_related(message):
                documents = self.vector_store.similarity_search(message, k=3)

                relevant_content = ""
                for doc in documents:
                    relevant_content += doc.page_content + " "

                if not any(self._check_relevance(message, doc.page_content) for doc in documents):
                    print("Waste-related query with no relevant documents found")

                    fallback_prompt = f"""
                        Provide a brief, helpful response to this waste management question:
                        "{message}"
                        Guidelines:
                        - Maximum 40 words
                        - Please provide a clear, complete, meaningful sentences
                        - Direct, practical answer
                        - No introductory phrases (like "Based on..." or "The answer is..." or "Answer: " or "Response: ")
                        - Start with the main point
                        - If uncertain, provide general best practices
                        """

                    response = self.llm_handler.generate_response(fallback_prompt)
                    return self._clean_response(response)

            if self._is_greeting(message) and len(message.split()) < 5:
                return "Hello! How can I help with waste management today?"

            if self._is_thanks(message):
                return "Thank you for your feedback! Any other waste management questions?"

            if intent == "Feedback" and self._is_feedback(message):
                return "Thank you for your feedback! Any other waste management questions?"

            if intent == "Complaints" or self._is_complaint(message):
                print("Detected complaint, providing specialized response")

                if any(word in message.lower() for word in ['miss', 'missed', 'didn\'t collect', 'skipped', 'forgot']):
                    complaint_prompt = f"""
                            The user has submitted this complaint about missed collection: "{message}"

                            Create a 20-60 word response that:
                            1. Apologizes for the missed collection
                            2. Explains that it will be reported to the collection team
                            3. Assures the user it will be collected on the next scheduled day or sooner
                            4. Maintains a professional and empathetic tone
                            5. Please provide a clear, complete, meaningful sentences
                            """
                    return self._clean_response(self.llm_handler.generate_response(complaint_prompt))

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

                                    Create a 20-60 word response that:
                                    1. Acknowledges the issue briefly with empathy
                                    2. Provides the solution based ONLY on the information above
                                    3. Apologizes appropriately
                                    4. Maintains a professional tone
                                    5. Please provide a clear, complete, meaningful sentences
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

                                Please provide a clear, complete, meaningful and helpful response based ONLY on this information.
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
                                Please provide a clear, complete, meaningful sentences
                                Provide direct, practical advice relevant to waste management. 
                                Avoid unnecessary details or filler content.
                                """
                response = self.llm_handler.generate_response(enhancement_prompt)

            print(f"Raw response: {response}")
            response = self._clean_response(response)
            print(f"Cleaned response: {response}")

            response = self._validate_response_completeness(response, message)
            return response

        except Exception as e:
            print(f"Error processing message: {e}")
            return "I apologize, but I encountered an error. Please try again with your waste management question."
