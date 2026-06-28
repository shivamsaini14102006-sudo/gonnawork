from pathlib import Path
import json

# -------------------------------------------------------
# Project Paths
# -------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

JD_PATH = DATA_DIR / "job_description.md"
CANDIDATES_PATH = DATA_DIR / "candidates.jsonl"
SAMPLE_PATH = DATA_DIR / "sample_candidates.json"


# -------------------------------------------------------
# Load Job Description
# -------------------------------------------------------

def load_job_description():
    """
    Reads the complete Job Description markdown file.

    Returns:
        str
    """

    with open(JD_PATH, "r", encoding="utf-8") as file:
        return file.read()


# -------------------------------------------------------
# Stream Candidates
# -------------------------------------------------------

def stream_candidates():
    """
    Streams candidates one-by-one from candidates.jsonl.

    Yields:
        dict
    """

    with open(CANDIDATES_PATH, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            yield json.loads(line)


# -------------------------------------------------------
# Load Sample Candidates
# -------------------------------------------------------

def load_sample_candidates():
    """
    Loads sample_candidates.json

    Returns:
        list
    """

    with open(SAMPLE_PATH, "r", encoding="utf-8") as file:
        return json.load(file)
    
if __name__ == "__main__":
    jd = load_job_description()
    print(f"JD loaded: {len(jd)} characters")

    first_candidate = next(stream_candidates())
    print(f"First candidate ID: {first_candidate['candidate_id']}")