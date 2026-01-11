"""
Dataset management for integrity auditor
"""
from datasets import load_dataset
import pandas as pd
from typing import Dict, List
import os


class DatasetManager:
    """Manages datasets for training"""
    
    def __init__(self):
        self.available_datasets = {
            'ai_vs_human': {
                'hc3': 'Hello-SimpleAI/HC3',
                'gpt2_output': 'imdb+gpt2',
                'mgtbench': 'MGTBench (Contact authors)'
            },
            'code_plagiarism': {
                'soco': 'SOCO - Source Code Corpus',
                'bigclonebench': 'BigCloneBench',
                'github_python': 'GitHub Python Repos'
            },
            'stylometry': {
                'pan_clef': 'PAN at CLEF',
                'blog_authorship': 'Blog Authorship Corpus'
            }
        }
    
    def load_hc3_dataset(self, sample_size=1000):
        """Load HC3 dataset for AI vs Human classification"""
        print(f"Loading HC3 dataset ({sample_size} samples)...")
        
        dataset = load_dataset(
            "Hello-SimpleAI/HC3", 
            "all", 
            split=f'train[:{sample_size}]', 
            trust_remote_code=True
        )
        
        texts = []
        labels = []
        
        for example in dataset:
            # Human answers
            if example['human_answers']:
                texts.append(example['human_answers'][0])
                labels.append(0)  # Human
            
            # AI answers
            if example['chatgpt_answers']:
                texts.append(example['chatgpt_answers'][0])
                labels.append(1)  # AI
        
        return texts, labels
    
    def load_pan_dataset(self):
        """Load PAN dataset for stylometry"""
        print("PAN dataset requires manual download from:")
        print("https://pan.webis.de/data.html")
        print("Please download and place in ./datasets/pan/")
        
        dataset_path = "./datasets/pan"
        if os.path.exists(dataset_path):
            # Load dataset logic here
            pass
        
        return [], []
    
    def get_dataset_info(self) -> Dict:
        """Get information about available datasets"""
        return self.available_datasets