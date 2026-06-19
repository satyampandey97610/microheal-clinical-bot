import argparse
import os
import json
import asyncio
import litellm
from pathlib import Path
from dotenv import load_dotenv
from pageindex import *
from pageindex.page_index_md import md_to_tree
from pageindex.utils import ConfigLoader

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

def main():
    parser = argparse.ArgumentParser(description='GastroRAG Indexing Utility')
    parser.add_argument('--pdf_path', type=str, help='Path to the PDF file')
    parser.add_argument('--md_path', type=str, help='Path to the Markdown file')
    parser.add_argument('--model', type=str, default='gpt-4o-mini', help='LLM model for indexing')
    parser.add_argument('--if-add-node-id', type=str, default='yes')
    parser.add_argument('--if-add-node-summary', type=str, default='yes')
    parser.add_argument('--if-add-doc-description', type=str, default='yes')
    parser.add_argument('--if-add-node-text', type=str, default='yes')
    
    args = parser.parse_args()
    
    if not args.pdf_path and not args.md_path:
        print("Error: Specify --pdf_path or --md_path")
        return

    options = {
        'model': args.model,
        'if_add_node_id': args.if_add_node_id,
        'if_add_node_summary': args.if_add_node_summary,
        'if_add_doc_description': args.if_add_doc_description,
        'if_add_node_text': args.if_add_node_text,
    }
    opt = ConfigLoader().load(options)
    
    output_dir = Path('./results')
    output_dir.mkdir(exist_ok=True)

    if args.pdf_path:
        if not os.path.exists(args.pdf_path):
            print(f"Error: File not found {args.pdf_path}")
            return
            
        print(f"Indexing PDF: {args.pdf_path}...")
        result = page_index_main(args.pdf_path, opt)
        pdf_name = Path(args.pdf_path).stem
        output_file = output_dir / f"{pdf_name}_structure.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Tree structure saved to: {output_file}")
            
    elif args.md_path:
        print(f"Indexing Markdown: {args.md_path}...")
        result = asyncio.run(md_to_tree(
            md_path=args.md_path,
            if_add_node_summary=opt.if_add_node_summary == 'yes',
            model=opt.model,
            if_add_doc_description=opt.if_add_doc_description == 'yes',
            if_add_node_text=opt.if_add_node_text == 'yes',
            if_add_node_id=opt.if_add_node_id == 'yes'
        ))
        md_name = Path(args.md_path).stem
        output_file = output_dir / f"{md_name}_structure.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Tree structure saved to: {output_file}")

    # ==========================================
    # FINAL COST & TOKEN REPORT
    # ==========================================
    from pageindex.utils import GLOBAL_USAGE
    
    prompt_tokens = GLOBAL_USAGE["prompt_tokens"]
    completion_tokens = GLOBAL_USAGE["completion_tokens"]
    total_tokens = GLOBAL_USAGE["total_tokens"]
    api_calls = GLOBAL_USAGE["api_calls"]
    
    # Cost calculation for gpt-4o-mini
    # $0.150 per 1M input tokens
    # $0.600 per 1M output tokens
    cost_prompt = (prompt_tokens / 1_000_000) * 0.150
    cost_completion = (completion_tokens / 1_000_000) * 0.600
    total_cost = cost_prompt + cost_completion
    
    print("\n" + "="*50)
    print("📈 FINAL TOKEN & COST REPORT")
    print("="*50)
    print(f"Total API Calls:     {api_calls}")
    print(f"Prompt Tokens:       {prompt_tokens:,} (${cost_prompt:.6f})")
    print(f"Completion Tokens:   {completion_tokens:,} (${cost_completion:.6f})")
    print(f"Total Tokens:        {total_tokens:,}")
    print(f"Total Exact Cost:    ${total_cost:.6f} USD")
    print("="*50)
    print("NOTE: Every single API call was permanently logged to logs/token_usage_raw.jsonl")

if __name__ == "__main__":
    main()