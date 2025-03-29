import pickle
import os
import pandas as pd
from Feedback_Complaints_Chatbot_Himan.config import Config

# Load the data - adjust path as needed
data = pd.read_excel('shuffled_text_queries.xlsx')

# Extract unique categories/intents
intent_labels = sorted(data['Category'].unique().tolist())

print(f"Found {len(intent_labels)} unique intent categories:")
for i, label in enumerate(intent_labels):
    print(f"{i+1}. {label}")

# Create directory if it doesn't exist
os.makedirs(Config.MODEL_PATH, exist_ok=True)

# Save labels
labels_path = os.path.join(Config.MODEL_PATH, 'intent_labels.pkl')
with open(labels_path, 'wb') as f:
    pickle.dump(intent_labels, f)

print(f"Intent labels saved to {labels_path}")