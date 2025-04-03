import tensorflow as tf
import numpy as np
import pickle
import os
from Feedback_Complaints_Chatbot_Himan.config import Config

load_model = tf.keras.models.load_model
pad_sequences = tf.keras.utils.pad_sequences


class IntentClassifier:
    def __init__(self, model_path=None, tokenizer_path=None, labels_path=None):
        self.model_path = model_path or os.path.join(Config.MODEL_PATH, 'best_intent_model (1).h5')
        self.tokenizer_path = tokenizer_path or os.path.join(Config.MODEL_PATH, 'tokenizer.pkl')
        self.labels_path = labels_path or os.path.join(Config.MODEL_PATH, 'intent_labels.pkl')

        self.model = self._load_model()
        self.tokenizer = self._load_tokenizer()
        self.labels = self._load_labels()

        self.max_sequence_length = 10

    def _load_model(self):
        try:
            model = load_model(self.model_path)
            print(f"Intent classification model loaded from {self.model_path}")
            return model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None

    def _load_tokenizer(self):
        try:
            with open(self.tokenizer_path, 'rb') as f:
                tokenizer = pickle.load(f)
            print(f"Tokenizer loaded from {self.tokenizer_path}")
            return tokenizer
        except Exception as e:
            print(f"Error loading tokenizer: {e}")
            return None

    def _load_labels(self):
        try:
            with open(self.labels_path, 'rb') as f:
                labels = pickle.load(f)
            print(f"Intent labels loaded from {self.labels_path}")
            return labels
        except Exception as e:
            print(f"Error loading labels: {e}")
            return None

    def predict_intent(self, text):
        if not self.model or not self.tokenizer or not self.labels:
            print("Model, tokenizer, or labels not loaded correctly")
            return "unknown", 0.0

        try:
            sequences = self.tokenizer.texts_to_sequences([text])
            padded_sequences = pad_sequences(sequences, maxlen=self.max_sequence_length)

            prediction = self.model.predict(padded_sequences)[0]
            predicted_class_index = np.argmax(prediction)
            confidence_score = prediction[predicted_class_index]

            predicted_intent = self.labels[predicted_class_index]

            return predicted_intent, float(confidence_score)
        except Exception as e:
            print(f"Error predicting intent: {e}")
            return "unknown", 0.0