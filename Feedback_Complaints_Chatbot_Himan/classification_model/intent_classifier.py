import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from sklearn.model_selection import train_test_split, KFold
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import (
    Embedding, Bidirectional, LSTM, Dense, Dropout,
    BatchNormalization, SpatialDropout1D, Conv1D,
    MaxPooling1D, GlobalMaxPooling1D, concatenate,
    Input, Add
)
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
)
from tensorflow.keras.regularizers import l2
from tensorflow.keras.optimizers import Adam
import re
import warnings
import os
from sklearn.metrics import confusion_matrix, classification_report
import itertools

np.random.seed(42)
tf.random.set_seed(42)
warnings.filterwarnings('ignore')

GLOVE_EMBEDDINGS_PATH = 'glove.6B.100d.txt'
MODEL_SAVE_PATH = 'model/best_intent_model.h5'

def load_and_preprocess_data(file_path):
    data = pd.read_excel(file_path)
    print("Dataset shape:", data.shape)
    print("\nClass distribution:")
    print(data['Category'].value_counts())
    return data

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()

def prepare_text_data(data):
    data['Query'] = data['Query'].apply(clean_text)

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(data['Query'])

    sequences = tokenizer.texts_to_sequences(data['Query'])
    max_sequence_length = max(len(seq) for seq in sequences)
    X = pad_sequences(sequences, maxlen=max_sequence_length, padding='post')

    intent_labels = list(set(data['Category']))
    intent_to_index = {intent: i for i, intent in enumerate(intent_labels)}
    y = np.array([intent_to_index[intent] for intent in data['Category']])

    return X, y, tokenizer, max_sequence_length, intent_labels, intent_to_index

def augment_text(text, max_augmented=2):
    augmented = [text]
    words = text.split()

    if len(words) > 3:
        dropped = words.copy()
        drop_idx = np.random.randint(0, len(words))
        dropped.pop(drop_idx)
        augmented.append(' '.join(dropped))

    if len(words) > 3:
        shuffled = words.copy()
        np.random.shuffle(shuffled)
        augmented.append(' '.join(shuffled))

    return augmented[:max_augmented]

def augment_dataset(X, y, tokenizer, max_sequence_length):
    augmented_texts = []
    augmented_labels = []

    original_texts = []
    for seq in X:
        text = []
        for idx in seq:
            if idx != 0:
                for word, word_idx in tokenizer.word_index.items():
                    if word_idx == idx:
                        text.append(word)
                        break
        original_texts.append(' '.join(text))

    for text, label in zip(original_texts, y):
        aug_texts = augment_text(text)
        augmented_texts.extend(aug_texts)
        augmented_labels.extend([label] * len(aug_texts))

    aug_sequences = tokenizer.texts_to_sequences(augmented_texts)
    X_aug = pad_sequences(aug_sequences, maxlen=max_sequence_length, padding='post')
    y_aug = np.array(augmented_labels)

    return X_aug, y_aug

def load_glove_embeddings(word_index, embedding_dim=94):
    if not os.path.exists(GLOVE_EMBEDDINGS_PATH):
        print(f"Warning: GloVe embeddings file {GLOVE_EMBEDDINGS_PATH} not found.")
        return None

    embeddings_index = {}
    try:
        with open(GLOVE_EMBEDDINGS_PATH, encoding='utf-8') as f:
            first_line = next(f)
            actual_dim = len(first_line.split()) - 1
            if actual_dim != embedding_dim:
                print(f"Warning: Expected embedding dimension {embedding_dim} but found {actual_dim}")
                embedding_dim = actual_dim

            f.seek(0)

            for line in f:
                values = line.split()
                word = values[0]
                coefs = np.asarray(values[1:], dtype='float32')
                embeddings_index[word] = coefs

        embedding_matrix = np.zeros((len(word_index) + 1, embedding_dim))
        for word, i in word_index.items():
            embedding_vector = embeddings_index.get(word)
            if embedding_vector is not None:
                embedding_matrix[i] = embedding_vector

        return embedding_matrix
    except Exception as e:
        print(f"Error loading GloVe embeddings: {e}")
        return None

def create_enhanced_model(vocab_size, embedding_dim, max_sequence_length, num_classes, embedding_matrix=None):

    input_layer = Input(shape=(max_sequence_length,))

    embedding = Embedding(
        input_dim=vocab_size,
        output_dim=embedding_dim,
        input_length=max_sequence_length,
        weights=[embedding_matrix] if embedding_matrix is not None else None,
        trainable=False if embedding_matrix is not None else True
    )(input_layer)

    embedding_dropout = SpatialDropout1D(0.2)(embedding)

    conv1 = Conv1D(128, 3, activation='relu', padding='same')(embedding_dropout)
    pool1 = MaxPooling1D(2)(conv1)
    conv2 = Conv1D(64, 3, activation='relu', padding='same')(pool1)
    global_pool1 = GlobalMaxPooling1D()(conv2)

    conv3 = Conv1D(128, 5, activation='relu', padding='same')(embedding_dropout)
    pool2 = MaxPooling1D(2)(conv3)
    conv4 = Conv1D(64, 5, activation='relu', padding='same')(pool2)
    global_pool2 = GlobalMaxPooling1D()(conv4)

    lstm1 = Bidirectional(LSTM(128, return_sequences=True,
                              kernel_regularizer=l2(1e-4)))(embedding_dropout)
    bn1 = BatchNormalization()(lstm1)
    lstm2 = Bidirectional(LSTM(64, return_sequences=False,
                              kernel_regularizer=l2(1e-4)))(bn1)
    bn2 = BatchNormalization()(lstm2)

    merged = concatenate([global_pool1, global_pool2, bn2])

    dense1 = Dense(128, activation='relu', kernel_regularizer=l2(1e-4))(merged)
    dropout1 = Dropout(0.4)(dense1)
    bn3 = BatchNormalization()(dropout1)

    dense2 = Dense(64, activation='relu', kernel_regularizer=l2(1e-4))(bn3)
    dropout2 = Dropout(0.3)(dense2)
    bn4 = BatchNormalization()(dropout2)

    output_layer = Dense(num_classes, activation='softmax')(bn4)

    model = Model(inputs=input_layer, outputs=output_layer)

    optimizer = Adam(
        learning_rate=0.0001,
        clipnorm=1.0,
        beta_1=0.9,
        beta_2=0.999,
        epsilon=1e-7
    )

    model.compile(
        optimizer=optimizer,
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    return model

def get_enhanced_training_config():
    return {
        'batch_size': 64,
        'epochs': 150,
        'callbacks': [
            EarlyStopping(
                monitor='val_loss',
                patience=8,
                restore_best_weights=True,
                min_delta=1e-5
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.2,
                patience=5,
                min_lr=1e-7,
                verbose=1
            ),
            ModelCheckpoint(
                MODEL_SAVE_PATH,
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            )
        ]
    }

def plot_confusion_matrix(y_true, y_pred, classes, normalize=False, title='Confusion Matrix'):
    cm = confusion_matrix(y_true, y_pred)
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='.2f' if normalize else 'd',
                cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.title(title)
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.show()

def plot_training_metrics(history, fold=None):
    metrics = ['loss', 'accuracy' if 'accuracy' in history.history else 'acc']

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f'Training Metrics {f"(Fold {fold})" if fold else ""}')

    for idx, metric in enumerate(metrics):
        axes[idx].plot(history.history[metric], label='Train')
        axes[idx].plot(history.history.get(f'val_{metric}', []), label='Validation')
        axes[idx].set_title(f'Model {metric.capitalize()}')
        axes[idx].set_xlabel('Epoch')
        axes[idx].set_ylabel(metric.capitalize())
        axes[idx].legend()

    plt.tight_layout()
    plt.show()

def train_enhanced_model(X, y, vocab_size, embedding_dim, max_sequence_length,
                         num_classes, embedding_matrix=None, n_splits=5):
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    fold_scores = []
    training_config = get_enhanced_training_config()
    all_predictions = []
    all_true_labels = []

    for fold, (train_idx, val_idx) in enumerate(kfold.split(X)):
        print(f'\nTraining fold {fold + 1}/{n_splits}')

        # Split data
        X_fold_train, y_fold_train = X[train_idx], y[train_idx]
        X_fold_val, y_fold_val = X[val_idx], y[val_idx]

        class_weights = compute_class_weight(
            class_weight="balanced",
            classes=np.unique(y_fold_train),
            y=y_fold_train
        )
        class_weight_dict = dict(enumerate(class_weights))

        model = create_enhanced_model(
            vocab_size, embedding_dim, max_sequence_length,
            num_classes, embedding_matrix
        )

        history = model.fit(
            X_fold_train, y_fold_train,
            validation_data=(X_fold_val, y_fold_val),
            class_weight=class_weight_dict,
            **training_config
        )

        val_loss, val_acc = model.evaluate(X_fold_val, y_fold_val)
        fold_scores.append(val_acc)

        y_pred = np.argmax(model.predict(X_fold_val), axis=1)
        all_predictions.extend(y_pred)
        all_true_labels.extend(y_fold_val)

        plot_training_metrics(history, fold + 1)

    plot_confusion_matrix(
        all_true_labels, all_predictions,
        classes=range(num_classes),
        normalize=True,
        title='Overall Normalized Confusion Matrix'
    )

    print(f'\nClassification Report:')
    print(classification_report(all_true_labels, all_predictions))
    print(f'\nAverage validation accuracy: {np.mean(fold_scores):.4f} ± {np.std(fold_scores):.4f}')

    return fold_scores

def predict_intent(text, model, tokenizer, max_sequence_length, intent_labels):
    cleaned_text = clean_text(text)
    sequence = tokenizer.texts_to_sequences([cleaned_text])
    padded_sequence = pad_sequences(sequence, maxlen=max_sequence_length, padding='post')

    prediction = model.predict(padded_sequence)
    predicted_class = np.argmax(prediction[0])
    confidence = prediction[0][predicted_class]

    return intent_labels[predicted_class], confidence

def main():
    data = load_and_preprocess_data("shuffled_text_queries.xlsx")
    X, y, tokenizer, max_sequence_length, intent_labels, intent_to_index = prepare_text_data(data)

    embedding_dim = 100
    vocab_size = len(tokenizer.word_index) + 1
    num_classes = len(intent_labels)
    embedding_matrix = load_glove_embeddings(tokenizer.word_index, embedding_dim)

    X_aug, y_aug = augment_dataset(X, y, tokenizer, max_sequence_length)

    fold_scores = train_enhanced_model(
        X_aug, y_aug,
        vocab_size, embedding_dim, max_sequence_length,
        num_classes, embedding_matrix
    )

    if os.path.exists(MODEL_SAVE_PATH):
        best_model = load_model(MODEL_SAVE_PATH)
        test_query = "How do I properly dispose of electronic waste?"
        intent, confidence = predict_intent(
            test_query, best_model, tokenizer,
            max_sequence_length, intent_labels
        )
        print(f"\nTest Query: {test_query}")
        print(f"Predicted Intent: {intent}")
        print(f"Confidence: {confidence:.2f}")
    else:
        print("No saved model found. Please train the model first.")

    return tokenizer, intent_labels, intent_to_index

if __name__ == "__main__":
    main()