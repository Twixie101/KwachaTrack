from flask import Blueprint, jsonify, request, send_file
from app.models import db, Constituency, Project, CitizenFeedback, VerificationStatus
from decimal import Decimal
import io
import csv
from sqlalchemy import func

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def decimal_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

@api_bp.route('/constituencies', methods=['GET'])
def get_constituencies():
    constituencies = Constituency.query.all()
    output = []
    for c in constituencies:
        total_budget = db.session.query(func.sum(Project.budget)).filter(Project.constituency_id == c.id).scalar() or 0
        output.append({
            'id': c.id,
            'name': c.name,
            'latitude': c.latitude,
            'longitude': c.longitude,
            'total_project_budget': float(total_budget)
        })
    return jsonify({'success': True, 'data': output})

# --- NEW GLOBAL ENDPOINT: GET ALL PROJECTS ACROSS ZAMBIA ---
@api_bp.route('/projects', methods=['GET'])
def get_all_projects():
    """Fetches every single tracked CDF project for national overview monitoring."""
    try:
        # Join with Constituency model to display the region name alongside the project details
        projects = db.session.query(Project, Constituency.name).join(
            Constituency, Project.constituency_id == Constituency.id
        ).all()
        
        output = []
        for p, constituency_name in projects:
            output.append({
                'id': p.id,
                'title': p.title,
                'constituency_name': constituency_name,
                'budget': float(p.budget),
                'expended': float(p.expended_amount),
                'status': p.status.value,
                'progress': p.progress_percentage or 0
            })
            
        return jsonify({'success': True, 'data': output}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/projects/<int:constituency_id>', methods=['GET'])
def get_projects_by_constituency(constituency_id):
    projects = Project.query.filter_by(constituency_id=constituency_id).all()
    output = []
    for p in projects:
        output.append({
            'id': p.id,
            'title': p.title,
            'budget': float(p.budget),
            'expended': float(p.expended_amount),
            'status': p.status.value,
            'progress': p.progress_percentage
        })
    return jsonify({'success': True, 'data': output})


@api_bp.route('/reports/export/csv/<int:constituency_id>', methods=['GET'])
def export_constituency_csv(constituency_id):
    projects = Project.query.filter_by(constituency_id=constituency_id).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Project ID', 'Title', 'Budget (ZMW)', 'Expended (ZMW)', 'Status', 'Progress %', 'Contractor'])
    
    for p in projects:
        cw.writerow([p.id, p.title, p.budget, p.expended_amount, p.status.value, p.progress_percentage, p.contractor_name])
    
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'CDF_Report_Constituency_{constituency_id}.csv'
    )

from flask import Blueprint, jsonify
from app.models import Project

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/v1/projects', methods=['GET'])
def get_all_projects():
    projects = Project.query.all()
    output = []
    
    for proj in projects:
        # Collect evidence images from the relationship
        images = []
        for feedback in proj.feedbacks:
            for evidence in feedback.evidence_attachments:
                images.append(evidence.file_secure_url)
        
        project_data = {
            'id': proj.id,
            'title': proj.title,
            'constituency': proj.constituency.name if proj.constituency else "N/A",
            'progress': proj.progress_percentage,
            'budget': float(proj.budget),
            'status': proj.status,
            'images': images # List of image URLs
        }
        output.append(project_data)
        
    return jsonify({'projects': output})