#!/usr/bin/env python3
"""
ABCD Admin Prompts Update Script - Google Colab Version
Updated for PostgreSQL-based improved Document Analyzer

This script is designed to run in Google Colab and maintains backwards compatibility
with the legacy CSV-based workflow while working with the new API architecture.

Usage in Google Colab:
    1. Upload your CSV file
    2. Set API credentials
    3. Run all cells

Features:
    - Google Sheets integration for CSV management
    - Pandas-based data processing
    - Compatible with legacy prompt CSV structure
    - Status reporting and error handling
"""

import requests
import json
import pandas as pd
from typing import List, Dict, Any
import sys

# ============================================================================
# GOOGLE COLAB SETUP (uncomment if running in Colab)
# ============================================================================

# Uncomment these lines when running in Google Colab:
# from google.colab import auth, drive
# auth.authenticate_user()
# drive.mount('/content/drive')

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration for API connection"""
    # IMPORTANT: Update these values for your deployment
    API_BASE_URL = 'https://your-api-domain.com'  # Update this!
    API_KEY = 'abcd_chatbot_prod'                   # Update this!
    API_SECRET = 'your-api-secret-here'             # Update this!
    
    # CSV source
    # Option 1: Local file
    CSV_PATH = 'abcd_prompts_2025.csv'
    
    # Option 2: Google Drive (uncomment if using)
    # CSV_PATH = '/content/drive/MyDrive/ABCD/abcd_prompts_2025.csv'
    
    # Option 3: Google Sheets (provide sheet ID)
    GOOGLE_SHEET_ID = None  # e.g., '1a2b3c4d5e6f7g8h9i0j'
    
    # Update flags
    UPDATE_P1_P5_PROMPTS = True
    UPDATE_COMMENTS_PROMPTS = True
    UPDATE_PROPOSAL_PROMPTS = True
    UPDATE_TOR_PROMPTS = True
    UPDATE_EVALUATORS_PROMPTS = True
    UPDATE_CUSTOM_PROMPTS = True
    
    # Delete flags (use with caution!)
    ENABLE_DELETE_PROMPTS = False
    ENABLE_DELETE_CUSTOM = False


# ============================================================================
# DATA LOADING
# ============================================================================

def load_csv_from_sheets(sheet_id: str) -> pd.DataFrame:
    """Load CSV data from Google Sheets"""
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
    df = pd.read_csv(url)
    return df


def load_csv(config: Config) -> pd.DataFrame:
    """Load CSV from configured source"""
    print("📂 Loading CSV data...")
    
    if config.GOOGLE_SHEET_ID:
        print(f"   Source: Google Sheets (ID: {config.GOOGLE_SHEET_ID})")
        df = load_csv_from_sheets(config.GOOGLE_SHEET_ID)
    else:
        print(f"   Source: Local file ({config.CSV_PATH})")
        df = pd.read_csv(config.CSV_PATH)
    
    # Clean data
    df.fillna('', inplace=True)
    df = df.astype(str)
    
    print(f"✓ Loaded {len(df)} rows")
    print(f"  Columns: {', '.join(df.columns)}")
    print(f"  Partition labels: {', '.join(df['partition_label'].unique())}")
    
    return df


# ============================================================================
# API FUNCTIONS
# ============================================================================

class APIClient:
    """API client for prompt updates"""
    
    def __init__(self, config: Config):
        self.base_url = config.API_BASE_URL
        self.headers = {
            'accept': 'application/json',
            'api-key': config.API_KEY,
            'api-secret': config.API_SECRET,
            'Content-Type': 'application/json',
        }
    
    def update_prompts(self, partition_label: str, data_list: List[Dict]) -> bool:
        """Update analyzer prompts (P1-P5)"""
        url = f"{self.base_url}/update_prompts?prompt_label={partition_label}"
        
        try:
            response = requests.put(url, headers=self.headers, data=json.dumps(data_list), timeout=60)
            if response.status_code == 200:
                result = response.json()
                print(f"  ✓ {result.get('message', 'Success')}")
                return True
            else:
                print(f"  ✗ Failed. Status: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
            return False
    
    def update_analyzer_comments_summary_prompts(self, data_list: List[Dict]) -> bool:
        """Update analyzer comments summary prompts (P0)"""
        url = f"{self.base_url}/update_analyzer_comments_summary_prompts"
        
        try:
            response = requests.put(url, headers=self.headers, data=json.dumps(data_list), timeout=60)
            return response.status_code == 200
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
            return False
    
    def update_proposal_summary_prompts(self, data_list: List[Dict]) -> bool:
        """Update proposal summary prompts (P-IS)"""
        url = f"{self.base_url}/update_analyzer_proposal_summary_prompts"
        
        try:
            response = requests.put(url, headers=self.headers, data=json.dumps(data_list), timeout=60)
            return response.status_code == 200
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
            return False
    
    def update_tor_summary_prompts(self, data_list: List[Dict]) -> bool:
        """Update TOR summary prompts"""
        url = f"{self.base_url}/update_tor_summary_prompts"
        
        try:
            response = requests.put(url, headers=self.headers, data=json.dumps(data_list), timeout=60)
            return response.status_code == 200
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
            return False
    
    def update_evaluator_prompts(self, data_list: List[Dict]) -> bool:
        """Update evaluator prompts"""
        url = f"{self.base_url}/update_evaluator_prompts"
        
        try:
            response = requests.put(url, headers=self.headers, data=json.dumps(data_list), timeout=60)
            return response.status_code == 200
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
            return False
    
    def update_custom_prompts(self, data_list: List[Dict]) -> bool:
        """Update custom organization prompts"""
        url = f"{self.base_url}/update_custom_prompts"
        
        try:
            response = requests.put(url, headers=self.headers, data=json.dumps(data_list), timeout=60)
            return response.status_code == 200
        except Exception as e:
            print(f"  ✗ Request failed: {e}")
            return False
    
    def delete_analyzer_prompts(self, partition_label: str, doc_type: str) -> bool:
        """Delete analyzer prompts"""
        url = f"{self.base_url}/delete_prompts"
        params = {'prompt_label': partition_label, 'doc_type': doc_type}
        
        try:
            response = requests.delete(url, params=params, headers=self.headers, timeout=30)
            return response.status_code in [200, 404]
        except Exception as e:
            print(f"  ✗ Delete failed: {e}")
            return False
    
    def delete_custom_prompts(self, organization_id: str, doc_type: str) -> bool:
        """Delete custom organization prompts"""
        url = f"{self.base_url}/delete_custom_prompts"
        params = {'organization_id': organization_id, 'doc_type': doc_type}
        
        try:
            response = requests.delete(url, params=params, headers=self.headers, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"  ✗ Delete failed: {e}")
            return False


# ============================================================================
# PROMPT PROCESSING
# ============================================================================

class PromptProcessor:
    """Process and update prompts from CSV"""
    
    PARTITION_LABELS = [
        'P1', 'P1.F1', 'P1.F2', 'P1.F3',
        'P2', 'P2.F1', 'P2.F2', 'P2.F3',
        'P3', 'P3.F1', 'P3.F2', 'P3.F3',
        'P4', 'P4.F1', 'P4.F2', 'P4.F3',
        'P5', 'P5.F1', 'P5.F2', 'P5.F3'
    ]
    
    def __init__(self, df: pd.DataFrame, client: APIClient, config: Config):
        self.df = df
        self.client = client
        self.config = config
        self.stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def process_all(self):
        """Process all prompts from CSV"""
        print(f"\n{'='*70}")
        print(" Processing Prompts")
        print(f"{'='*70}\n")
        
        for partition_label, group in self.df.groupby('partition_label'):
            if partition_label in self.PARTITION_LABELS:
                self._process_p1_p5(partition_label, group)
            elif partition_label == "P0":
                self._process_comments(group)
            elif partition_label == "P-IS":
                self._process_proposal(group)
            elif partition_label == "TOR-SUMMARY":
                self._process_tor(group)
            elif partition_label in ["P_Internal", "P_Internal.F1", "P_Internal.F2", "P_External", "P_Delta"]:
                self._process_evaluators(partition_label, group)
            elif partition_label == "P_Custom":
                self._process_custom(group)
            else:
                print(f"⚠️  Unknown partition label: {partition_label}")
        
        return self.stats
    
    def _process_p1_p5(self, partition_label: str, group: pd.DataFrame):
        """Process P1-P5 analyzer prompts"""
        if not self.config.UPDATE_P1_P5_PROMPTS:
            print(f"⊘ Skipping {partition_label}")
            self.stats["skipped"] += len(group)
            return
        
        print(f"📝 Processing {partition_label}...")
        data_list = []
        
        for _, row in group.iterrows():
            if self.config.ENABLE_DELETE_PROMPTS and row['delete'] == "True":
                if self.client.delete_analyzer_prompts(partition_label, row['doc_type'].strip()):
                    self.stats["success"] += 1
                else:
                    self.stats["failed"] += 1
                continue
            
            data_list.append({
                "doc_type": row['doc_type'].strip(),
                "base_prompt": row['base_prompt'].strip(),
                "customization_prompt": row['customization_prompt'].strip(),
                "corpus_id": row['corpus_id'].strip(),
                "section_title": row['section_title'].strip(),
                "wisdom_1": row['wisdom_1'].strip(),
                "wisdom_2": row['wisdom_2'].strip(),
                "number_of_chunks": int(float(row['number_of_chunks'].strip())) if row['number_of_chunks'].strip() else None,
                "dependencies": row['dependencies'].strip(),
                "customize_prompt_based_on": row['customize_prompt_based_on'].strip(),
                "send_along_customised_prompt": row['send_along_customised_prompt'].strip(),
                "which_chunks": row['which_chunks'].strip(),
                "wisdom_received": row['wisdom_received'].strip(),
                "llm_flow": row['llm_flow'].strip(),
                "llm": row['llm'].strip(),
                "model": row['model'].strip(),
                "show_on_frontend": row['show_on_frontend'].strip(),
                "label_for_output": row['label_for_output'].strip(),
                "system_prompt": row.get('system_prompt', '').strip(),
                "temperature": float(row.get('temperature', 0.7)),
                "max_tokens": int(float(row.get('max_tokens', 4000)))
            })
        
        if data_list:
            if self.client.update_prompts(partition_label, data_list):
                self.stats["success"] += len(data_list)
            else:
                self.stats["failed"] += len(data_list)
            self.stats["processed"] += len(data_list)
    
    def _process_comments(self, group: pd.DataFrame):
        """Process P0 comments summary prompts"""
        if not self.config.UPDATE_COMMENTS_PROMPTS:
            print(f"⊘ Skipping P0 (comments)")
            self.stats["skipped"] += len(group)
            return
        
        print(f"📝 Processing P0 (Comments Summary)...")
        data_list = group.apply(lambda row: {
            "summary_prompt": row['base_prompt'].strip(),
            "doc_type": row['doc_type'].strip()
        }, axis=1).tolist()
        
        if self.client.update_analyzer_comments_summary_prompts(data_list):
            self.stats["success"] += len(data_list)
        else:
            self.stats["failed"] += len(data_list)
        self.stats["processed"] += len(data_list)
    
    def _process_proposal(self, group: pd.DataFrame):
        """Process P-IS proposal summary prompts"""
        if not self.config.UPDATE_PROPOSAL_PROMPTS:
            print(f"⊘ Skipping P-IS (proposal)")
            self.stats["skipped"] += len(group)
            return
        
        print(f"📝 Processing P-IS (Proposal Summary)...")
        data_list = group.apply(lambda row: {
            "proposal_prompt": row['base_prompt'].strip(),
            "doc_type": row['doc_type'].strip()
        }, axis=1).tolist()
        
        if self.client.update_proposal_summary_prompts(data_list):
            self.stats["success"] += len(data_list)
        else:
            self.stats["failed"] += len(data_list)
        self.stats["processed"] += len(data_list)
    
    def _process_tor(self, group: pd.DataFrame):
        """Process TOR summary prompts"""
        if not self.config.UPDATE_TOR_PROMPTS:
            print(f"⊘ Skipping TOR-SUMMARY")
            self.stats["skipped"] += len(group)
            return
        
        print(f"📝 Processing TOR-SUMMARY...")
        data_list = group.apply(lambda row: {
            "tor_summary_prompt": row['base_prompt'].strip(),
            "doc_type": row['doc_type'].strip(),
            "organization_id": row['organization_id'].strip()
        }, axis=1).tolist()
        
        if self.client.update_tor_summary_prompts(data_list):
            self.stats["success"] += len(data_list)
        else:
            self.stats["failed"] += len(data_list)
        self.stats["processed"] += len(data_list)
    
    def _process_evaluators(self, partition_label: str, group: pd.DataFrame):
        """Process evaluator prompts"""
        if not self.config.UPDATE_EVALUATORS_PROMPTS:
            print(f"⊘ Skipping {partition_label} (evaluator)")
            self.stats["skipped"] += len(group)
            return
        
        print(f"📝 Processing {partition_label} (Evaluator)...")
        data_list = group.apply(lambda row: {
            "prompt_label": partition_label,
            "doc_type": row['doc_type'].strip(),
            "base_prompt": row['base_prompt'].strip(),
            "customization_prompt": row['customization_prompt'].strip(),
            "wisdom_1": row['wisdom_1'].strip(),
            "wisdom_2": row['wisdom_2'].strip(),
            "organization_id": row['organization_id'].strip(),
            "org_guideline_id": row['org_guideline_id'].strip(),
            "section_title": row['section_title'].strip(),
            "number_of_chunks": int(float(row['number_of_chunks'].strip())) if row['number_of_chunks'].strip() else None,
            "additional_dependencies": row['dependencies'].strip(),
            "customize_prompt_based_on": row['customize_prompt_based_on'].strip(),
            "send_along_customised_prompt": row['send_along_customised_prompt'].strip(),
            "wisdom_received": row['wisdom_received'].strip(),
            "llm_flow": row['llm_flow'].strip(),
            "llm": row['llm'].strip(),
            "model": row['model'].strip(),
            "show_on_frontend": row['show_on_frontend'].strip(),
            "label_for_output": row['label_for_output'].strip(),
            "prompt_corpus": row['prompt_corpus'].strip()
        }, axis=1).tolist()
        
        if self.client.update_evaluator_prompts(data_list):
            self.stats["success"] += len(data_list)
        else:
            self.stats["failed"] += len(data_list)
        self.stats["processed"] += len(data_list)
    
    def _process_custom(self, group: pd.DataFrame):
        """Process custom organization prompts"""
        if not self.config.UPDATE_CUSTOM_PROMPTS:
            print(f"⊘ Skipping P_Custom")
            self.stats["skipped"] += len(group)
            return
        
        print(f"📝 Processing P_Custom (Organization-Specific)...")
        data_list = []
        
        for _, row in group.iterrows():
            if self.config.ENABLE_DELETE_CUSTOM and row['delete'] == "True":
                if self.client.delete_custom_prompts(row['organization_id'].strip(), row['doc_type'].strip()):
                    self.stats["success"] += 1
                else:
                    self.stats["failed"] += 1
                continue
            
            data_list.append({
                "doc_type": row['doc_type'].strip(),
                "corpus_id": row['corpus_id'].strip(),
                "base_prompt": row['base_prompt'].strip(),
                "customization_prompt": row['customization_prompt'].strip(),
                "organization_id": row['organization_id'].strip(),
                "number_of_chunks": int(float(row['number_of_chunks'].strip())) if row['number_of_chunks'].strip() else None
            })
        
        if data_list:
            if self.client.update_custom_prompts(data_list):
                self.stats["success"] += len(data_list)
            else:
                self.stats["failed"] += len(data_list)
            self.stats["processed"] += len(data_list)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    print(f"{'='*70}")
    print(" ABCD Document Analyzer - Prompts Update (Colab)")
    print(f"{'='*70}\n")
    
    # Load configuration
    config = Config()
    
    print("⚙️  Configuration:")
    print(f"  API URL: {config.API_BASE_URL}")
    print(f"  CSV Source: {'Google Sheets' if config.GOOGLE_SHEET_ID else 'Local File'}")
    print(f"  Updates Enabled:")
    print(f"    P1-P5 Analyzer: {config.UPDATE_P1_P5_PROMPTS}")
    print(f"    Comments (P0): {config.UPDATE_COMMENTS_PROMPTS}")
    print(f"    Proposal (P-IS): {config.UPDATE_PROPOSAL_PROMPTS}")
    print(f"    TOR Summary: {config.UPDATE_TOR_PROMPTS}")
    print(f"    Evaluators: {config.UPDATE_EVALUATORS_PROMPTS}")
    print(f"    Custom (P_Custom): {config.UPDATE_CUSTOM_PROMPTS}")
    print()
    
    # Load CSV
    try:
        df = load_csv(config)
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        return 1
    
    # Initialize API client
    client = APIClient(config)
    
    # Process prompts
    processor = PromptProcessor(df, client, config)
    stats = processor.process_all()
    
    # Print summary
    print(f"\n{'='*70}")
    print(" SUMMARY")
    print(f"{'='*70}")
    print(f"Processed: {stats['processed']}")
    print(f"Success: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"{'='*70}\n")
    
    if stats['failed'] > 0:
        print("⚠️  Some operations failed. Check logs above for details.")
        return 1
    else:
        print("✅ All operations completed successfully!")
        return 0


# ============================================================================
# COLAB EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run main function
    exit_code = main()
    
    # In Colab, we don't exit, just print the result
    if exit_code == 0:
        print("\n🎉 Update completed successfully!")
    else:
        print("\n❌ Update completed with errors. See details above.")
