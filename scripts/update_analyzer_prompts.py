#!/usr/bin/env python3
"""
ABCD Admin Prompts Update Script
Updated for PostgreSQL-based improved Document Analyzer

This script maintains backwards compatibility with the legacy Colab workflow
while working with the new API architecture.

Usage:
    python scripts/update_analyzer_prompts.py --csv abcd_prompts_2025.csv

Environment Variables:
    API_BASE_URL: Base URL for API (default: http://localhost:8001)
    API_KEY: API key for authentication
    API_SECRET: API secret for authentication
"""

import requests
import json
import pandas as pd
import argparse
import os
import sys
from typing import List, Dict, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Configuration (can be overridden by environment variables)
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
API_KEY = os.getenv('API_KEY', 'abcd_chatbot_prod')
API_SECRET = os.getenv('API_SECRET', 'e87a50be-4c74-4bfc-80b0-bbcca3e2a1bd')

# Headers for requests
HEADERS = {
    'accept': 'application/json',
    'api-key': API_KEY,
    'api-secret': API_SECRET,
    'Content-Type': 'application/json',
}

# Partition labels
PARTITION_LABELS = [
    'P1', 'P1.F1', 'P1.F2', 'P1.F3',
    'P2', 'P2.F1', 'P2.F2', 'P2.F3',
    'P3', 'P3.F1', 'P3.F2', 'P3.F3',
    'P4', 'P4.F1', 'P4.F2', 'P4.F3',
    'P5', 'P5.F1', 'P5.F2', 'P5.F3'
]

# Document types
DOC_TYPES = [
    "Program design Document",
    "Investment or grant proposal",
    "Strategy recommendations",
    "School or college course outline",
    "MEL approach",
    "Research draft or proposal",
    "Media article or draft",
    "Policy Document",
    "Product or service design"
]

# ============================================================================
# API FUNCTIONS
# ============================================================================

def update_prompts(partition_label: str, data_list: List[Dict]) -> bool:
    """Update analyzer prompts (P1-P5)"""
    url = f"{API_BASE_URL}/update_prompts?prompt_label={partition_label}"
    
    try:
        response = requests.put(url, headers=HEADERS, data=json.dumps(data_list), timeout=60)
        if response.status_code == 200:
            print(f"✓ Updated prompts for {partition_label}")
            return True
        else:
            print(f"✗ Failed for {partition_label}. Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed for {partition_label}: {e}")
        return False


def update_analyzer_comments_summary_prompts(data_list: List[Dict]) -> bool:
    """Update analyzer comments summary prompts (P0)"""
    url = f"{API_BASE_URL}/update_analyzer_comments_summary_prompts"
    
    try:
        response = requests.put(url, headers=HEADERS, data=json.dumps(data_list), timeout=60)
        if response.status_code == 200:
            print("✓ Updated analyzer comments summary prompts")
            return True
        else:
            print(f"✗ Failed to update comments prompts. Status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False


def update_proposal_summary_prompts(data_list: List[Dict]) -> bool:
    """Update proposal summary prompts (P-IS)"""
    url = f"{API_BASE_URL}/update_analyzer_proposal_summary_prompts"
    
    try:
        response = requests.put(url, headers=HEADERS, data=json.dumps(data_list), timeout=60)
        if response.status_code == 200:
            print("✓ Updated proposal summary prompts")
            return True
        else:
            print(f"✗ Failed to update proposal prompts. Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False


def update_tor_summary_prompts(data_list: List[Dict]) -> bool:
    """Update TOR summary prompts"""
    url = f"{API_BASE_URL}/update_tor_summary_prompts"
    
    try:
        response = requests.put(url, headers=HEADERS, data=json.dumps(data_list), timeout=60)
        if response.status_code == 200:
            print("✓ Updated TOR summary prompts")
            return True
        else:
            print(f"✗ Failed to update TOR prompts. Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False


def update_evaluator_prompts(data_list: List[Dict]) -> bool:
    """Update evaluator prompts"""
    url = f"{API_BASE_URL}/update_evaluator_prompts"
    
    try:
        response = requests.put(url, headers=HEADERS, data=json.dumps(data_list), timeout=60)
        if response.status_code == 200:
            print("✓ Updated evaluator prompts")
            return True
        else:
            print(f"✗ Failed to update evaluator prompts. Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False


def update_custom_prompts(data_list: List[Dict]) -> bool:
    """Update custom organization prompts"""
    url = f"{API_BASE_URL}/update_custom_prompts"
    
    try:
        response = requests.put(url, headers=HEADERS, data=json.dumps(data_list), timeout=60)
        if response.status_code == 200:
            print("✓ Updated custom prompts")
            return True
        else:
            print(f"✗ Failed to update custom prompts. Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Request failed: {e}")
        return False


def delete_analyzer_prompts(partition_label: str, doc_type: str) -> bool:
    """Delete analyzer prompts"""
    url = f"{API_BASE_URL}/delete_prompts"
    params = {'prompt_label': partition_label, 'doc_type': doc_type}
    
    try:
        response = requests.delete(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            print(f"✓ Deleted prompts for {partition_label}/{doc_type}")
            return True
        elif response.status_code == 404:
            print(f"ℹ No prompts found for {partition_label}/{doc_type}")
            return True
        else:
            print(f"✗ Failed to delete. Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Delete request failed: {e}")
        return False


def delete_custom_prompts(organization_id: str, doc_type: str) -> bool:
    """Delete custom organization prompts"""
    url = f"{API_BASE_URL}/delete_custom_prompts"
    params = {'organization_id': organization_id, 'doc_type': doc_type}
    
    try:
        response = requests.delete(url, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            print(f"✓ Deleted custom prompts for {organization_id}/{doc_type}")
            return True
        else:
            print(f"✗ Failed to delete custom prompts. Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Delete request failed: {e}")
        return False


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_csv(csv_path: str, update_flags: Dict[str, bool], delete_flags: Dict[str, bool]) -> Dict[str, int]:
    """
    Process CSV file and update prompts
    
    Args:
        csv_path: Path to CSV file
        update_flags: Dict of which prompt types to update
        delete_flags: Dict of which prompt types to delete
        
    Returns:
        Dict with statistics
    """
    print(f"\n{'='*70}")
    print(f" ABCD Prompts Update - {csv_path}")
    print(f"{'='*70}\n")
    
    # Load CSV
    print(f"📂 Loading CSV file: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
        df.fillna('', inplace=True)
        df = df.astype(str)
        print(f"✓ Loaded {len(df)} rows\n")
    except Exception as e:
        print(f"✗ Failed to load CSV: {e}")
        return {"error": 1}
    
    # Statistics
    stats = {
        "processed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Process by partition label
    for partition_label, group in df.groupby('partition_label'):
        
        # ====== P1-P5 Analyzer Prompts ======
        if partition_label in PARTITION_LABELS:
            if not update_flags.get('p1_p5_prompts', False):
                print(f"⊘ Skipping {partition_label} (disabled)")
                stats["skipped"] += len(group)
                continue
            
            print(f"\n📝 Processing {partition_label}...")
            data_list = []
            
            for _, row in group.iterrows():
                # Check delete flag
                if delete_flags.get('delete_prompts', False) and row['delete'] == "True":
                    doc_type = row['doc_type'].strip()
                    print(f"  🗑️  Deleting {partition_label}/{doc_type}")
                    if delete_analyzer_prompts(partition_label, doc_type):
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                    continue
                
                # Build data item
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
                    "label_for_output": row['label_for_output'].strip()
                })
            
            if data_list:
                if update_prompts(partition_label, data_list):
                    stats["success"] += len(data_list)
                else:
                    stats["failed"] += len(data_list)
                stats["processed"] += len(data_list)
        
        # ====== P0 Comments Summary ======
        elif partition_label == "P0":
            if not update_flags.get('comments_prompts', False):
                print(f"⊘ Skipping P0 comments (disabled)")
                stats["skipped"] += len(group)
                continue
            
            print(f"\n📝 Processing P0 (Comments Summary)...")
            data_list = group.apply(lambda row: {
                "summary_prompt": row['base_prompt'].strip(),
                "doc_type": row['doc_type'].strip()
            }, axis=1).tolist()
            
            if update_analyzer_comments_summary_prompts(data_list):
                stats["success"] += len(data_list)
            else:
                stats["failed"] += len(data_list)
            stats["processed"] += len(data_list)
        
        # ====== P-IS Proposal Summary ======
        elif partition_label == "P-IS":
            if not update_flags.get('proposal_prompts', False):
                print(f"⊘ Skipping P-IS proposal (disabled)")
                stats["skipped"] += len(group)
                continue
            
            print(f"\n📝 Processing P-IS (Proposal Summary)...")
            data_list = group.apply(lambda row: {
                "proposal_prompt": row['base_prompt'].strip(),
                "doc_type": row['doc_type'].strip()
            }, axis=1).tolist()
            
            if update_proposal_summary_prompts(data_list):
                stats["success"] += len(data_list)
            else:
                stats["failed"] += len(data_list)
            stats["processed"] += len(data_list)
        
        # ====== TOR Summary ======
        elif partition_label == "TOR-SUMMARY":
            if not update_flags.get('tor_prompts', False):
                print(f"⊘ Skipping TOR summary (disabled)")
                stats["skipped"] += len(group)
                continue
            
            print(f"\n📝 Processing TOR-SUMMARY...")
            data_list = group.apply(lambda row: {
                "tor_summary_prompt": row['base_prompt'].strip(),
                "doc_type": row['doc_type'].strip(),
                "organization_id": row['organization_id'].strip()
            }, axis=1).tolist()
            
            if update_tor_summary_prompts(data_list):
                stats["success"] += len(data_list)
            else:
                stats["failed"] += len(data_list)
            stats["processed"] += len(data_list)
        
        # ====== Evaluator Prompts ======
        elif partition_label in ["P_Internal", "P_Internal.F1", "P_Internal.F2", "P_External", "P_Delta"]:
            if not update_flags.get('evaluators_prompts', False):
                print(f"⊘ Skipping {partition_label} evaluator (disabled)")
                stats["skipped"] += len(group)
                continue
            
            print(f"\n📝 Processing {partition_label} (Evaluator)...")
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
            
            if update_evaluator_prompts(data_list):
                stats["success"] += len(data_list)
            else:
                stats["failed"] += len(data_list)
            stats["processed"] += len(data_list)
        
        # ====== Custom Prompts ======
        elif partition_label == "P_Custom":
            if not update_flags.get('p_custom_prompts', False):
                print(f"⊘ Skipping P_Custom (disabled)")
                stats["skipped"] += len(group)
                continue
            
            print(f"\n📝 Processing P_Custom (Organization-Specific)...")
            data_list = []
            
            for _, row in group.iterrows():
                # Check delete flag
                if delete_flags.get('delete_custom_prompts', False) and row['delete'] == "True":
                    org_id = row['organization_id'].strip()
                    doc_type = row['doc_type'].strip()
                    print(f"  🗑️  Deleting custom prompt for {org_id}/{doc_type}")
                    if delete_custom_prompts(org_id, doc_type):
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
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
                if update_custom_prompts(data_list):
                    stats["success"] += len(data_list)
                else:
                    stats["failed"] += len(data_list)
                stats["processed"] += len(data_list)
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Update ABCD Document Analyzer prompts from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Update all prompts
    python scripts/update_analyzer_prompts.py --csv abcd_prompts_2025.csv --all
    
    # Update only analyzer prompts (P1-P5)
    python scripts/update_analyzer_prompts.py --csv abcd_prompts_2025.csv --p1-p5
    
    # Update evaluators only
    python scripts/update_analyzer_prompts.py --csv abcd_prompts_2025.csv --evaluators
    
    # Enable deletions
    python scripts/update_analyzer_prompts.py --csv abcd_prompts_2025.csv --all --delete-prompts

Environment Variables:
    API_BASE_URL: API base URL (default: http://localhost:8001)
    API_KEY: API key for authentication
    API_SECRET: API secret for authentication
        """
    )
    
    parser.add_argument('--csv', required=True, help='Path to CSV file with prompts')
    parser.add_argument('--api-url', help='Override API base URL')
    
    # Enable specific prompt types
    parser.add_argument('--all', action='store_true', help='Update all prompt types')
    parser.add_argument('--p1-p5', action='store_true', help='Update P1-P5 analyzer prompts')
    parser.add_argument('--proposal', action='store_true', help='Update proposal summary prompts')
    parser.add_argument('--tor', action='store_true', help='Update TOR summary prompts')
    parser.add_argument('--comments', action='store_true', help='Update comments summary prompts')
    parser.add_argument('--evaluators', action='store_true', help='Update evaluator prompts')
    parser.add_argument('--custom', action='store_true', help='Update custom org prompts')
    
    # Delete flags
    parser.add_argument('--delete-prompts', action='store_true', help='Enable deletion of prompts marked with delete=True')
    parser.add_argument('--delete-custom', action='store_true', help='Enable deletion of custom prompts marked with delete=True')
    
    args = parser.parse_args()
    
    # Override API URL if provided
    if args.api_url:
        global API_BASE_URL
        API_BASE_URL = args.api_url
    
    # Build update flags
    update_flags = {
        'p1_p5_prompts': args.all or args.p1_p5,
        'proposal_prompts': args.all or args.proposal,
        'tor_prompts': args.all or args.tor,
        'comments_prompts': args.all or args.comments,
        'evaluators_prompts': args.all or args.evaluators,
        'p_custom_prompts': args.all or args.custom
    }
    
    delete_flags = {
        'delete_prompts': args.delete_prompts,
        'delete_custom_prompts': args.delete_custom
    }
    
    # Check if any update flag is set
    if not any(update_flags.values()):
        print("⚠️  No prompt types selected. Use --all or specific flags like --p1-p5")
        parser.print_help()
        return 1
    
    # Show configuration
    print(f"API Base URL: {API_BASE_URL}")
    print(f"CSV File: {args.csv}")
    print(f"\nPrompt Types to Update:")
    for key, value in update_flags.items():
        print(f"  {key}: {'✓ Enabled' if value else '⊗ Disabled'}")
    
    # Process CSV
    stats = process_csv(args.csv, update_flags, delete_flags)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f" SUMMARY")
    print(f"{'='*70}")
    if "error" in stats:
        print("❌ Failed to process CSV")
        return 1
    
    print(f"Processed: {stats['processed']}")
    print(f"Success: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"{'='*70}\n")
    
    return 0 if stats['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
