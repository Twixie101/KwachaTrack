from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from app.models import db, Project, CitizenFeedback, UploadedEvidence, UserRole, ProjectStatus, FinancialTransaction
from datetime import datetime
from app.utils.ai_client import analyze_expenditure_anomalies
import io
import csv
import os

citizen_bp = Blueprint('citizen', __name__)

@citizen_bp.route('/projects/track/<int:project_id>', methods=['GET', 'POST'])
def track_project_detail(project_id):
    from app.models import Project, CitizenFeedback
    
    project = Project.query.get_or_404(project_id)
    feedbacks = CitizenFeedback.query.filter_by(project_id=project_id).order_by(CitizenFeedback.created_at.desc()).all()
    
    # 1. FIXED: Leverage your built-in relationship backref name
    timeline = project.financial_records
    
    # Calculate variance metrics
    budget_variance = project.budget - project.expended_amount
    variance_percentage = (project.expended_amount / project.budget) * 100 if project.budget > 0 else 0
    
    return render_template(
        'project_tracker.html',
        project=project,
        feedbacks=feedbacks,
        timeline=timeline,  # Successfully passes your transaction array to the UI table!
        budget_variance=budget_variance,
        variance_percentage=round(variance_percentage, 1)
    )

@citizen_bp.route('/projects/audit/<int:project_id>', methods=['GET', 'POST'])
def run_ai_audit(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Prepare details payload for the Gemini SDK wrapper
    details_context = f"Contractor: {project.contractor_name}. Current Progress reported at {project.progress_percentage}%."
    
    # Trigger Gemini Analysis
    ai_analysis_result = analyze_expenditure_anomalies(
        project_title=project.title,
        budget=project.budget,
        expended=project.expended_amount,
        contractor=project.contractor_name,
        details=details_context
    )
    
    return render_template('ai_audit_result.html', project=project, audit_text=ai_analysis_result)


@citizen_bp.route('/projects/report/<int:project_id>', methods=['GET', 'POST'])
def submit_report(project_id):
    from app.models import db, CitizenFeedback, UploadedEvidence
    
    if request.method == 'POST':
        # 1. Save feedback
        # Use conditional expression for user_id to support anonymous users
        new_feedback = CitizenFeedback(
            project_id=project_id,
            user_id=current_user.id if current_user.is_authenticated else None,
            feedback_type="Complaint",
            comment=request.form.get('description'),
            verification_status='PENDING',
            upvote_count=0
        )
        db.session.add(new_feedback)
        db.session.flush() # Get new_feedback.id for evidence linking

        # 2. Handle file upload
        file = request.files.get('evidence')
        if file and file.filename != '':
            filename = secure_filename(f"{new_feedback.id}_{file.filename}")
            
            # Ensure the directory exists
            upload_dir = os.path.join('app', 'static', 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            file.save(os.path.join(upload_dir, filename))
            
            # 3. Save evidence record
            evidence = UploadedEvidence(
                file_secure_url=filename,
                feedback_id=new_feedback.id
            )
            db.session.add(evidence)
        
        db.session.commit()
        flash("Incident report submitted successfully.", "success")
        return redirect(url_for('core.track_project_detail', project_id=project_id))
        
    return render_template('submit_report.html', project_id=project_id)

from app.models import CitizenFeedback, Project # Ensure both are imported

@citizen_bp.route('/reports/dashboard')
def reports_dashboard():
    # 1. Keep your existing stats
    total_reports = CitizenFeedback.query.count()
    verified_count = CitizenFeedback.query.filter_by(verification_status='VERIFIED').count()
    
    # 2. Add the query for all projects
    all_projects = Project.query.all()
    
    # 3. Pass both the stats AND the projects list
    return render_template('report.html', 
                           total=total_reports, 
                           verified=verified_count,
                           projects=all_projects)


def add_transaction():
    # Capture data from a form
    new_tx = FinancialTransaction(
        project_id=request.form['project_id'],
        transaction_date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
        amount=float(request.form['amount']),
        description=request.form['description'],
        recipient=request.form['recipient'],
        reference_number=request.form['ref']
    )
    db.session.add(new_tx)
    db.session.commit()
    return "Transaction added successfully!"


@citizen_bp.route('/projects/export/csv/<int:project_id>')
def export_report_csv(project_id):
    """Exports transaction data to CSV."""
    project = Project.query.get_or_404(project_id)
    transactions = FinancialTransaction.query.filter_by(project_id=project_id).all()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Recipient', 'Description', 'Amount'])
    for tx in transactions:
        cw.writerow([tx.transaction_date, tx.recipient, tx.description, tx.amount])

    output = io.BytesIO(si.getvalue().encode('utf-8'))
    return send_file(
        output,
        mimetype='text/csv',
        download_name=f'project_{project.id}_transactions.csv',
        as_attachment=True
    )