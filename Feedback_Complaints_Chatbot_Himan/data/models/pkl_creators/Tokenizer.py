import pickle
import os
import pandas as pd
from tensorflow.keras.preprocessing.text import Tokenizer
from config import Config

# Load the data - adjust path as needed
data = pd.read_excel('shuffled_text_queries.xlsx')

# Extract the query texts
intent_phrases = data['Query'].tolist()

# Create and fit tokenizer
tokenizer = Tokenizer()
tokenizer.fit_on_texts(intent_phrases)

# Create directory if it doesn't exist
os.makedirs(Config.MODEL_PATH, exist_ok=True)

# Save tokenizer
tokenizer_path = os.path.join(Config.MODEL_PATH, 'tokenizer.pkl')
with open(tokenizer_path, 'wb') as f:
    pickle.dump(tokenizer, f)

print(f"Tokenizer saved to {tokenizer_path}")
print(f"Vocabulary size: {len(tokenizer.word_index) + 1}")  # +1 for the reserved 0 index