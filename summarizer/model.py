# summarizer/model.py

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# --- 1. Define the path and load the model ---
MODEL_PATH = "./my-fine-tuned-model"
print("Loading fine-tuned summarization model and tokenizer...")

try:
    # We need to load the tokenizer and model separately for chunking
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
    print("Fine-tuned model loaded successfully.")
except Exception as e:
    print(f"Error loading fine-tuned model: {e}")
    # Fallback in case something is wrong
    tokenizer = AutoTokenizer.from_pretrained("t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")

# Create the pipeline, which we'll use to summarize each chunk
summarizer_pipeline = pipeline(
    "summarization", 
    model=model, 
    tokenizer=tokenizer
)

# --- 2. Define Chunking Parameters ---
# The t5-small model has a 512 token limit. We'll use 450 to be safe.
MAX_TOKENS_PER_CHUNK = 450
# We overlap chunks to ensure no context is lost between them
OVERLAP_TOKENS = 50

def summarize_text(text_to_summarize):
    """
    Summarizes text of ANY length by recursively
    chunking and summarizing (Map-Reduce).
    """
    
    # 1. Tokenize the whole text to see how long it is
    # We add the prefix here to get an accurate token count
    prefixed_text = "summarize: " + text_to_summarize
    
    # We use the tokenizer directly to count tokens
    tokens = tokenizer(prefixed_text, return_tensors="pt")
    num_tokens = tokens.input_ids.shape[1]
    
    # 2. BASE CASE: If text is short enough, summarize it directly.
    if num_tokens <= MAX_TOKENS_PER_CHUNK:
        print(f"--- Text is short ({num_tokens} tokens). Performing final summary. ---")
        summary_result = summarizer_pipeline(
            prefixed_text, 
            min_length=40, 
            max_new_tokens=150, # Generate up to 150 new tokens
            do_sample=False
        )
        return summary_result[0]['summary_text']
        
    # 3. RECURSIVE CASE: Text is too long. Chunk it.
    print(f"--- Text is long ({num_tokens} tokens). Starting recursive chunking. ---")
    
    # Get all token IDs from the input
    token_ids = tokens.input_ids[0]
    
    chunks_of_token_ids = []
    # We "stride" over the text, creating chunks
    stride = MAX_TOKENS_PER_CHUNK - OVERLAP_TOKENS
    
    for i in range(0, num_tokens, stride):
        # Get a chunk of token IDs
        chunk = token_ids[i : i + MAX_TOKENS_PER_CHUNK]
        chunks_of_token_ids.append(chunk)
        
    # 4. Convert token chunks back into text strings
    text_chunks = [tokenizer.decode(chunk, skip_special_tokens=True) for chunk in chunks_of_token_ids]
    
    print(f"--- Split text into {len(text_chunks)} overlapping chunks. ---")
    
    # 5. Summarize each chunk (the "Map" step)
    list_of_mini_summaries = []
    for i, chunk in enumerate(text_chunks):
        print(f"Summarizing chunk {i+1}/{len(text_chunks)}...")
        # We must add the prefix back to each chunk
        chunk_with_prefix = "summarize: " + chunk
        
        chunk_summary = summarizer_pipeline(
            chunk_with_prefix,
            min_length=20,     # Shorter min_length for chunks
            max_new_tokens=75, # Shorter max_length for chunks
            do_sample=False
        )
        list_of_mini_summaries.append(chunk_summary[0]['summary_text'])
        
    # 6. Combine all mini-summaries (the "Combine" step)
    combined_summaries = " ".join(list_of_mini_summaries)
    
    # 7. Summarize the combined text (the "Reduce" step)
    # We call the function *itself* on the new, shorter text.
    print("--- Combining mini-summaries and performing final summary... ---")
    return summarize_text(combined_summaries) # This is the recursive call