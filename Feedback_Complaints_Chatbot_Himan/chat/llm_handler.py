from langchain_huggingface import HuggingFaceEndpoint
import os


class LLMHandler:
    def __init__(self):
        self.llm = HuggingFaceEndpoint(
            endpoint_url="https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
            max_length=50,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.15
        )

    def generate_response(self, prompt):
        try:
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            response = self.llm(formatted_prompt)

            if isinstance(response, str):
                response = response.replace("[INST]", "").replace("[/INST]", "").strip()

            return response
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I encountered an error. Please try again."
