import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer
)

# --- 1. Configuration ---
# THE FIX: Using the much smaller and faster t5-small model
MODEL_CHECKPOINT = "t5-small" 
DATA_FILE = "bbc_news_cleaned.csv"
NEW_MODEL_DIR = "./my-fine-tuned-model" 

# --- 2. Load and Prepare the Dataset ---
print("Loading dataset...")
df = pd.read_csv(DATA_FILE)
df = df.dropna()
raw_dataset = Dataset.from_pandas(df)

dataset_split = raw_dataset.train_test_split(test_size=0.1)
train_dataset = dataset_split['train']
eval_dataset = dataset_split['test']

print(f"Data loaded and split:")
print(f"Training examples: {len(train_dataset)}")
print(f"Validation examples: {len(eval_dataset)}")

# --- 3. Load Tokenizer ---
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)

# --- 4. Tokenize (Preprocess) the Data ---
MAX_INPUT_LENGTH = 1024
MAX_TARGET_LENGTH = 256
# T5 models require a prefix
prefix = "summarize: " 

def preprocess_function(examples):
    # --- T5 CHANGE: Add prefix to the article ---
    inputs = [prefix + doc for doc in examples['article']]
    
    model_inputs = tokenizer(
        inputs, 
        max_length=MAX_INPUT_LENGTH, 
        truncation=True, 
        padding="max_length"
    )
    
    # Tokenize the summaries (as labels)
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            examples['summary'], 
            max_length=MAX_TARGET_LENGTH, 
            truncation=True, 
            padding="max_length"
        )
    
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

print("Tokenizing datasets... (This may take a moment)")
tokenized_train_dataset = train_dataset.map(preprocess_function, batched=True)
tokenized_eval_dataset = eval_dataset.map(preprocess_function, batched=True)
print("Tokenizing complete.")

# --- 5. Load the Pre-trained Model ---
print(f"Loading pre-trained model: {MODEL_CHECKPOINT}")
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_CHECKPOINT)

# --- 6. Set Up Training ---
print("Setting up training arguments...")

data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

training_args = Seq2SeqTrainingArguments(
    output_dir=NEW_MODEL_DIR,
    eval_strategy="epoch",        
    learning_rate=2e-5,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=3,
    predict_with_generate=True,
    fp16=False,
    push_to_hub=False,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train_dataset,
    eval_dataset=tokenized_eval_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
)

# --- 7. Start Training ---
print("\n--- STARTING FINE-TUNING (T5-Small) ---")
print("This should be MUCH faster...")
trainer.train()
print("--- TRAINING COMPLETE ---")

# --- 8. Save the Final Model ---
print(f"Saving the final, fine-tuned model to {NEW_MODEL_DIR}")
trainer.save_model(NEW_MODEL_DIR)
print("Done.")