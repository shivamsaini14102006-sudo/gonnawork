"""Production RANKING logic leveraging stream processing."""

import csv
import heapq
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, FrozenSet

import loader
import scorer

@dataclass
class HeapItem:
    """Wrapper to properly maintain min-heap ordering with custom tiebreakers."""
    score: float
    candidate_id: str
    data: Dict[str, Any] = field(compare=False)
    
    def __lt__(self, other: "HeapItem") -> bool:
        # Min-heap puts the "worst" items at the front to be popped.
        if self.score != other.score:
            return self.score < other.score
        # For ties, smaller candidate_id is better. So the LARGER candidate_id is WORSE.
        return self.candidate_id > other.candidate_id

def _extract_jd_keywords(jd_text: str) -> FrozenSet[str]:
    """Parse and normalize keywords from the job description markdown once."""
    # Find all alphanumeric words, lowercase them, and generate a frozenset for rapid lookup
    words: List[str] = re.findall(r'\b[a-z0-9_]+\b', jd_text.lower())
    return frozenset(words)

def main() -> None:
    """Main execution block: streams candidates, scores them, targets top 100."""
    # 1. Load the fully detailed Job Description using native loader module
    jd_text: str = loader.load_job_description()
    
    # 2. Preprocess JD ONCE into frozenset optimization
    jd_keywords: FrozenSet[str] = _extract_jd_keywords(jd_text)
    
    # 3. Process candidate evaluations efficiently maintaining purely the definitive best 100
    best_100: List[HeapItem] = []
    
    # Stream gracefully bypassing monolithic JSON loads
    for candidate in loader.stream_candidates():
        # 4. Score each candidate
        # Feed parameters utilizing optimized subsets downstream
        res: Dict[str, Any] = scorer.score_candidate(candidate, jd_keywords)
        
        final_score: float = res["scores"]["final"]
        cid: str = res["candidate_id"]
        
        item = HeapItem(score=final_score, candidate_id=cid, data=res)
        
        # 5. Shield memory by restricting heap accumulation exactly at ceiling capacity bounds
        if len(best_100) < 100:
            heapq.heappush(best_100, item)
        else:
            heapq.heappushpop(best_100, item)
            
    # 6. Struct heap array strictly holds the top subsets natively mapped out of order.
    # We sort descendingly so that the highest scoring (absolute 'best') are initialized first.
    best_100.sort(
        key=lambda item: (
            -item.score,
            item.candidate_id
        )
    )
    
    # Standardize output locations via loader's native root
    output_dir: Path = loader.PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save meticulously mapped submission file
    csv_path: Path = output_dir / "submission.csv"
    
    # 11. Write utilizing CSV dict handler to ensure strict adherence
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, 
            fieldnames=["candidate_id", "rank", "score", "reasoning"]
        )
        writer.writeheader()
        
        # 8. Assign sequential 1+ rank endpoints during write output
        for rank, item in enumerate(best_100, start=1):
            # 9. Extract correct reason parameter structure mapped via internal dictionary returns
            writer.writerow({
                "candidate_id": item.candidate_id,
                "rank": rank,
                "score": item.score,
                "reasoning": item.data["reason"]
            })

if __name__ == "__main__":
    main()
