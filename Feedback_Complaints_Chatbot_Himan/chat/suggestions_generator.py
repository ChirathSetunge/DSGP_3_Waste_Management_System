from .llm_handler import LLMHandler


class SuggestionsGenerator:
    def __init__(self):
        self.llm_handler = LLMHandler()

    def generate_suggestions(self, user_input, bot_response, max_suggestions=3):
        prompt = f"""
        You are a waste management assistant helping users with questions about recycling, 
        waste collection, and eco-friendly practices.

        Based on the following conversation, generate {max_suggestions} relevant follow-up questions 
        that the user might want to ask next. Keep them brief (under 10 words if possible) and 
        directly related to waste management.

        User input: {user_input}
        Your response: {bot_response}

        Provide exactly {max_suggestions} short follow-up questions, one per line.
        Do NOT use any formatting like bold, italics, quotes, or numbering.
        """

        try:
            response = self.llm_handler.generate_response(prompt)

            suggestions = [
                self._clean_suggestion(line.strip())
                for line in response.split('\n')
                if line.strip()
            ]

            suggestions = [
                s for s in suggestions
                if self._is_valid_suggestion(s)
            ]

            return suggestions[:max_suggestions] or [
                "How do I recycle electronics?",
                "When is my next collection day?",
                "Share eco-friendly tips"
            ]

        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return [
                "How do I recycle electronics?",
                "When is my next collection day?",
                "Share eco-friendly tips"
            ]

    def _clean_suggestion(self, suggestion):

        for char in ['*', '_', '`', '"', "'", '1.', '2.', '3.']:
            suggestion = suggestion.replace(char, '').strip()
        return suggestion

    def _is_valid_suggestion(self, suggestion):

        return (
                suggestion and
                '?' in suggestion or
                suggestion.lower().startswith(('how', 'what', 'when', 'where', 'why', 'can', 'show'))
        )