# TOPkACE

## AI-Powered Candidate Ranking System
### Redrob Data & AI Challenge Submission

---

# Overview

TOPkACE is a deterministic, CPU-only candidate ranking system developed for the Redrob Data & AI Challenge.

The system ranks candidates against a benchmark Job Description using a modular scoring pipeline that combines profile relevance and recruiter-oriented behavioral signals. It is designed to be lightweight, reproducible, and suitable for execution within the challenge's compute constraints.

Given a Job Description and a candidate dataset, the system generates an official `submission.csv` containing the highest-ranked candidates together with an explainable reasoning field.

The repository also includes a Streamlit sandbox that allows judges to upload a sample candidate dataset, execute the ranking pipeline, preview the generated submission, and download the resulting CSV.

---

# Key Features

- Deterministic ranking pipeline
- CPU-only execution
- No external API or network calls during ranking
- Streaming candidate processing
- Heap-based Top-K ranking
- Explainable candidate reasoning
- Validator-compatible CSV generation
- Interactive Streamlit sandbox

---

# Repository Structure

```text
gonnawork/

├── app.py
├── README.md
├── requirements.txt
├── submission_metadata.yaml
├── validate_submission.py
│
├── data/
│   ├── job_description.md
│   ├── candidates.jsonl
│   ├── sample_candidates.json
│
├── scripts/
│   ├── loader.py
│   ├── scorer.py
│   ├── rank.py
│   └── __init__.py
│
├── outputs/
│   └── submission.csv
│
├── artifacts/
│   ├── jd_profile_schema.md
│   └── candidate_schema.json
```

---

# System Architecture

```
                Job Description
                        │
                        ▼
              Keyword Extraction
                        │
                        ▼
               Candidate Loader
                        │
                        ▼
              Feature Extraction
                        │
                        ▼
               Candidate Scoring
                        │
                        ▼
               Top-K Heap Ranking
                        │
                        ▼
                submission.csv
```

---

# Ranking Pipeline

## 1. Job Description Loading

The benchmark Job Description is loaded from:

```
data/job_description.md
```

using the loader module.

---

## 2. Job Description Processing

The ranking pipeline preprocesses the Job Description into a normalized keyword set by extracting lowercase alphanumeric tokens. These keywords are reused throughout candidate evaluation to avoid repeated parsing.

---

## 3. Candidate Loading

Candidates are streamed from the JSONL dataset, enabling memory-efficient processing without loading the full dataset into memory.

---

## 4. Feature Extraction

Each candidate is transformed into a normalized feature representation containing:

- Candidate identifier
- Experience
- Current title
- Headline
- Summary
- Skills
- Open-to-work status
- Recruiter response rate
- Notice period

---

## 5. Candidate Scoring

Each candidate receives multiple component scores including:

- Skill relevance
- Experience
- Title alignment
- Profile score
- Behavioral score

These components are combined into a final normalized ranking score.

---

## 6. Top-K Ranking

Instead of storing every candidate in memory, the system maintains only the highest-ranked candidates using a bounded min-heap.

This provides:

- Memory complexity: **O(K)**
- Ranking complexity: **O(N log K)**

---

## 7. CSV Generation

The final ranked candidates are exported as

```
outputs/submission.csv
```

with the required columns:

- candidate_id
- rank
- score
- reasoning

---

# Project Components

## loader.py

Responsible for:

- loading the benchmark Job Description
- streaming candidate datasets
- loading sample datasets

---

## scorer.py

Responsible for:

- feature extraction
- profile scoring
- behavioral scoring
- reason generation
- final score aggregation

---

## rank.py

Responsible for:

- preprocessing the Job Description
- invoking candidate scoring
- maintaining the Top-K heap
- generating submission.csv

---

## app.py

Provides the Streamlit sandbox used for demonstration and evaluation.

Features:

- upload candidate dataset
- execute ranking
- preview submission
- download submission.csv

---

# Installation

```bash
git clone https://github.com/shivamsaini14102006-sudo/gonnawork.git

pip install -r requirements.txt
```

---

# Generate submission.csv

Run:

```bash
python -m scripts.rank
```

Generated output:

```
outputs/submission.csv
```

---

# Validate Submission

```bash
python validate_submission.py outputs/submission.csv
```

---

## Live Sandbox

A hosted demonstration of the ranking system is available at:

**🔗 Sandbox:** https://qwertpassd.streamlit.app/

The sandbox uses the same ranking pipeline as the CLI implementation.

### Sandbox Workflow

1. Upload a candidate dataset (`.jsonl`)
2. The benchmark Job Description is loaded internally
3. Click **Run Ranking**
4. Preview the generated `submission.csv`
5. Download the final submission file



# Streamlit localhost 

Launch:

```bash
python -m streamlit run app.py
```

Workflow:

1. Upload a candidate JSONL file.
2. Click **Run Ranking**.
3. Preview the top-ranked candidates.
4. Download the generated `submission.csv`.

---

# Performance

Execution Mode:

- CPU only

Python Version:

- Python 3.11

Network:

- Disabled during ranking

GPU:

- Not required

Memory:

- Top-K heap limits memory usage.

---

# Design Principles

The ranking engine was designed around the following engineering principles:

- Deterministic execution
- Modular architecture
- Explainable ranking
- Memory efficiency
- Reproducibility
- Separation of concerns

---

# Future Improvements

Potential future extensions include:

- Structured Job Description profiles
- Semantic responsibility matching
- Advanced candidate feature engineering
- Enhanced explainability

---

# Dependencies

- Python 3.11+
- Streamlit 1.57.0

Install all dependencies with:


---

# License

This repository was developed as a submission for the Redrob Data & AI Challenge.