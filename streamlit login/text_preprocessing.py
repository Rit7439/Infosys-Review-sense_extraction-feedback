import pandas as pd
import numpy as np
import re
import warnings
warnings.filterwarnings('ignore')

# Import NLTK
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

# Import spaCy
try:
    import spacy
    nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])
    SPACY_AVAILABLE = True
except:
    SPACY_AVAILABLE = False
    print("SpaCy not available, using NLTK only")

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

# Get stopwords
stop_words = set(stopwords.words('english'))

class TextPreprocessingPipeline:
    """
    Text Preprocessing Pipeline for customer reviews
    Implements 5 stages: Load -> Clean -> Tokenize -> Remove Stopwords -> Lemmatize
    """
    
    def __init__(self):
        self.processed_texts = []
        
    def step1_load_data(self, file_path):
        """Step 1: Load uploaded data"""
        print("=" * 60)
        print("STEP 1: LOADING DATA")
        print("=" * 60)
        
        try:
            df = pd.read_csv(file_path)
            print(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"Columns: {list(df.columns)}")
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def step2_clean_normalize(self, text):
        """Step 2: Cleaning and Normalization"""
        if pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove special characters but keep letters, spaces, and basic punctuation
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def step3_tokenization(self, text):
        """Step 3: Tokenization"""
        if not text:
            return []
        
        # Use spaCy if available, otherwise NLTK
        if SPACY_AVAILABLE:
            doc = nlp(text)
            tokens = [token.text for token in doc]
        else:
            tokens = word_tokenize(text)
        
        return tokens
    
    def step4_remove_stopwords(self, tokens):
        """Step 4: Stopword Removal"""
        # Remove stopwords and keep only meaningful words
        filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
        
        # Remove very short tokens (less than 2 characters)
        filtered_tokens = [token for token in filtered_tokens if len(token) > 2]
        
        return filtered_tokens
    
    def step5_lemmatization(self, tokens):
        """Step 5: Lemmatization"""
        lemmatized_tokens = []
        for token in tokens:
            # Lemmatize the token
            lemma = lemmatizer.lemmatize(token.lower(), pos='v')  # verb
            lemma = lemmatizer.lemmatize(lemma, pos='n')  # noun
            lemma = lemmatizer.lemmatize(lemma, pos='a')  # adjective
            lemma = lemmatizer.lemmatize(lemma, pos='r')  # adverb
            lemmatized_tokens.append(lemma)
        
        return lemmatized_tokens
    
    def preprocess_text(self, text, return_as_list=False):
        """
        Complete preprocessing pipeline for a single text
        """
        # Step 2: Clean and normalize
        cleaned_text = self.step2_clean_normalize(text)
        
        # Step 3: Tokenize
        tokens = self.step3_tokenization(cleaned_text)
        
        # Step 4: Remove stopwords
        filtered_tokens = self.step4_remove_stopwords(tokens)
        
        # Step 5: Lemmatize
        lemmatized_tokens = self.step5_lemmatization(filtered_tokens)
        
        if return_as_list:
            return lemmatized_tokens
        else:
            return ' '.join(lemmatized_tokens)
    
    def process_dataset(self, df, text_column='reviewText'):
        """
        Process entire dataset through the pipeline
        """
        print("\n" + "=" * 60)
        print("PROCESSING TEXT THROUGH PIPELINE")
        print("=" * 60)
        
        # Check if column exists
        if text_column not in df.columns:
            print(f"Error: Column '{text_column}' not found in dataset")
            return df
        
        total_rows = len(df)
        print(f"Processing {total_rows} texts...")
        
        # Process each text
        processed_texts = []
        for idx, text in enumerate(df[text_column], 1):
            if idx % 100 == 0:
                print(f"Processed {idx}/{total_rows} texts...")
            
            processed = self.preprocess_text(text)
            processed_texts.append(processed)
        
        # Add processed column to dataframe
        df['processed_text'] = processed_texts
        
        print(f"\nProcessing complete! {total_rows} texts processed.")
        
        return df
    
    def save_results(self, df, output_file='data/preprocessed_reviews.csv'):
        """
        Save preprocessed results to CSV
        """
        print("\n" + "=" * 60)
        print("SAVING RESULTS")
        print("=" * 60)
        
        try:
            # Save the processed dataframe
            df.to_csv(output_file, index=False)
            print(f"Results saved to: {output_file}")
            print(f"Total rows saved: {len(df)}")
            
            # Show sample results
            print("\nSample preprocessed texts:")
            sample_df = df[['reviewText', 'processed_text']].head(10)
            for idx, row in sample_df.iterrows():
                print(f"\nOriginal: {row['reviewText'][:100]}...")
                print(f"Processed: {row['processed_text']}")
            
            return output_file
        except Exception as e:
            print(f"Error saving results: {e}")
            return None

def main():
    """
    Main function to run the preprocessing pipeline
    """
    print("\n" + "=" * 60)
    print("TEXT PREPROCESSING PIPELINE")
    print("Review Sense - Milestone 2: Text Processing")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = TextPreprocessingPipeline()
    
    # Step 1: Load data
    file_path = 'data/amazon_reviews.csv'
    df = pipeline.step1_load_data(file_path)
    
    if df is None:
        print("Failed to load data. Exiting.")
        return
    
    # Process dataset
    df_processed = pipeline.process_dataset(df, text_column='reviewText')
    
    # Save results
    output_file = pipeline.save_results(df_processed, output_file='data/preprocessed_reviews.csv')
    
    print("\n" + "=" * 60)
    print("PREPROCESSING PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Results saved to: {output_file}")
    print("\nNext steps:")
    print("1. Review the preprocessed_reviews.csv file")
    print("2. Integrate results with Streamlit frontend")
    print("3. Proceed to sentiment analysis")

if __name__ == "__main__":
    main()
