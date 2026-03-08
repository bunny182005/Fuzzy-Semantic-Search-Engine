"""
Data Preprocessing Module

This module handles cleaning and preparing the 20 Newsgroups dataset.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd


class NewsGroupPreprocessor:
    """Handles cleaning and preprocessing of 20 Newsgroups data."""

    def __init__(self):
        self.email_pattern = re.compile(r'\S+@\S+')
        self.url_pattern = re.compile(r'http[s]?://\S+')
        self.header_pattern = re.compile(
    r'^(From|Subject|Date|Organization|Lines|Distribution|NNTP-Posting-Host|Path|X-.*?):\s*.+$',
    re.MULTILINE
)

    def remove_headers(self, text: str) -> Tuple[str, str]:
        """Extract subject and remove email headers."""
        subject = ""

        subject_match = re.search(r'^Subject:\s*(.+)$', text, re.MULTILINE)
        if subject_match:
            subject = subject_match.group(1).strip()

        text = self.header_pattern.sub('', text)

        return text, subject

    def remove_quoted_text(self, text: str) -> str:
        """Remove lines starting with > (quoted previous messages)."""

        lines = text.split('\n')
        filtered_lines = [line for line in lines if not line.strip().startswith('>')]

        return '\n'.join(filtered_lines)

    def remove_signatures(self, text: str) -> str:
        """Remove email signatures."""

        if '\n--\n' in text:
            text = text.split('\n--\n')[0]
        elif '\n-- \n' in text:
            text = text.split('\n-- \n')[0]

        return text

    def clean_text(self, text: str) -> str:
        """Apply all cleaning steps to a single document."""

        text = self.url_pattern.sub('', text)
        text = self.email_pattern.sub('', text)

        text, subject = self.remove_headers(text)

        text = self.remove_quoted_text(text)
        text = self.remove_signatures(text)

        text = re.sub(r'\s+', ' ', text).strip()

        if subject:
            text = f"{subject} {text}"

        return text

    def load_and_clean_dataset(self, data_path: str) -> pd.DataFrame:
        """
        Load dataset from extracted UCI files.

        Args:
            data_path: path to extracted 20_newsgroups folder
        """

        print(f"Loading dataset from {data_path}")

        data_path = Path(data_path)

        cleaned_docs = []
        doc_id = 0

        for category_folder in data_path.iterdir():

            if not category_folder.is_dir():
                continue

            category = category_folder.name

            for file in category_folder.iterdir():

                try:
                    with open(file, "r", encoding="latin1") as f:
                        text = f.read()
                except:
                    continue

                cleaned = self.clean_text(text)

                if len(cleaned) < 50:
                    continue

                cleaned_docs.append({
                    "doc_id": doc_id,
                    "text": cleaned,
                    "category": category,
                    "original_text": text,
                    "length": len(cleaned)
                })

                doc_id += 1

        df = pd.DataFrame(cleaned_docs)

        print(f"Loaded {len(df)} cleaned documents")
        print(f"Categories: {df['category'].nunique()}")

        return df

    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """Get basic statistics about the cleaned dataset."""

        return {
            'total_documents': len(df),
            'unique_categories': df['category'].nunique(),
            'avg_length': df['length'].mean(),
            'min_length': df['length'].min(),
            'max_length': df['length'].max(),
            'category_distribution': df['category'].value_counts().to_dict()
        }


if __name__ == "__main__":

    preprocessor = NewsGroupPreprocessor()

    df = preprocessor.load_and_clean_dataset("../data/raw/20_newsgroups")

    output_path = "../data/processed/cleaned_newsgroups.parquet"

    df.to_parquet(output_path, index=False)

    print(f"\nSaved cleaned data to {output_path}")

    stats = preprocessor.get_statistics(df)

    print("\nDataset Statistics:")

    for key, value in stats.items():
        if key != "category_distribution":
            print(f"{key}: {value}")

    print("\nSample document:")
    print(df.iloc[0]["text"][:500])