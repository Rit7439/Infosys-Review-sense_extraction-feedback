import pandas as pd
import re
from text_preprocessing import TextPreprocessingPipeline

def parse_sentiment_data():
    """Parse the sentiment_analysis.csv with proper formatting issues"""
    print("=" * 60)
    print("PARSING SENTIMENT ANALYSIS DATA")
    print("=" * 60)
    
    data = []
    
    # Read the file
    with open('data/sentiment_analysis.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header and process each line
    for line in lines[1:]:
        line = line.strip()
        if not line or line == '""':
            continue
        
        # Remove the outer quotes
        line = line.strip('"')
        
        # Split by comma, but be careful with quoted fields
        parts = []
        current_part = ""
        in_quotes = False
        quote_count = 0
        
        for char in line:
            if char == '"':
                quote_count += 1
                if quote_count % 2 == 1:
                    in_quotes = True
                else:
                    in_quotes = False
            elif char == ',' and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
                continue
            current_part += char
        
        # Add the last part
        parts.append(current_part.strip())
        
        # Clean up the parts
        cleaned_parts = []
        for part in parts:
            part = part.strip('"').strip("'").strip()
            cleaned_parts.append(part)
        
        # Only add if we have the right number of fields
        if len(cleaned_parts) >= 7:
            data.append(cleaned_parts[:7])
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=['Text', 'Sentiment', 'Source', 'Date/Time', 'User ID', 'Location', 'Confidence Score'])
    
    print(f"Parsed: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Sentiment distribution:\n{df['Sentiment'].value_counts()}")
    
    return df

def main():
    """Main function to preprocess sentiment analysis data"""
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS DATA PREPROCESSING")
    print("Review Sense - Milestone 2: Text Processing")
    print("=" * 60)
    
    # Parse the sentiment data
    df = parse_sentiment_data()
    
    if df is None or len(df) == 0:
        print("Failed to parse sentiment data. Exiting.")
        return
    
    # Initialize preprocessing pipeline
    pipeline = TextPreprocessingPipeline()
    
    # Process the dataset
    df_processed = pipeline.process_dataset(df, text_column='Text')
    
    # Save results manually for sentiment data
    output_file = 'data/preprocessed_sentiment_analysis.csv'
    
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    try:
        df_processed.to_csv(output_file, index=False)
        print(f"Results saved to: {output_file}")
        print(f"Total rows saved: {len(df_processed)}")
        
        # Show sample results
        print("\nSample preprocessed texts:")
        sample_df = df_processed[['Text', 'processed_text']].head(10)
        for idx, row in sample_df.iterrows():
            print(f"\nOriginal: {row['Text'][:100]}...")
            print(f"Processed: {row['processed_text']}")
        
    except Exception as e:
        print(f"Error saving results: {e}")
        output_file = None
    
    print("\n" + "=" * 60)
    print("SENTIMENT ANALYSIS DATA PREPROCESSING COMPLETED!")
    print("=" * 60)
    print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
