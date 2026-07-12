# manage.py
import os
import sys
from dotenv import load_dotenv
from app import create_app, db
from app.models import Province, District, Constituency




env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)
load_dotenv()

def run_seeding():
    """Seeds the database with foundational Zambian structural data."""
    print("Initializing structural database seeding matrix...")
    
    # 1. Create Sample Province
    lusaka_prov = Province.query.filter_by(name="Lusaka").first()
    if not lusaka_prov:
        lusaka_prov = Province(name="Lusaka")
        db.session.add(lusaka_prov)
        db.session.commit()
    
    # 2. Create Sample District
    lusaka_dist = District.query.filter_by(name="Lusaka District").first()
    if not lusaka_dist:
        lusaka_dist = District(name="Lusaka District", province_id=lusaka_prov.id)
        db.session.add(lusaka_dist)
        db.session.commit()
        
    # 3. Create Sample Constituency
    central_const = Constituency.query.filter_by(name="Lusaka Central").first()
    if not central_const:
        central_const = Constituency(
            name="Lusaka Central", 
            district_id=lusaka_dist.id,
            latitude=-15.4167,
            longitude=28.2833
        )
        db.session.add(central_const)
        db.session.commit()
        print("Seeding completed successfully! Sample structures active.")
    else:
        print("Database already contains structural entities. Skipping.")

if __name__ == '__main__':
    with app.app_context():
        # Build relational tables automatically if missing
        db.create_all()
        
        # Check if the user passed 'seed-db' as an argument manually
        if len(sys.argv) > 1 and sys.argv[1] == 'seed-db':
            run_seeding()
        else:
            # Default fallback behavior: Run the application development server
            print("Booting KwachaTrack Engine...")
            app.run(
                host=os.environ.get('HOST', '127.0.0.1'),
                port=int(os.environ.get('PORT', 5000)),
                debug=True
            )