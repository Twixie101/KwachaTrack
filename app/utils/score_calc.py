# app/utils/score_calc.py

import datetime
from sqlalchemy import func
from app.models import db, Project, ProjectStatus, CitizenFeedback, VerificationStatus

def calculate_constituency_transparency_score(constituency_id):
    """
    Algorithmic Transparency Score Engine (TSE) for KwachaTrack.
    Generates a dynamic 0-100 rating optimizing public accountability metrics.
    
    Formula:
    TSE = (0.40 * Completion_Rate) + (0.40 * Financial_Discipline) + Responsiveness_Bonus - Penalties
    """
    # 1. Fetch project profile vectors for target constituency
    projects = Project.query.filter_by(constituency_id=constituency_id).all()
    
    # If a constituency has no assigned projects yet, return a neutral base benchmark
    if not projects:
        return 70.0

    total_projects = len(projects)
    completed_count = 0
    abandoned_count = 0
    in_progress_count = 0
    
    total_budget_allocated = 0
    total_expended_actual = 0
    overspent_penalty_points = 0

    for p in projects:
        total_budget_allocated += float(p.budget)
        total_expended_actual += float(p.expended_amount)
        
        if p.status == ProjectStatus.COMPLETED:
            completed_count += 1
        elif p.status == ProjectStatus.ABANDONED:
            abandoned_count += 1
        elif p.status == ProjectStatus.IN_PROGRESS:
            in_progress_count += 1
            
        # Metric: Individual Project Cost Discipline Variance
        # Slashing points if actual expended tracking overflows original approved project thresholds
        if p.expended_amount > p.budget:
            variance_ratio = (float(p.expended_amount) - float(p.budget)) / float(p.budget)
            # Deduct scaling penalty up to a max of 15 points per overspent project
            overspent_penalty_points += min(15, variance_ratio * 50)

    # --- METRIC 1: PROJECT COMPLETION RATE (WEIGHT: 40%) ---
    # Formula components: Completed accounts for full value, In-progress gains partial value
    completion_rate = ((completed_count + (in_progress_count * 0.5)) / total_projects) * 100
    metric_completion_score = completion_rate * 0.40

    # --- METRIC 2: FINANCIAL DISCIPLINE & VARIANCE INDEX (WEIGHT: 40%) ---
    # Evaluates aggregate overruns and subtracts individual project variance penalties
    if total_budget_allocated > 0:
        aggregate_overflow_ratio = total_expended_actual / total_budget_allocated
        # If aggregate spending exceeds 120% of total allocated budget, inflict baseline cost penalties
        if aggregate_overflow_ratio > 1.20:
            overspent_penalty_points += 20
            
    financial_discipline_base = max(0, 100 - overspent_penalty_points)
    metric_financial_score = financial_discipline_base * 0.40

    # --- METRIC 3: CIVIC ENGAGEMENT & RESPONSIVENESS BONUS (WEIGHT: 20%) ---
    # Measures the verification velocity of the local government regarding citizen complaints
    total_feedback = db.session.query(func.count(CitizenFeedback.id))\
        .join(Project)\
        .filter(Project.constituency_id == constituency_id).scalar() or 0
        
    verified_feedback = db.session.query(func.count(CitizenFeedback.id))\
        .join(Project)\
        .filter(Project.constituency_id == constituency_id, 
                CitizenFeedback.verification_status == VerificationStatus.VERIFIED).scalar() or 0

    # High percentage of addressed/verified public feedback flags high communication transparency
    if total_feedback > 0:
        responsiveness_ratio = verified_feedback / total_feedback
        metric_civic_score = (responsiveness_ratio * 100) * 0.20
    else:
        # Neutral compliance fallback if no citizens have flagged incidents yet
        metric_civic_score = 15.0 

    # --- SYSTEM PENALTIES ---
    # Critical Structural Failure Penalty: Immediate heavy penalty for active abandoned infrastructure sites
    abandoned_site_penalty = abandoned_count * 12.5

    # --- AGGREGATION & NORMALIZATION MATRIX ---
    raw_tse_score = metric_completion_score + metric_financial_score + metric_civic_score
    final_score = raw_tse_score - abandoned_site_penalty

    # Hard-clip boundary guardrail values between strict mathematical limits [0, 100]
    normalized_score = max(0.0, min(100.0, final_score))
    
    return round(normalized_score, 1)