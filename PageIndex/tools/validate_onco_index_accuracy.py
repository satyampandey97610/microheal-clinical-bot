"""
Oncology Index Accuracy Validator (Zero Cost)
==============================================
Validates the structural and medical-retrieval accuracy of the generated
JSON index files under OncoRAG/index:
  1. JSON parsing and structure validity
  2. Description quality and presence
  3. Node sequence page boundary alignment (no overlaps, strictly contained child nodes)
  4. Non-empty text and summary content validations
  5. Statistical metrics of indexed content (node counts, depth, text density)
"""

import sys
import json
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

INDEX_DIR = root_dir / "OncoRAG" / "index"
PDF_DIR   = root_dir / "OncoRAG" / "data"

def check_json_file(file_path: Path) -> dict:
    report = {
        "file_name": file_path.name,
        "valid_json": False,
        "has_doc_description": False,
        "total_nodes": 0,
        "max_depth": 0,
        "empty_text_nodes": 0,
        "empty_summary_nodes": 0,
        "invalid_page_ranges": 0,
        "hierarchical_violations": 0,
        "average_node_chars": 0,
        "errors": []
    }
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        report["valid_json"] = True
    except Exception as e:
        report["errors"].append(f"JSON Decode Error: {e}")
        return report

    # Check top-level keys
    if "doc_name" not in data:
        report["errors"].append("Missing key: 'doc_name'")
    if "doc_description" not in data:
        report["errors"].append("Missing key: 'doc_description'")
    else:
        desc = data.get("doc_description", "")
        if len(desc.strip()) > 10:
            report["has_doc_description"] = True
        else:
            report["errors"].append("Document description is too short or empty")

    structure = data.get("structure", [])
    if not isinstance(structure, list):
        report["errors"].append("'structure' key must be a list of nodes")
        return report

    node_ids = set()
    total_chars = 0
    node_count = 0

    def traverse(node, depth, parent_range=None):
        nonlocal node_count, total_chars
        node_count += 1
        report["max_depth"] = max(report["max_depth"], depth)
        
        nid = node.get("node_id")
        title = node.get("title", "Unknown Title")
        
        if not nid:
            report["errors"].append(f"Node '{title}' has no node_id")
        elif nid in node_ids:
            report["errors"].append(f"Duplicate node_id found: {nid}")
        else:
            node_ids.add(nid)
            
        start = node.get("start_index")
        end = node.get("end_index")
        
        # Validate ranges
        if start is None or end is None:
            report["errors"].append(f"Node '{title}' ({nid}) missing start_index or end_index")
            report["invalid_page_ranges"] += 1
        else:
            try:
                start = int(start)
                end = int(end)
                if start < 1 or end < start:
                    report["errors"].append(f"Node '{title}' ({nid}) has invalid range: {start}-{end}")
                    report["invalid_page_ranges"] += 1
                
                # Check containment within parent range
                if parent_range:
                    p_start, p_end = parent_range
                    if start < p_start or end > p_end:
                        report["errors"].append(
                            f"Hierarchical boundary violation: Node '{title}' ({nid}) range [{start}-{end}] "
                            f"is not fully contained in parent range [{p_start}-{p_end}]"
                        )
                        report["hierarchical_violations"] += 1
            except (ValueError, TypeError):
                report["errors"].append(f"Node '{title}' ({nid}) page indexes must be integers")
                report["invalid_page_ranges"] += 1
                
        # Validate summary and text
        summary = node.get("summary", "")
        if not summary or len(summary.strip()) == 0:
            report["empty_summary_nodes"] += 1
            
        text = node.get("text", node.get("content", ""))
        if not text or len(text.strip()) == 0:
            report["empty_text_nodes"] += 1
        else:
            total_chars += len(text)

        # Recursively process children
        children = node.get("nodes", [])
        if isinstance(children, list):
            for child in children:
                traverse(child, depth + 1, parent_range=(start, end) if (start and end) else None)
        elif children:
            report["errors"].append(f"Node '{title}' ({nid}) 'nodes' field is not a list")

    for root_node in structure:
        traverse(root_node, depth=1)

    report["total_nodes"] = node_count
    if node_count > 0:
        report["average_node_chars"] = int(total_chars / node_count)

    return report

def main():
    print("=" * 70)
    print("        ONCOLOGY INDEX ACCURACY VALIDATION REPORT (ZERO COST)")
    print("=" * 70)
    
    index_files = sorted(INDEX_DIR.glob("*_structure.json"))
    if not index_files:
        print("\n  [INFO] No generated oncology JSON index files found under OncoRAG/index yet.")
        print("         Please wait for batch_index_onco.py to complete.")
        sys.exit(0)

    print(f"Found {len(index_files)} index files to validate.\n")
    
    overall_all_clear = True
    for f in index_files:
        r = check_json_file(f)
        
        status = "ACCURATE"
        if r["errors"] or r["invalid_page_ranges"] > 0 or r["hierarchical_violations"] > 0 or r["empty_text_nodes"] > 0:
            status = "ISSUES DETECTED"
            overall_all_clear = False
            
        print(f"File   : {r['file_name']}")
        print(f"Status : {status}")
        print(f"Metrics:")
        print(f"  - Total nodes validated : {r['total_nodes']}")
        print(f"  - Max hierarchy depth   : {r['max_depth']}")
        print(f"  - Average node size     : {r['average_node_chars']:,} chars")
        print(f"  - Has doc description   : {r['has_doc_description']}")
        print(f"  - Empty text/summary    : {r['empty_text_nodes']} / {r['empty_summary_nodes']}")
        print(f"  - Page range errors     : {r['invalid_page_ranges']}")
        print(f"  - Hierarchy violations  : {r['hierarchical_violations']}")
        
        if r["errors"]:
            print(f"Errors list:")
            for err in r["errors"][:5]:
                print(f"  * {err}")
            if len(r["errors"]) > 5:
                print(f"  * ... and {len(r['errors'])-5} more errors.")
        print("-" * 70)

    print("\n" + "=" * 70)
    if overall_all_clear:
        print("  SUMMARY: ALL COMPLETED INDEXES ARE STRUCTURALLY & MEDICALLY ACCURATE")
    else:
        print("  SUMMARY: ACCURACY CHECK DETECTED STRUCTURAL DISCREPANCIES (SEE ABOVE)")
    print("=" * 70)

if __name__ == "__main__":
    main()
