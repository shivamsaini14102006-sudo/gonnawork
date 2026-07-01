"""Production RANKING logic leveraging stream processing."""

import csv
import heapq
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, List

from scripts import loader
from scripts import scorer

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

def rank_candidates(
    candidates: Iterable[dict],
    jd_text: str,
    top_k: int = 100,
) -> list[dict]:
    if top_k <= 0:
      return []
    jd_keywords = _extract_jd_keywords(jd_text)
    
    best_k: List[HeapItem] = []
    
    for candidate in candidates:
        res = scorer.score_candidate(candidate, jd_keywords)
        
        final_score = res["scores"]["final"]
        cid = res["candidate_id"]
        
        item = HeapItem(score=final_score, candidate_id=cid, data=res)
        
        if len(best_k) < top_k:
            heapq.heappush(best_k, item)
        else:
            heapq.heappushpop(best_k, item)
            
    best_k.sort(
        key=lambda item: (
            -item.score,
            item.candidate_id
        )
    )
    
    ranked_candidates = []
    for rank, item in enumerate(best_k, start=1):
        ranked_candidates.append({
            "candidate_id": item.candidate_id,
            "rank": rank,
            "score": item.score,
            "reasoning": item.data["reason"]
        })
        
    return ranked_candidates

def _write_csv_to_file_obj(ranked_candidates: list[dict], file_obj: Any) -> None:
    writer = csv.DictWriter(
        file_obj, 
        fieldnames=["candidate_id", "rank", "score", "reasoning"]
    )
    writer.writeheader()
    writer.writerows(ranked_candidates)

def write_submission_csv(
    ranked_candidates: list[dict],
    output_path: Path,
) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        _write_csv_to_file_obj(ranked_candidates, f)

def generate_submission_csv_bytes(
    ranked_candidates: list[dict],
) -> bytes:
    output = io.StringIO(newline="")
    _write_csv_to_file_obj(ranked_candidates, output)
    return output.getvalue().encode("utf-8")

def main() -> None:
    """Main execution block: streams candidates, scores them, targets top 100."""
    # 1. Load the fully detailed Job Description using native loader module
    jd_text: str = loader.load_job_description()
    
    # 2. Process candidate evaluations
    ranked_candidates = rank_candidates(
        candidates=loader.stream_candidates(),
        jd_text=jd_text,
        top_k=100
    )
    
    # Standardize output locations via loader's native root
    output_dir: Path = loader.PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save meticulously mapped submission file
    csv_path: Path = output_dir / "submission.csv"
    write_submission_csv(ranked_candidates, csv_path)

if __name__ == "__main__":
    main()
