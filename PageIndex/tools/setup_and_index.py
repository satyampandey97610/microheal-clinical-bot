#!/usr/bin/env python3
"""
GastroRAG Setup and Indexing Script
Run this script to set up your OpenAI API key and index all PDFs
"""

import os
import subprocess
import sys
from pathlib import Path

def check_api_key():
    """Check if OpenAI API key is configured"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        return False
    return True

def update_env_file():
    """Update .env file with user's API key"""
    env_file = Path(".env")
    print("\n" + "="*60)
    print("🔑 OPENAI API KEY SETUP")
    print("="*60)
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if "your-openai-api-key-here" in content:
                print("Please enter your OpenAI API key:")
                api_key = input("OpenAI API Key (sk-...): ").strip()
                if api_key.startswith("sk-"):
                    new_content = content.replace("your-openai-api-key-here", api_key)
                    with open(env_file, 'w') as f:
                        f.write(new_content)
                    print("✅ API key saved to .env file")
                    return True
                else:
                    print("❌ Invalid API key format")
                    return False
            else:
                print("✅ API key already configured")
                return True
    else:
        print("❌ .env file not found")
        return False

def run_indexing():
    """Run indexing for all PDFs"""
    pdfs = [
        ("digestive_datasets_cran.pdf", "5 pages", "~1 minute"),
        ("PageIndex_Optimized_GI_Report.pdf", "9 pages", "~1 minute"),
        ("EMJ-Gastroenterology-10_1-2021-4.pdf", "103 pages", "~3-5 minutes"),
        ("Yamadas-Handbook-of-Gastroenterology-2019.pdf", "536 pages", "~15-20 minutes"),
        ("I-546_Gastro.pdf", "826 pages", "~25-35 minutes")
    ]
    
    print("\n" + "="*60)
    print("📚 INDEXING PDF FILES")
    print("="*60)
    print("This will take approximately 45-60 minutes total.")
    print("Estimated cost: $1-2 (one-time)\n")
    
    confirm = input("Do you want to proceed with indexing? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Indexing cancelled.")
        return False
    
    for pdf_name, pages, duration in pdfs:
        print(f"\n📄 Indexing {pdf_name} ({pages}) - {duration}")
        print("-" * 50)
        
        cmd = [
            sys.executable, "run_pageindex.py",
            "--pdf_path", f"pdfs/{pdf_name}",
            "--if-add-node-summary", "yes"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                print(f"✅ {pdf_name} indexed successfully")
                
                # Check if JSON file was created
                json_name = pdf_name.replace(".pdf", "_structure.json")
                if Path(f"results/{json_name}").exists():
                    print(f"✅ {json_name} created")
                else:
                    print(f"⚠️  {json_name} not found")
            else:
                print(f"❌ Error indexing {pdf_name}")
                print("Error:", result.stderr)
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout indexing {pdf_name}")
            return False
        except Exception as e:
            print(f"❌ Exception indexing {pdf_name}: {e}")
            return False
    
    return True

def verify_indexing():
    """Verify that all PDFs were indexed"""
    print("\n" + "="*60)
    print("🔍 VERIFYING INDEXING")
    print("="*60)
    
    expected_files = [
        "digestive_datasets_cran_structure.json",
        "PageIndex_Optimized_GI_Report_structure.json", 
        "EMJ-Gastroenterology-10_1-2021-4_structure.json",
        "Yamadas-Handbook-of-Gastroenterology-2019_structure.json",
        "I-546_Gastro_structure.json"
    ]
    
    results_dir = Path("results")
    if not results_dir.exists():
        print("❌ results/ directory not found")
        return False
    
    success_count = 0
    for json_file in expected_files:
        file_path = results_dir / json_file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {json_file} ({size:,} bytes)")
            success_count += 1
        else:
            print(f"❌ {json_file} missing")
    
    print(f"\n📊 Summary: {success_count}/{len(expected_files)} files indexed successfully")
    
    if success_count == len(expected_files):
        print("\n🎉 All PDFs indexed successfully!")
        print("You can now run: streamlit run app.py")
        return True
    else:
        print("\n⚠️  Some PDFs failed to index. Check the errors above.")
        return False

def main():
    """Main setup function"""
    print("🏥 GastroRAG Setup and Indexing Script")
    print("="*60)
    
    # Step 1: Check API key
    if not check_api_key():
        if not update_env_file():
            print("❌ Setup cancelled - API key required")
            return
    
    # Step 2: Run indexing
    if run_indexing():
        # Step 3: Verify indexing
        if verify_indexing():
            print("\n🚀 Setup complete! You can now run the Streamlit app:")
            print("   streamlit run app.py")
        else:
            print("\n⚠️  Setup completed with errors. Check the output above.")
    else:
        print("\n❌ Indexing was cancelled or failed.")

if __name__ == "__main__":
    main()
