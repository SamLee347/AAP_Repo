#!/usr/bin/env python3
"""
Script to fix Git merge conflicts in Jupyter notebook
"""

import json
import re

def clean_notebook_conflicts(input_file, output_file):
    """Remove Git merge conflict markers from notebook"""
    
    print(f"Reading {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Removing merge conflict markers...")
    
    # Remove Git merge conflict markers
    patterns_to_remove = [
        r'<<<<<<< HEAD\n',
        r'=======\n', 
        r'>>>>>>> Chatbot\n',
        r'<<<<<<< HEAD',
        r'=======',
        r'>>>>>>> Chatbot'
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content)
    
    # Try to parse as JSON to validate
    try:
        notebook_data = json.loads(content)
        print("✓ Valid JSON after cleanup")
        
        # Save the cleaned version
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(notebook_data, f, indent=1)
        
        print(f"✓ Cleaned notebook saved to {output_file}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"✗ Still invalid JSON: {e}")
        
        # If still invalid, try to save the raw cleaned content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Raw cleaned content saved to {output_file}")
        return False

if __name__ == "__main__":
    input_file = "jason_dept name model.ipynb"
    output_file = "jason_dept name model_fixed.ipynb"
    
    success = clean_notebook_conflicts(input_file, output_file)
    
    if success:
        print("\n🎉 Notebook successfully cleaned and is now valid!")
        print(f"Original: {input_file}")
        print(f"Fixed: {output_file}")
        print("\nYou can now:")
        print("1. Replace the original with the fixed version")
        print("2. Open the fixed notebook in VS Code")
    else:
        print("\n⚠️  Manual intervention may be needed")
        print("The conflicts were removed but JSON structure may need additional fixes")
