from typing import Any, Dict, List, Set, TypedDict

# ==================================================
# Configuration Constants
# ==================================================

# Overall Weights
PROFILE_WEIGHT: float = 0.70
BEHAVIOR_WEIGHT: float = 0.30

# Profile Weights
SKILL_WEIGHT: float = 0.40
EXPERIENCE_WEIGHT: float = 0.40
TITLE_WEIGHT: float = 0.20

# Behavior Weights
OPEN_TO_WORK_WEIGHT: float = 0.40
RESPONSE_RATE_WEIGHT: float = 0.40
NOTICE_PERIOD_WEIGHT: float = 0.20

# ==================================================
# Type Definitions
# ==================================================

class SkillDict(TypedDict, total=False):
    """Type definition for a single skill record."""
    name: str
    proficiency: str
    endorsements: int
    duration_months: int

class CandidateFeatures(TypedDict):
    """Type definition for the extracted flat features used in scoring."""
    candidate_id: str
    experience_years: float
    current_title: str
    headline: str
    summary: str
    skills: List[SkillDict]
    open_to_work: bool
    response_rate: float
    notice_period: float


# ==================================================
# Feature Extraction
# ==================================================

def extract_features(candidate: Dict[str, Any]) -> CandidateFeatures:
    """Extract ONLY candidate features using the actual nested structure.
    
    Args:
        candidate: The raw candidate dictionary loaded from JSON/JSONL.
        
    Returns:
        A CandidateFeatures dictionary containing parsed and typed values.
    """
    profile: Dict[str, Any] = candidate.get("profile") or {}
    redrob: Dict[str, Any] = candidate.get("redrob_signals") or {}
    
    def safe_float(val: Any, default: float = 0.0) -> float:
        try:
            return float(val) if val is not None else default
        except (ValueError, TypeError):
            return default

    # Defensively extract features exactly mapped to the provided schema
    return {
        "candidate_id": str(candidate.get("candidate_id", "")),
        "experience_years": safe_float(profile.get("years_of_experience")),
        "current_title": str(profile.get("current_title") or ""),
        "headline": str(profile.get("headline") or ""),
        "summary": str(profile.get("summary") or ""),
        "skills": candidate.get("skills") or [],
        "open_to_work": bool(redrob.get("open_to_work_flag", False)),
        "response_rate": safe_float(redrob.get("recruiter_response_rate")),
        "notice_period": safe_float(redrob.get("notice_period_days")),
    }


# ==================================================
# Profile Scoring
# ==================================================

def skill_score(features: CandidateFeatures, jd_keywords: Set[str]) -> float:
    """Calculate the skill score based on keyword overlap and skill metadata.
    
    Args:
        features: Extracted candidate features.
        jd_keywords: Pre-computed lowercase target keywords from job description.
        
    Returns:
        A float between 0.0 and 1.0 representing the skill match score.
    """
    if not jd_keywords:
        return 0.0
        
    skills: List[SkillDict] = features["skills"]
    if not skills:
        return 0.0
        
    total_score: float = 0.0
    matched_count: int = 0
    max_possible_per_skill: float = 2.0 
    
    for skill in skills:
        if not isinstance(skill, dict):
            continue
            
        name: str = str(skill.get("name", ""))
        if not name:
            continue
            
        lower_name: str = name.strip().lower()
        if lower_name in jd_keywords:
            matched_count += 1
            
            # Base match score
            match_score: float = 1.0
            
            # 1. Bonus for proficiency
            prof: str = str(skill.get("proficiency", "")).lower()
            if prof in ("expert", "advanced"):
                match_score += 0.5
            elif prof == "intermediate":
                match_score += 0.25
                
            # 2. Bonus for endorsements
            try:
                endorsements: int = int(skill.get("endorsements", 0))
            except (ValueError, TypeError):
                endorsements = 0
                
            if endorsements >= 20:
                match_score += 0.25
            elif endorsements >= 5:
                match_score += 0.1
                
            # 3. Bonus for duration
            try:
                duration: int = int(skill.get("duration_months", 0))
            except (ValueError, TypeError):
                duration = 0
                
            if duration >= 60:
                match_score += 0.25
            elif duration >= 24:
                match_score += 0.1
                
            total_score += match_score
            
    if matched_count == 0:
        return 0.0
        
    coverage: float = min(1.0, matched_count / len(jd_keywords))
    quality: float = total_score / (matched_count * max_possible_per_skill)
    
    score: float = (coverage * 0.7) + (quality * 0.3)
    return max(0.0, min(1.0, score))


def experience_score(features: CandidateFeatures) -> float:
    """Calculate the experience score based on brackets from specification."""
    years: float = features["experience_years"]
        
    if years < 2.0:
        return 0.20
    elif years < 5.0:
        return 0.60
    elif years < 10.0:
        return 1.00
    elif years <= 15.0:
        return 0.80
    else:
        return 0.60


def title_score(features: CandidateFeatures, jd_keywords: Set[str]) -> float:
    """Calculate the title match score based on keyword overlap."""
    if not jd_keywords:
        return 0.0
        
    title: str = features["current_title"].strip().lower()
    if not title:
        return 0.0
        
    matched: int = sum(1 for kw in jd_keywords if kw in title)
    
    score: float = matched / len(jd_keywords)
    return max(0.0, min(1.0, score))


def profile_score(skill: float, experience: float, title: float) -> float:
    """Calculate the combined profile score from precomputed components.
    
    Avoids duplicate internal computations by accepting the already computed
    component scores instead of re-reading features.
    
    Args:
        skill: Pre-calculated skill score.
        experience: Pre-calculated experience score.
        title: Pre-calculated title score.
        
    Returns:
        A float between 0.0 and 1.0.
    """
    score: float = (skill * SKILL_WEIGHT) + (experience * EXPERIENCE_WEIGHT) + (title * TITLE_WEIGHT)
    return max(0.0, min(1.0, score))


# ==================================================
# Behavior Scoring
# ==================================================

def open_to_work_score(features: CandidateFeatures) -> float:
    """Calculate the open to work score."""
    return 1.0 if features["open_to_work"] else 0.0


def recruiter_response_score(features: CandidateFeatures) -> float:
    """Calculate the recruiter response score."""
    rate: float = features["response_rate"]
    return max(0.0, min(1.0, rate))


def notice_period_score(features: CandidateFeatures) -> float:
    """Calculate the notice period score with linear normalization."""
    days: float = features["notice_period"]
    clamped_days: float = max(0.0, min(180.0, days))
    score: float = 1.0 - (clamped_days / 180.0)
    
    return max(0.0, min(1.0, score))


def behavior_score(otw: float, response: float, notice: float) -> float:
    """Calculate the combined behavior score from precomputed components.
    
    Avoids duplicate internal computations by accepting the already computed
    component scores.
    """
    score: float = (otw * OPEN_TO_WORK_WEIGHT) + (response * RESPONSE_RATE_WEIGHT) + (notice * NOTICE_PERIOD_WEIGHT)
    return max(0.0, min(1.0, score))


# ==================================================
# Reason Generation
# ==================================================

def generate_reason(features: CandidateFeatures, jd_keywords: Set[str]) -> str:
    """Generate a brief, factual reason string detailing candidate strengths.
    
    Args:
        features: Extracted candidate features.
        jd_keywords: Pre-lowercased target keywords from job description.
        
    Returns:
        A deterministic short string summarizing the candidate's core profile.
    """
    parts: List[str] = []
    
    skills: List[SkillDict] = features["skills"]
    matched_skills: List[tuple[int, str]] = []
    
    for skill in skills:
        if not isinstance(skill, dict):
            continue
            
        name: str = str(skill.get("name", "")).strip()
        if not name:
            continue
            
        lower_name: str = name.lower()
        if lower_name in jd_keywords:
            prof: str = str(skill.get("proficiency", "")).lower()
            prof_bonus = 2 if prof in ("expert", "advanced") else (1 if prof == "intermediate" else 0)
            
            try:
                end_bonus = int(skill.get("endorsements", 0))
            except (ValueError, TypeError):
                end_bonus = 0
                
            try:
                dur_bonus = int(skill.get("duration_months", 0))    
            except (ValueError, TypeError):
                dur_bonus = 0
                
            score = (prof_bonus * 1000) + (end_bonus * 10) + dur_bonus
            matched_skills.append((score, name))
            
    # Sort strongest matches first and take up to 3
    matched_skills.sort(key=lambda x: x[0], reverse=True)
    top_skill_names: List[str] = [name for _, name in matched_skills[:3]]
    
    if top_skill_names:
        if len(top_skill_names) == 1:
            joined = top_skill_names[0]
        elif len(top_skill_names) == 2:
            joined = f"{top_skill_names[0]} and {top_skill_names[1]}"
        else:
            joined = f"{', '.join(top_skill_names[:-1])}, and {top_skill_names[-1]}"
        parts.append(f"Strong {joined} skills")
    else:
        # Fallback if no specific JD matches
        if skills and isinstance(skills, list) and isinstance(skills[0], dict):
            fallback_name = str(skills[0].get("name", "")).strip()
            if fallback_name:
                parts.append(f"Strong {fallback_name} skills")
            else:
                parts.append("Relevant skills")
        else:
            parts.append("Relevant skills")
            
    # Append experience length
    exp_raw: float = features["experience_years"]
    if exp_raw > 0:
        exp_display = int(exp_raw) if exp_raw.is_integer() else exp_raw
        parts.append(f"{exp_display} years experience")
            
    # Append Open to Work behavior
    if features["open_to_work"]:
        parts.append("Open to Work")
        
    return ", ".join(parts) + "."


# ==================================================
# Public Interface
# ==================================================

def score_candidate(candidate: Dict[str, Any], jd_keywords: List[str]) -> Dict[str, Any]:
    """Score a single candidate against job description keywords.
    
    Provides deterministic float boundaries natively enforcing 0.0 to 1.0 scales
    for each sub-score. Avoids duplicated internal logic.
    
    Args:
        candidate: The raw candidate dictionary.
        jd_keywords: List of target keywords from the job description.
        
    Returns:
        A dictionary containing the candidate_id, detailed scores block,
        and a generated reason, with floats explicitly rounded to 4 spaces.
    """
    # 1. Pre-process JD keywords ONCE. Saves thousands of iterations converting/setting lists.
    jd_set: Set[str] = {k.strip().lower() for k in jd_keywords if k.strip()} if jd_keywords else set()
    
    # 2. Extract strictly relevant features internally, cleanly decoupled from JD inputs.
    features: CandidateFeatures = extract_features(candidate)
    
    # 3. Compute individual profile and behavior components
    s_score: float = skill_score(features, jd_set)
    e_score: float = experience_score(features)
    t_score: float = title_score(features, jd_set)
    
    # Avoid recomputing logic natively inside profile score logic
    p_score: float = profile_score(s_score, e_score, t_score)
    
    otw_score: float = open_to_work_score(features)
    rr_score: float = recruiter_response_score(features)
    np_score: float = notice_period_score(features)
    
    # Avoid recomputing logic natively inside behavior score logic
    b_score: float = behavior_score(otw_score, rr_score, np_score)
    
    # 4. Compute final weighted score
    final_score: float = (p_score * PROFILE_WEIGHT) + (b_score * BEHAVIOR_WEIGHT)
    final_score = max(0.0, min(1.0, final_score))
    
    # 5. Generate deterministic factual reason
    reason: str = generate_reason(features, jd_set)
    
    # 6. Return structured result strictly rounded to 4 dec
    return {
        "candidate_id": features["candidate_id"],
        "scores": {
            "skill": round(s_score, 4),
            "experience": round(e_score, 4),
            "title": round(t_score, 4),
            "profile": round(p_score, 4),
            "behavior": round(b_score, 4),
            "final": round(final_score, 4)
        },
        "reason": reason
    }
