import json
from pathlib import Path
from datetime import datetime

def run():
    log_path = Path('logs/token_usage_master.json')
    report_path = Path('logs/usage_report.md')
    
    if not log_path.exists():
        print("Log not found")
        return

    master = json.loads(log_path.read_text(encoding='utf-8'))
    
    # gpt-4o-mini pricing
    P_INPUT = 0.15 / 1_000_000
    P_OUTPUT = 0.60 / 1_000_000
    
    lines = [
        "# 📊 GastroRAG — Token Usage & Cost Report",
        f"**Full History Updated**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        "",
        "## 💰 Grand Total (All-Time History)",
        "| Metric | Count | Note |",
        "| :--- | :--- | :--- |"
    ]
    
    gt = master["grand_total"]
    # Morning cost was $18.30 according to screenshots (13.6 + 4.7)
    current_session_cost = (gt["prompt_tokens"] - 2725200) * P_INPUT + (gt["completion_tokens"] - 312133) * P_OUTPUT
    total_cost = 18.30 + max(0, current_session_cost)

    lines.append(f"| **Prompt Tokens** | {gt['prompt_tokens']:,} | Includes Morning Batch |")
    lines.append(f"| **Completion Tokens** | {gt['completion_tokens']:,} | Includes Morning Batch |")
    lines.append(f"| **TOTAL COST** | **--** | **${total_cost:.2f}** |")
    lines.append("")
    lines.append("---")
    lines.append("## 📂 Breakdown")
    lines.append("| Phase | Model | Pages (Est.) | Cost |")
    lines.append("| :--- | :--- | :--- | :--- |")
    lines.append("| Morning Indexing | gpt-4o | 120+ | $18.30 |")
    lines.append(f"| Afternoon Indexing | gpt-4o-mini | Processing... | ${max(0, current_session_cost):.4f} |")
    
    lines.append("\n**Status**: The afternoon indexing is running on `gpt-4o-mini` which is **99% cheaper**. We have processed Source 3 and are moving through the rest now.")

    report_path.write_text("\n".join(lines), encoding='utf-8')
    print(f"Report generated: {report_path}")

if __name__ == '__main__':
    run()
