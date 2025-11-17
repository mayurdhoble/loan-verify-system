from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from agents.doc_agent import DocumentAgent
from agents.web_agent import WebAgent
from utils.matcher import FieldMatcher
from models.database import User, Member, DocumentExtraction, WebExtraction, Verification, init_db, get_session
from config import Config
import os
import csv
from io import StringIO, BytesIO
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.DATA_FOLDER, exist_ok=True)

# Initialize database
app.secret_key = Config.SECRET_KEY

# Initialize
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data', exist_ok=True)
init_db()

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db = get_session()
    user = db.query(User).get(int(user_id))
    db.close()
    return user

# Agents
doc_agent = DocumentAgent()
web_agent = WebAgent()
matcher = FieldMatcher()

# ============= AUTH ROUTES =============

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        db = get_session()
        
        # Check existing
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            flash('Username or email already exists', 'error')
            db.close()
            return redirect(url_for('signup'))
        
        # Create user
        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        
        db.add(user)
        db.commit()
        db.close()
        
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_session()
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if user and user.check_password(password):
            login_user(user)
            db.close()
            return redirect(url_for('dashboard'))
        
        db.close()
        flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ============= MAIN ROUTES =============

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # Get files
        doc_dfr = request.files.get('doc_dfr')
        doc_pa = request.files.get('doc_pa')
        doc_title = request.files.get('doc_title')
        profile_url = request.form.get('profile_url')
        
        if not all([doc_dfr, doc_pa, doc_title, profile_url]):
            flash('Please provide all 3 documents and profile URL', 'error')
            return redirect(url_for('upload'))
        
        db = get_session()
        
        # Get next member_id
        last_member = db.query(Member).order_by(Member.member_id.desc()).first()
        next_member_id = (last_member.member_id + 1) if last_member else 1
        
        # Save files
        files_saved = []
        for file, doc_type in [(doc_dfr, 'dfr'), (doc_pa, 'pa'), (doc_title, 'title')]:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                new_filename = f"member_{next_member_id}_{doc_type}_{filename}"
                filepath = os.path.join(Config.UPLOAD_FOLDER, new_filename)
                file.save(filepath)
                files_saved.append(filepath)
        
        # Create member record
        member = Member(
            member_id=next_member_id,
            doc_dfr=files_saved[0] if len(files_saved) > 0 else None,
            doc_pa=files_saved[1] if len(files_saved) > 1 else None,
            doc_title=files_saved[2] if len(files_saved) > 2 else None,
            profile_url=profile_url,
            uploaded_by=current_user.id
        )
        
        db.add(member)
        db.commit()
        db.close()
        
        flash(f'Member ID {next_member_id} created successfully!', 'success')
        return redirect(url_for('profiles'))
    
    return render_template('upload.html')

@app.route('/profiles')
@login_required
def profiles():
    db = get_session()
    members = db.query(Member).order_by(Member.member_id).all()
    db.close()
    
    return render_template('profiles.html', members=members)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        return redirect(url_for('search') + f'?id={member_id}')
    
    member_id = request.args.get('id')
    member = None
    
    if member_id:
        db = get_session()
        member = db.query(Member).filter_by(member_id=int(member_id)).first()
        db.close()
    
    return render_template('search.html', member=member)

@app.route('/verify/<int:member_id>')
@login_required
def verify(member_id):
    db = get_session()
    
    # Get member
    member = db.query(Member).filter_by(member_id=member_id).first()
    
    if not member:
        flash('Member not found', 'error')
        db.close()
        return redirect(url_for('search'))
    
    # Agent 1: Extract from documents
    doc_paths = [member.doc_dfr, member.doc_pa, member.doc_title]
    doc_paths = [p for p in doc_paths if p and os.path.exists(p)]
    
    doc_data = doc_agent.process(doc_paths)
    
    # Save document extraction
    doc_extraction = DocumentExtraction(
        member_id=member_id,
        applicant_name=doc_data.get('applicant_name'),
        vin=doc_data.get('vin'),
        loan_amount=doc_data.get('loan_amount'),
        routing_no=doc_data.get('routing_no'),
        account_no=doc_data.get('account_no')
    )
    db.add(doc_extraction)
    db.commit()
    
    # Agent 2: Extract from web
    web_data = web_agent.process(member.profile_url)
    
    # Save web extraction
    web_extraction = WebExtraction(
        member_id=member_id,
        profile_url=member.profile_url,
        applicant_name=web_data.get('applicant_name'),
        vin=web_data.get('vin'),
        loan_amount=web_data.get('loan_amount'),
        routing_no=web_data.get('routing_no'),
        account_no=web_data.get('account_no')
    )
    db.add(web_extraction)
    db.commit()
    
    # Agent 3: Compare and verify
    comparison = matcher.compare(doc_data, web_data)
    
    # Save verification
    verification = Verification(
        member_id=member_id,
        user_id=current_user.id,
        similarity_score=comparison['similarity_score'],
        status=comparison['status'],
        matched_fields=comparison['matched_fields'],
        mismatched_fields=comparison['mismatched_fields'],
        doc_extraction_id=doc_extraction.id,
        web_extraction_id=web_extraction.id
    )
    db.add(verification)
    db.commit()
    
    verification_id = verification.id
    db.close()
    
    flash(f'Verification completed! Status: {comparison["status"]}', 
          'success' if comparison['status'] == 'Verified' else 'warning')
    
    return redirect(url_for('history'))

@app.route('/history')
@login_required
def history():
    db = get_session()
    verifications = db.query(Verification).order_by(Verification.verification_date.desc()).all()
    
    # Get member info for each verification
    results = []
    for v in verifications:
        member = db.query(Member).filter_by(member_id=v.member_id).first()
        doc_ext = db.query(DocumentExtraction).get(v.doc_extraction_id)
        
        results.append({
            'verification': v,
            'member': member,
            'doc_extraction': doc_ext
        })
    
    db.close()
    
    return render_template('history.html', results=results)

@app.route('/export-csv')
@login_required
def export_csv():
    db = get_session()
    verifications = db.query(Verification).order_by(Verification.verification_date.desc()).all()
    
    # Create CSV in text mode
    text_stream = StringIO()
    writer = csv.writer(text_stream)
    
    # Header
    writer.writerow(['ID', 'Member ID', 'Status', 'Similarity Score', 'Matched Fields', 
                     'Mismatched Fields', 'Date'])
    
    # Data
    for v in verifications:
        writer.writerow([
            v.id,
            v.member_id,
            v.status,
            v.similarity_score,
            len(v.matched_fields) if v.matched_fields else 0,
            len(v.mismatched_fields) if v.mismatched_fields else 0,
            v.verification_date.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    db.close()

    # Convert to binary stream for send_file
    binary_stream = BytesIO()
    binary_stream.write(text_stream.getvalue().encode('utf-8'))
    binary_stream.seek(0)

    return send_file(
        binary_stream,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'verifications_{datetime.now().strftime("%Y%m%d")}.csv'
    )

# ============= API ROUTES FOR DASHBOARD =============

@app.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    db = get_session()
    
    # Total profiles
    total_profiles = db.query(Member).count()
    
    # Verifications
    verifications = db.query(Verification).all()
    
    # Today's verifications
    today = datetime.now().date()
    verified_today = sum(1 for v in verifications 
                        if v.verification_date.date() == today and v.status == 'Verified')
    
    # Success rate
    verified_count = sum(1 for v in verifications if v.status == 'Verified')
    total_verifications = len(verifications)
    success_rate = round((verified_count / total_verifications * 100), 1) if total_verifications > 0 else 0
    
    # Pending
    pending = total_profiles - total_verifications
    
    # Recent verifications (last 5)
    recent = db.query(Verification).order_by(Verification.verification_date.desc()).limit(5).all()
    recent_data = []
    for v in recent:
        recent_data.append({
            'member_id': v.member_id,
            'status': v.status,
            'similarity_score': v.similarity_score,
            'matched_count': len(v.matched_fields) if v.matched_fields else 0,
            'mismatched_count': len(v.mismatched_fields) if v.mismatched_fields else 0,
            'verification_date': v.verification_date.isoformat()
        })
    
    db.close()
    
    return jsonify({
        'total_profiles': total_profiles,
        'verified_today': verified_today,
        'pending': max(0, pending),
        'success_rate': success_rate,
        'recent_verifications': recent_data
    })

# ============= DOCUMENTATION ROUTES =============

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

@app.route('/help')
def help_page():
    return render_template('help.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api-guide')
@login_required
def api_guide():
    return render_template('api_guide.html')

if __name__ == '__main__':
    # For local development
    app.run(debug=True, port=5002)