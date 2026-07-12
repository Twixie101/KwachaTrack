from flask import Blueprint, render_template, abort, request, redirect, url_for 
from app.models import db, Constituency, Project, CDFAllocation, ProjectStatus, CitizenFeedback, FinancialTransaction
from sqlalchemy import func
from datetime import datetime

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
@core_bp.route('/dashboard')
def national_dashboard():
    # Metric Aggregation across all constraints
    total_allocated = db.session.query(func.sum(CDFAllocation.allocated_amount)).scalar() or 0
    total_disbursed = db.session.query(func.sum(CDFAllocation.disbursed_amount)).scalar() or 0
    total_expended = db.session.query(func.sum(Project.expended_amount)).scalar() or 0
    remaining_balance = total_allocated - total_expended
    
    # Project Status Metric Splits
    total_projects = db.session.query(func.count(Project.id)).scalar() or 0
    completed_projects = db.session.query(func.count(Project.id)).filter(Project.status == ProjectStatus.COMPLETED).scalar() or 0
    abandoned_projects = db.session.query(func.count(Project.id)).filter(Project.status == ProjectStatus.ABANDONED).scalar() or 0
    in_progress_projects = db.session.query(func.count(Project.id)).filter(Project.status == ProjectStatus.IN_PROGRESS).scalar() or 0
    
    completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0

    return render_template(
        'dashboard.html',
        total_allocated=total_allocated,
        total_disbursed=total_disbursed,
        total_expended=total_expended,
        remaining_balance=remaining_balance,
        total_projects=total_projects,
        completed_projects=completed_projects,
        abandoned_projects=abandoned_projects,
        in_progress_projects=in_progress_projects,
        completion_rate=round(completion_rate, 1)
    )

@core_bp.route('/projects-directory')
def constituencies_list():
    # Fetch all projects to display in the directory
    all_projects = Project.query.order_by(Project.id.asc()).all()
    return render_template('constituencies.html', projects=all_projects)

@core_bp.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    # Fetch chronological asset tracking flow for "Follow the Money" feature
    timeline = sorted(project.financial_records, key=lambda x: x.transaction_date)
    return render_template('project_tracker.html', project=project, timeline=timeline)

@core_bp.route('/projects/track/<int:project_id>')
def track_project_detail(project_id):
    # 1. Fetch the single project by ID
    project = Project.query.get_or_404(project_id)
    
    # 2. Fetch the feedbacks for this specific project
    feedbacks = CitizenFeedback.query.filter_by(project_id=project_id).all()
    
    # 3. Calculate the variance
    budget_variance = project.budget - project.expended_amount

    transactions = FinancialTransaction.query.filter_by(project_id=project_id)\
    .order_by(FinancialTransaction.transaction_date.desc())\
    .limit(5).all()
# Pass this to render_template
    return render_template('project_tracker.html', project=project, feedbacks=feedbacks, budget_variance=budget_variance, transactions=transactions)
    

@core_bp.route('/admin')
def old_admin_trap():
    # If someone tries to go to /admin, send them to the homepage
    return redirect(url_for('core.national_dashboard'))

