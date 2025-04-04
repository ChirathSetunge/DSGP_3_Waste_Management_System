import pickle
import os
import pandas as pd
from google.colab import files

uploaded = files.upload()

data = pd.read_excel('Waste Management Dataset.xlsx')

intent_labels = sorted(data['Category'].unique().tolist())

print(f"Found {len(intent_labels)} unique intent categories:")
for i, label in enumerate(intent_labels):
    print(f"{i+1}. {label}")

MODEL_PATH = "/content/model"
os.makedirs(MODEL_PATH, exist_ok=True)

labels_path = os.path.join(MODEL_PATH, 'intent_labels.pkl')
with open(labels_path, 'wb') as f:
    pickle.dump(intent_labels, f)

print(f"Intent labels saved to {labels_path}")