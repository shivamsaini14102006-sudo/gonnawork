"""
Streamlit application for the Redrob AI Candidate Ranking System.
This acts as a production sandbox to demonstrate the ranking system.
"""

import json
import time
from typing import Any, Dict, List

import streamlit as st

from scripts import loader
from scripts import rank


def main() -> None:
    st.set_page_config(page_title="Redrob AI Candidate Ranking System", page_icon="🔥")

    st.markdown(
        "<h1 style='text-align: center;'>🤖 Redrob AI Candidate Ranking System</h1>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "<h3 style='text-align: center;'>Production Sandbox</h3>", 
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: gray;'>The benchmark Job Description is loaded internally.<br>Upload a candidate dataset and generate the official submission.csv.</p>", 
        unsafe_allow_html=True
    )
    
    st.divider()

    st.subheader("Candidate Dataset")
    
    uploaded_file = st.file_uploader(
        "Upload Candidate Dataset (.jsonl)", 
        type=["jsonl"],
        help="Supports datasets up to approximately 1000 candidates."
    )

    if uploaded_file is not None:
        if st.button("🚀 Run Ranking", type="primary"):
            
            candidates: List[Dict[str, Any]] = []
            
            try:
                for line in uploaded_file:
                    line_str = line.decode("utf-8").strip()
                    if line_str:
                        candidates.append(json.loads(line_str))
                        
                if not candidates:
                    raise ValueError("Empty file")
                
                with st.spinner("Evaluating candidates... Generating ranking... Preparing submission..."):
                    start_time = time.perf_counter()
                    
                    jd_text: str = loader.load_job_description()
                    ranked: List[Dict[str, Any]] = rank.rank_candidates(
                        candidates,
                        jd_text,
                        top_k=100
                    )
                    
                    csv_bytes: bytes = rank.generate_submission_csv_bytes(ranked)
                    
                    runtime = time.perf_counter() - start_time
                    
                st.success("✅ Ranking Completed Successfully")
                
                st.divider()

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Candidates Uploaded", len(candidates))
                with col2:
                    st.metric("Candidates Ranked", len(ranked))
                with col3:
                    st.metric("Submission Rows", len(ranked))
                with col4:
                    st.metric("Runtime", f"{runtime:.2f} sec")

                st.divider()
                
                st.subheader("Submission Preview")
                preview = []

                for row in ranked[:10]:
                 preview.append({
                               "candidate_id": row["candidate_id"],
        "rank": row["rank"],
        "score": f"{row['score']:.4f}",
        "reasoning": row["reasoning"],
    })

                st.dataframe(
    preview,
    use_container_width=True,
    hide_index=True,
)
                st.divider()
                
                st.download_button(
                    label="📥 Download submission.csv",
                    data=csv_bytes,
                    file_name="submission.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )
                
            except json.JSONDecodeError:
                st.error("Error: Invalid JSON or JSONL format. Please check your uploaded file.")
            except ValueError as ve:
                if str(ve) == "Empty file":
                    st.error("Error: The uploaded file is empty.")
                else:
                    st.error("Error: Invalid JSON or JSONL data.")
            except Exception:
                st.error("An unexpected error occurred during processing. Please verify your dataset structure.")


if __name__ == "__main__":
    main()
