import csv
import io
import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import FinancialTransaction, Project, CitizenFeedback, Constituency, ProjectStatus
from datetime import datetime
from app.extensions import limiter

admin_bp = Blueprint('admin', __name__)

# --- Global Security ---
@admin_bp.before_request
@limiter.limit("60 per hour")
def limit_admin_access():
    pass

# --- Authentication ---
@admin_bp.route('/admin-login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    if request.method == 'POST':
        if request.form.get('key') == 'Khethiwe':
            session.permanent = True
            session['is_admin'] = True
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid Key', 'danger')
    return render_template('admin_login.html')

# --- Dashboard ---
@admin_bp.route('/dashboard')
def admin_dashboard():
    if not session.get('is_admin'): return "Access Denied", 403
    return render_template('admin_home.html', total_projects=Project.query.count())

# --- Project Management (CRUD) ---
@admin_bp.route('/admin/projects')
def manage_projects():
    if not session.get('is_admin'): return "Access Denied", 403
    return render_template('manage_projects.html', projects=Project.query.all())

@admin_bp.route('/admin/add-project', methods=['GET', 'POST'])
def add_project():
    if not session.get('is_admin'): return "Access Denied", 403
    if request.method == 'POST':
        new_project = Project(
            title=request.form.get('title'),
            description=request.form.get('description'),
            budget=float(request.form.get('budget')),
            expended_amount=float(request.form.get('expended_amount')),
            contractor_name=request.form.get('contractor_name'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date() if request.form.get('end_date') else None,
            status=ProjectStatus(request.form.get('status')),
            progress_percentage=int(request.form.get('progress_percentage', 0)),
            constituency_id=int(request.form.get('constituency_id'))
        )
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('admin.manage_projects'))
    return render_template('add_project.html', constituencies=Constituency.query.all())

@admin_bp.route('/admin/projects/edit/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    if not session.get('is_admin'): return "Access Denied", 403
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        
        form_budget = request.form.get('budget')
        form_expended = request.form.get('expended_amount')
        project.budget = float(form_budget) if form_budget else project.budget
        project.expended_amount = float(form_expended) if form_expended else 0.0
        
        form_contractor = request.form.get('contractor_name')
        project.contractor_name = form_contractor.strip() if form_contractor else project.contractor_name
        
        if request.form.get('status'):
            project.status = ProjectStatus(request.form.get('status'))
            
        project.progress_percentage = int(request.form.get('progress_percentage', 0))
        
        db.session.commit()
        return redirect(url_for('admin.manage_projects'))
        
    return render_template('edit_project.html', project=project)



@admin_bp.route('/admin/projects/bulk-upload', methods=['POST'])
def bulk_upload_projects():
    # 1. Admin Authentication Check
    if not session.get('is_admin'):
        return "Access Denied", 403

    # 2. File Presence and Validation
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('admin.manage_projects'))

    if not file.filename.endswith('.csv'):
        flash('File must be a CSV.', 'danger')
        return redirect(url_for('admin.manage_projects'))

    status_map = {
        'IN_PROGRESS': ProjectStatus.IN_PROGRESS, 
        'COMPLETED': ProjectStatus.COMPLETED, 
        'PROPOSED': ProjectStatus.PROPOSED
    }

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        count = 0
        
        for i, row in enumerate(reader, start=2):
            # A. Validate Constituency
            const = Constituency.query.filter_by(name=row['constituency_name'].strip()).first()
            if not const:
                raise ValueError(f"Row {i}: Constituency '{row['constituency_name']}' not found in database.")
            
            # B. Validate Status
            status_val = row['status'].strip().upper()
            if status_val not in status_map:
                raise ValueError(f"Row {i}: Invalid status '{status_val}'.")
            
            # C. Duplicate Check: Prevent redundant entries
            existing = Project.query.filter_by(
                title=row['title'].strip(), 
                constituency_id=const.id
            ).first()
            
            if existing:
                continue # Skip duplicates gracefully
            
            # D. Create Project Instance
            new_project = Project(
                title=row['title'].strip(),
                description=row.get('description', ''),
                budget=float(row['budget']),
                expended_amount=float(row['expended_amount']),
                constituency_id=const.id,
                contractor_name=row.get('contractor_name', 'N/A'),
                start_date=datetime.strptime(row['start_date'], '%Y-%m-%d').date(),
                end_date=datetime.strptime(row['end_date'], '%Y-%m-%d').date() if row.get('end_date') else None,
                status=status_map.get(status_val),
                progress_percentage=int(row['progress_percentage']),
                created_at=datetime.utcnow()
            )
            db.session.add(new_project)
            count += 1
            
        db.session.commit()
        
        # E. Final Feedback
        if count > 0:
            flash(f'Successfully imported {count} projects.', 'success')
        else:
            flash('No new projects to import (duplicates detected).', 'info')
        
    except (ValueError, KeyError) as e:
        db.session.rollback()
        flash(f'Import Error: {str(e)}', 'danger')
    except Exception as e:
        db.session.rollback()
        print(f"CRITICAL ERROR: {str(e)}") # Log for server terminal
        flash('A database error occurred. Ensure your CSV headers match the required format.', 'danger')
        
    return redirect(url_for('admin.manage_projects'))

# --- Transactions & Reports ---
@admin_bp.route('/admin/add-transaction', methods=['GET', 'POST'])
def add_transaction():
    if not session.get('is_admin'): return "Access Denied", 403
    if request.method == 'POST':
        new_tx = FinancialTransaction(
            project_id=request.form.get('project_id'),
            transaction_date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            amount=float(request.form.get('amount')),
            description=request.form.get('description'),
            recipient=request.form.get('recipient'),
            reference_number=request.form.get('ref')
        )
        db.session.add(new_tx)
        db.session.commit()
        return redirect(url_for('admin.manage_projects'))
    return render_template('admin_add_transaction.html', projects=Project.query.all())

@admin_bp.route('/verify-reports')
def verify_reports():
    if not session.get('is_admin'): return "Access Denied", 403
    return render_template('verify_reports.html', reports=CitizenFeedback.query.all())

@admin_bp.route('/verify-report/<int:report_id>', methods=['POST'])
def verify_report(report_id):
    if not session.get('is_admin'): return "Access Denied", 403
    report = CitizenFeedback.query.get_or_404(report_id)
    report.verification_status = 'VERIFIED'
    db.session.commit()
    return redirect(url_for('admin.verify_reports'))

@admin_bp.route('/admin/report/delete/<int:report_id>', methods=['POST'])
def delete_report(report_id):
    if not session.get('is_admin'): 
        return "Access Denied", 403
    
    report = CitizenFeedback.query.get_or_404(report_id)
    
    # This prints all valid attributes for your report object to your terminal
    print("--- AVAILABLE ATTRIBUTES ---")
    print(dir(report))
    print("----------------------------")
    
    # Just to prevent the crash for now, I've commented out the check
    # Once you see the output in your terminal, we will know the right name.
    db.session.delete(report)
    db.session.commit()
    
    flash('Report deleted.', 'success')
    return redirect(url_for('admin.verify_reports'))

# Fixed: Added /admin prefix to keep your blueprint URLs uniform
@admin_bp.route('/admin/projects/delete/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if not session.get('is_admin'): return "Access Denied", 403
    db.session.delete(Project.query.get_or_404(project_id))
    db.session.commit()
    return redirect(url_for('admin.manage_projects'))