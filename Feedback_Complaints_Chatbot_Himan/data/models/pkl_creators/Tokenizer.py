import pickle
import os
import pandas as pd
from tensorflow.keras.preprocessing.text import Tokenizer

from google.colab import files

uploaded = files.upload()

data = pd.read_excel('Waste Management Dataset.xlsx')

intent_phrases = data['Query'].tolist()

tokenizer = Tokenizer()
tokenizer.fit_on_texts(intent_phrases)

MODEL_PATH = "/content/model"
os.makedirs(MODEL_PATH, exist_ok=True)

tokenizer_path = os.path.join(MODEL_PATH, 'tokenizer.pkl')
with open(tokenizer_path, 'wb') as f:
    pickle.dump(tokenizer, f)

print(f"Tokenizer saved to {tokenizer_path}")
print(f"Vocabulary size: {len(tokenizer.word_index) + 1}")