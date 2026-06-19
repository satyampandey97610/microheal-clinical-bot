
import json
import re
from pathlib import Path

def normalize_text(text):
    text = text.lower()
    text = text.replace(".", " ").replace("-", " ").replace("'", "").replace("\u2019", "")
    return re.sub(r"\s+", " ", text)

def get_candidates(query, tree_nodes, top_k=15):
    q_norm = normalize_text(query)
    keywords = [w for w in q_norm.split() if len(w) > 2]
    
    print(f"Query: {query}")
    print(f"Normalized Query: {q_norm}")
    print(f"Keywords: {keywords}")
    
    candidates = []
    def traverse(nodes):
        for n in nodes:
            score = 0
            t_norm = normalize_text(n.get("title", ""))
            s_norm = normalize_text(n.get("summary", ""))
            
            # Direct phrase match
            if q_norm in t_norm or q_norm in s_norm:
                score += 20
            
            # Keyword match
            for kw in keywords:
                if kw in t_norm: score += 5
                if kw in s_norm: score += 2
            
            if score > 0:
                candidates.append({"node": n, "score": score})
            
            if "nodes" in n:
                traverse(n["nodes"])
    
    traverse(tree_nodes)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:top_k]

# Load I-546
json_path = r"c:\Satyam_Onedrive\OneDrive\Desktop\New folder\gastroRAG\PageIndex\results\I-546_Gastro_structure.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

query = "What is GLP-1?"
candidates = get_candidates(query, data.get("structure", []))

print(f"Found {len(candidates)} candidates.")
for i, c in enumerate(candidates[:5]):
    print(f"Candidate {i}: Score {c['score']} | Title: {c['node'].get('title')} | Summary snippet: {c['node'].get('summary')[:100]}...")
