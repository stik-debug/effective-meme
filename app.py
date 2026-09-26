from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import os
import json

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# ==================== MODELS ====================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='member')  # member, treasurer, chairperson
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    memberships = db.relationship('Membership', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Chama(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    contribution_amount = db.Column(db.Float, default=1000.0)  # Monthly contribution in KES
    contribution_day = db.Column(db.Integer, default=5)  # Day of month
    loan_interest_rate = db.Column(db.Float, default=5.0)  # % per month
    max_loan_multiplier = db.Column(db.Float, default=3.0)  # Max loan = savings * multiplier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    memberships = db.relationship('Membership', backref='chama', lazy=True)
    contributions = db.relationship('Contribution', backref='chama', lazy=True)
    loans = db.relationship('Loan', backref='chama', lazy=True)
    merry_go_rounds = db.relationship('MerryGoRound', backref='chama', lazy=True)
    meetings = db.relationship('Meeting', backref='chama', lazy=True)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chama_id = db.Column(db.Integer, db.ForeignKey('chama.id'), nullable=False)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_savings = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    role_in_chama = db.Column(db.String(20), default='member')  # member, treasurer, chairperson, secretary

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chama.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    contribution_date = db.Column(db.Date, default=date.today)
    month = db.Column(db.String(7))  # YYYY-MM
    payment_method = db.Column(db.String(30), default='Cash')  # Cash, M-Pesa, Bank
    mpesa_code = db.Column(db.String(20))
    notes = db.Column(db.String(200))
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', foreign_keys=[user_id])

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chama.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    total_repayable = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, default=0.0)
    purpose = db.Column(db.String(200))
    status = db.Column(db.String(20), default='pending')  # pending, approved, active, repaid, rejected
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    due_date = db.Column(db.Date)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    user = db.relationship('User', foreign_keys=[user_id])
    repayments = db.relationship('LoanRepayment', backref='loan', lazy=True)

class LoanRepayment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=date.today)
    payment_method = db.Column(db.String(30), default='Cash')
    mpesa_code = db.Column(db.String(20))
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MerryGoRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chama.id'), nullable=False)
    name = db.Column(db.String(100), default='Merry Go Round')
    contribution_per_member = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, default=date.today)
    frequency = db.Column(db.String(20), default='monthly')  # weekly, monthly
    is_active = db.Column(db.Boolean, default=True)
    
    rounds = db.relationship('MGRRound', backref='merry_go_round', lazy=True, order_by='MGRRound.round_number')

class MGRRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mgr_id = db.Column(db.Integer, db.ForeignKey('merry_go_round.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scheduled_date = db.Column(db.Date)
    amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, paid, skipped
    paid_date = db.Column(db.Date)
    
    recipient = db.relationship('User')

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chama.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    meeting_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    agenda = db.Column(db.Text)
    minutes = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    present = db.Column(db.Boolean, default=False)
    apology = db.Column(db.String(200))


class MpesaTransaction(db.Model):
    """Tracks STK Push requests and their status"""
    id = db.Column(db.Integer, primary_key=True)
    chama_id = db.Column(db.Integer, db.ForeignKey('chama.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    purpose = db.Column(db.String(50))  # contribution, loan_repayment
    reference = db.Column(db.String(50))  # our internal ref
    checkout_request_id = db.Column(db.String(100))
    merchant_request_id = db.Column(db.String(100))
    mpesa_receipt = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, cancelled
    result_desc = db.Column(db.String(200))
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', foreign_keys=[user_id])


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== HELPERS ====================

def get_user_chamas(user):
    return Chama.query.join(Membership).filter(
        Membership.user_id == user.id,
        Membership.is_active == True
    ).all()

def get_membership(user_id, chama_id):
    return Membership.query.filter_by(user_id=user_id, chama_id=chama_id, is_active=True).first()

def is_treasurer_or_chair(user, chama_id):
    m = get_membership(user.id, chama_id)
    if not m:
        return False
    return m.role_in_chama in ['treasurer', 'chairperson'] or user.role in ['treasurer', 'chairperson']

def calculate_group_balance(chama_id):
    total_contrib = db.session.query(db.func.sum(Contribution.amount)).filter_by(chama_id=chama_id).scalar() or 0
    total_loans = db.session.query(db.func.sum(Loan.amount)).filter(
        Loan.chama_id == chama_id,
        Loan.status.in_(['approved', 'active'])
    ).scalar() or 0
    total_repaid = db.session.query(db.func.sum(LoanRepayment.amount)).join(Loan).filter(
        Loan.chama_id == chama_id
    ).scalar() or 0
    return total_contrib - total_loans + total_repaid

# ==================== ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        if not name or not phone or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')
        
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already registered.', 'danger')
            return render_template('register.html')
        
        user = User(name=name, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(phone=phone).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        
        flash('Invalid phone or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    chamas = get_user_chamas(current_user)
    
    # Stats
    total_savings = 0
    active_loans = 0
    for c in chamas:
        m = get_membership(current_user.id, c.id)
        if m:
            total_savings += m.total_savings
        loans = Loan.query.filter_by(user_id=current_user.id, chama_id=c.id, status='active').all()
        active_loans += sum(l.total_repayable - l.amount_paid for l in loans)
    
    upcoming_meetings = Meeting.query.join(Membership, Meeting.chama_id == Membership.chama_id).filter(
        Membership.user_id == current_user.id,
        Meeting.meeting_date >= datetime.now(),
        Meeting.status == 'scheduled'
    ).order_by(Meeting.meeting_date).limit(5).all()
    
    return render_template('dashboard.html',
                           chamas=chamas,
                           total_savings=total_savings,
                           active_loans=active_loans,
                           upcoming_meetings=upcoming_meetings)

@app.route('/chama/create', methods=['GET', 'POST'])
@login_required
def create_chama():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        amount = float(request.form.get('contribution_amount', 1000))
        day = int(request.form.get('contribution_day', 5))
        interest = float(request.form.get('loan_interest_rate', 5))
        
        if not name:
            flash('Chama name is required.', 'danger')
            return render_template('create_chama.html')
        
        chama = Chama(
            name=name,
            description=description,
            contribution_amount=amount,
            contribution_day=day,
            loan_interest_rate=interest
        )
        db.session.add(chama)
        db.session.flush()
        
        # Creator becomes chairperson
        membership = Membership(
            user_id=current_user.id,
            chama_id=chama.id,
            role_in_chama='chairperson',
            total_savings=0
        )
        db.session.add(membership)
        db.session.commit()
        
        flash(f'Chama "{name}" created successfully!', 'success')
        return redirect(url_for('chama_detail', chama_id=chama.id))
    
    return render_template('create_chama.html')

@app.route('/chama/<int:chama_id>')
@login_required
def chama_detail(chama_id):
    chama = Chama.query.get_or_404(chama_id)
    membership = get_membership(current_user.id, chama_id)
    
    if not membership:
        flash('You are not a member of this Chama.', 'danger')
        return redirect(url_for('dashboard'))
    
    members = Membership.query.filter_by(chama_id=chama_id, is_active=True).all()
    recent_contribs = Contribution.query.filter_by(chama_id=chama_id).order_by(Contribution.created_at.desc()).limit(10).all()
    active_loans = Loan.query.filter(
        Loan.chama_id == chama_id,
        Loan.status.in_(['pending', 'active', 'approved'])
    ).all()
    
    group_balance = calculate_group_balance(chama_id)
    is_admin = is_treasurer_or_chair(current_user, chama_id)
    
    # Merry go round
    mgr = MerryGoRound.query.filter_by(chama_id=chama_id, is_active=True).first()
    
    return render_template('chama_detail.html',
                           chama=chama,
                           membership=membership,
                           members=members,
                           recent_contribs=recent_contribs,
                           active_loans=active_loans,
                           group_balance=group_balance,
                           is_admin=is_admin,
                           mgr=mgr)

@app.route('/chama/<int:chama_id>/members')
@login_required
def chama_members(chama_id):
    chama = Chama.query.get_or_404(chama_id)
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    members = Membership.query.filter_by(chama_id=chama_id, is_active=True).all()
    is_admin = is_treasurer_or_chair(current_user, chama_id)
    
    return render_template('members.html', chama=chama, members=members, is_admin=is_admin)

@app.route('/chama/<int:chama_id>/add_member', methods=['POST'])
@login_required
def add_member(chama_id):
    if not is_treasurer_or_chair(current_user, chama_id):
        flash('Only treasurer or chairperson can add members.', 'danger')
        return redirect(url_for('chama_members', chama_id=chama_id))
    
    phone = request.form.get('phone', '').strip()
    role = request.form.get('role', 'member')
    
    user = User.query.filter_by(phone=phone).first()
    if not user:
        flash('User with that phone not found. They must register first.', 'danger')
        return redirect(url_for('chama_members', chama_id=chama_id))
    
    existing = get_membership(user.id, chama_id)
    if existing:
        flash('User is already a member.', 'warning')
        return redirect(url_for('chama_members', chama_id=chama_id))
    
    membership = Membership(user_id=user.id, chama_id=chama_id, role_in_chama=role)
    db.session.add(membership)
    db.session.commit()
    
    flash(f'{user.name} added successfully!', 'success')
    return redirect(url_for('chama_members', chama_id=chama_id))

@app.route('/chama/<int:chama_id>/contributions')
@login_required
def contributions(chama_id):
    chama = Chama.query.get_or_404(chama_id)
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    contribs = Contribution.query.filter_by(chama_id=chama_id).order_by(Contribution.contribution_date.desc()).all()
    is_admin = is_treasurer_or_chair(current_user, chama_id)
    members = Membership.query.filter_by(chama_id=chama_id, is_active=True).all()
    
    return render_template('contributions.html',
                           chama=chama,
                           contribs=contribs,
                           is_admin=is_admin,
                           members=members)

@app.route('/chama/<int:chama_id>/add_contribution', methods=['POST'])
@login_required
def add_contribution(chama_id):
    if not is_treasurer_or_chair(current_user, chama_id):
        flash('Only treasurer or chairperson can record contributions.', 'danger')
        return redirect(url_for('contributions', chama_id=chama_id))
    
    user_id = int(request.form.get('user_id'))
    amount = float(request.form.get('amount'))
    contrib_date = request.form.get('contribution_date')
    method = request.form.get('payment_method', 'Cash')
    mpesa = request.form.get('mpesa_code', '')
    notes = request.form.get('notes', '')
    
    if contrib_date:
        contrib_date = datetime.strptime(contrib_date, '%Y-%m-%d').date()
    else:
        contrib_date = date.today()
    
    month = contrib_date.strftime('%Y-%m')
    
    contrib = Contribution(
        chama_id=chama_id,
        user_id=user_id,
        amount=amount,
        contribution_date=contrib_date,
        month=month,
        payment_method=method,
        mpesa_code=mpesa if method == 'M-Pesa' else None,
        notes=notes,
        recorded_by=current_user.id
    )
    db.session.add(contrib)
    
    # Update member savings
    membership = get_membership(user_id, chama_id)
    if membership:
        membership.total_savings += amount
    
    db.session.commit()
    
    # Send SMS notification
    try:
        from services.sms import SMSService
        user = User.query.get(user_id)
        chama = Chama.query.get(chama_id)
        if user and chama and membership:
            sms = SMSService()
            sms.notify_contribution_received(
                user.phone, user.name, amount, chama.name, membership.total_savings
            )
    except Exception as e:
        print(f'SMS error: {e}')
    
    flash('Contribution recorded successfully! SMS sent to member.', 'success')
    return redirect(url_for('contributions', chama_id=chama_id))

@app.route('/chama/<int:chama_id>/loans')
@login_required
def loans(chama_id):
    chama = Chama.query.get_or_404(chama_id)
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    all_loans = Loan.query.filter_by(chama_id=chama_id).order_by(Loan.application_date.desc()).all()
    is_admin = is_treasurer_or_chair(current_user, chama_id)
    
    return render_template('loans.html',
                           chama=chama,
                           loans=all_loans,
                           is_admin=is_admin,
                           membership=membership)

@app.route('/chama/<int:chama_id>/apply_loan', methods=['POST'])
@login_required
def apply_loan(chama_id):
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    chama = Chama.query.get_or_404(chama_id)
    amount = float(request.form.get('amount'))
    purpose = request.form.get('purpose', '')
    
    max_loan = membership.total_savings * chama.max_loan_multiplier
    if amount > max_loan:
        flash(f'Maximum loan allowed is KES {max_loan:,.0f} (based on your savings).', 'danger')
        return redirect(url_for('loans', chama_id=chama_id))
    
    if amount <= 0:
        flash('Invalid amount.', 'danger')
        return redirect(url_for('loans', chama_id=chama_id))
    
    total_repayable = amount * (1 + chama.loan_interest_rate / 100)
    
    loan = Loan(
        chama_id=chama_id,
        user_id=current_user.id,
        amount=amount,
        interest_rate=chama.loan_interest_rate,
        total_repayable=total_repayable,
        purpose=purpose,
        status='pending',
        due_date=date.today() + relativedelta(months=3)
    )
    db.session.add(loan)
    db.session.commit()
    
    flash('Loan application submitted successfully!', 'success')
    return redirect(url_for('loans', chama_id=chama_id))

@app.route('/loan/<int:loan_id>/approve', methods=['POST'])
@login_required
def approve_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if not is_treasurer_or_chair(current_user, loan.chama_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    action = request.form.get('action')
    user = User.query.get(loan.user_id)
    chama = Chama.query.get(loan.chama_id)
    
    if action == 'approve':
        loan.status = 'active'
        loan.approval_date = datetime.utcnow()
        loan.approved_by = current_user.id
        flash('Loan approved! SMS sent to member.', 'success')
        
        try:
            from services.sms import SMSService
            if user and chama:
                sms = SMSService()
                sms.notify_loan_approved(user.phone, user.name, loan.amount, chama.name, loan.total_repayable)
        except Exception as e:
            print(f'SMS error: {e}')
    else:
        loan.status = 'rejected'
        flash('Loan rejected. SMS sent to member.', 'info')
        
        try:
            from services.sms import SMSService
            if user and chama:
                sms = SMSService()
                sms.notify_loan_rejected(user.phone, user.name, loan.amount, chama.name)
        except Exception as e:
            print(f'SMS error: {e}')
    
    db.session.commit()
    return redirect(url_for('loans', chama_id=loan.chama_id))

@app.route('/loan/<int:loan_id>/repay', methods=['POST'])
@login_required
def repay_loan(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    if not is_treasurer_or_chair(current_user, loan.chama_id) and loan.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    amount = float(request.form.get('amount'))
    method = request.form.get('payment_method', 'Cash')
    mpesa = request.form.get('mpesa_code', '')
    
    if amount <= 0:
        flash('Invalid amount.', 'danger')
        return redirect(url_for('loans', chama_id=loan.chama_id))
    
    remaining = loan.total_repayable - loan.amount_paid
    if amount > remaining:
        amount = remaining
    
    repayment = LoanRepayment(
        loan_id=loan.id,
        amount=amount,
        payment_method=method,
        mpesa_code=mpesa if method == 'M-Pesa' else None,
        recorded_by=current_user.id
    )
    db.session.add(repayment)
    
    loan.amount_paid += amount
    if loan.amount_paid >= loan.total_repayable:
        loan.status = 'repaid'
    
    db.session.commit()
    flash(f'Repayment of KES {amount:,.0f} recorded!', 'success')
    return redirect(url_for('loans', chama_id=loan.chama_id))

@app.route('/chama/<int:chama_id>/mgr')
@login_required
def merry_go_round(chama_id):
    chama = Chama.query.get_or_404(chama_id)
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    mgr = MerryGoRound.query.filter_by(chama_id=chama_id, is_active=True).first()
    is_admin = is_treasurer_or_chair(current_user, chama_id)
    members = Membership.query.filter_by(chama_id=chama_id, is_active=True).all()
    
    return render_template('mgr.html', chama=chama, mgr=mgr, is_admin=is_admin, members=members)

@app.route('/chama/<int:chama_id>/create_mgr', methods=['POST'])
@login_required
def create_mgr(chama_id):
    if not is_treasurer_or_chair(current_user, chama_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('merry_go_round', chama_id=chama_id))
    
    # Deactivate existing
    existing = MerryGoRound.query.filter_by(chama_id=chama_id, is_active=True).all()
    for e in existing:
        e.is_active = False
    
    name = request.form.get('name', 'Merry Go Round')
    amount = float(request.form.get('contribution_per_member'))
    frequency = request.form.get('frequency', 'monthly')
    
    mgr = MerryGoRound(
        chama_id=chama_id,
        name=name,
        contribution_per_member=amount,
        frequency=frequency
    )
    db.session.add(mgr)
    db.session.flush()
    
    # Create rounds for all members
    members = Membership.query.filter_by(chama_id=chama_id, is_active=True).all()
    start = date.today()
    
    for i, m in enumerate(members):
        if frequency == 'monthly':
            sched = start + relativedelta(months=i)
        else:
            sched = start + timedelta(weeks=i)
        
        total_pot = amount * len(members)
        round_obj = MGRRound(
            mgr_id=mgr.id,
            round_number=i + 1,
            recipient_id=m.user_id,
            scheduled_date=sched,
            amount=total_pot,
            status='upcoming'
        )
        db.session.add(round_obj)
    
    db.session.commit()
    flash('Merry Go Round created successfully!', 'success')
    return redirect(url_for('merry_go_round', chama_id=chama_id))

@app.route('/mgr_round/<int:round_id>/mark_paid', methods=['POST'])
@login_required
def mark_mgr_paid(round_id):
    rnd = MGRRound.query.get_or_404(round_id)
    mgr = MerryGoRound.query.get(rnd.mgr_id)
    
    if not is_treasurer_or_chair(current_user, mgr.chama_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('merry_go_round', chama_id=mgr.chama_id))
    
    rnd.status = 'paid'
    rnd.paid_date = date.today()
    db.session.commit()
    
    # SMS to recipient
    try:
        from services.sms import SMSService
        chama = Chama.query.get(mgr.chama_id)
        if chama and rnd.recipient:
            sms = SMSService()
            sms.notify_mgr_payout(
                rnd.recipient.phone, rnd.recipient.name,
                rnd.amount or 0, rnd.round_number, chama.name
            )
    except Exception as e:
        print(f'SMS error: {e}')
    
    flash(f'Round {rnd.round_number} marked as paid to {rnd.recipient.name}! SMS sent.', 'success')
    return redirect(url_for('merry_go_round', chama_id=mgr.chama_id))

@app.route('/chama/<int:chama_id>/meetings')
@login_required
def meetings(chama_id):
    chama = Chama.query.get_or_404(chama_id)
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    all_meetings = Meeting.query.filter_by(chama_id=chama_id).order_by(Meeting.meeting_date.desc()).all()
    is_admin = is_treasurer_or_chair(current_user, chama_id)
    
    return render_template('meetings.html', chama=chama, meetings=all_meetings, is_admin=is_admin)

@app.route('/chama/<int:chama_id>/add_meeting', methods=['POST'])
@login_required
def add_meeting(chama_id):
    if not is_treasurer_or_chair(current_user, chama_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('meetings', chama_id=chama_id))
    
    title = request.form.get('title')
    meeting_date = request.form.get('meeting_date')
    location = request.form.get('location', '')
    agenda = request.form.get('agenda', '')
    
    dt = datetime.strptime(meeting_date, '%Y-%m-%dT%H:%M')
    
    meeting = Meeting(
        chama_id=chama_id,
        title=title,
        meeting_date=dt,
        location=location,
        agenda=agenda,
        created_by=current_user.id
    )
    db.session.add(meeting)
    db.session.commit()
    
    flash('Meeting scheduled!', 'success')
    return redirect(url_for('meetings', chama_id=chama_id))

@app.route('/chama/<int:chama_id>/reports')
@login_required
def reports(chama_id):
    chama = Chama.query.get_or_404(chama_id)
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    members = Membership.query.filter_by(chama_id=chama_id, is_active=True).all()
    
    # Member statements
    statements = []
    for m in members:
        contribs = Contribution.query.filter_by(chama_id=chama_id, user_id=m.user_id).all()
        loans = Loan.query.filter_by(chama_id=chama_id, user_id=m.user_id).all()
        total_contrib = sum(c.amount for c in contribs)
        total_loaned = sum(l.amount for l in loans if l.status in ['active', 'repaid', 'approved'])
        total_repaid = sum(l.amount_paid for l in loans)
        
        statements.append({
            'member': m,
            'total_contrib': total_contrib,
            'total_loaned': total_loaned,
            'total_repaid': total_repaid,
            'outstanding': total_loaned - total_repaid,
            'savings': m.total_savings
        })
    
    group_balance = calculate_group_balance(chama_id)
    total_contributions = db.session.query(db.func.sum(Contribution.amount)).filter_by(chama_id=chama_id).scalar() or 0
    
    return render_template('reports.html',
                           chama=chama,
                           statements=statements,
                           group_balance=group_balance,
                           total_contributions=total_contributions)

@app.route('/profile')
@login_required
def profile():
    chamas = get_user_chamas(current_user)
    return render_template('profile.html', chamas=chamas)


# ==================== M-PESA STK PUSH ====================

@app.route('/chama/<int:chama_id>/mpesa/pay', methods=['POST'])
@login_required
def mpesa_stk_push(chama_id):
    """Initiate STK Push for contribution or loan repayment"""
    from services.mpesa import MpesaService
    from services.sms import SMSService
    
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        return jsonify({'success': False, 'error': 'Not a member'}), 403
    
    chama = Chama.query.get_or_404(chama_id)
    amount = float(request.form.get('amount', 0))
    phone = request.form.get('phone', current_user.phone).strip()
    purpose = request.form.get('purpose', 'contribution')  # contribution | loan_repayment
    loan_id = request.form.get('loan_id')
    
    if amount < 1:
        flash('Invalid amount.', 'danger')
        return redirect(request.referrer or url_for('chama_detail', chama_id=chama_id))
    
    # Create pending transaction record
    ref = f"CH{chama_id}-{purpose[:4].upper()}-{current_user.id}-{datetime.now().strftime('%H%M%S')}"
    
    mpesa = MpesaService()
    result = mpesa.stk_push(
        phone=phone,
        amount=amount,
        account_reference=ref,
        transaction_desc=f'{chama.name[:10]} {purpose}'
    )
    
    if result.get('success'):
        txn = MpesaTransaction(
            chama_id=chama_id,
            user_id=current_user.id,
            amount=amount,
            phone=phone,
            purpose=purpose,
            reference=ref,
            checkout_request_id=result.get('CheckoutRequestID'),
            merchant_request_id=result.get('MerchantRequestID'),
            status='pending',
            loan_id=int(loan_id) if loan_id else None
        )
        db.session.add(txn)
        db.session.commit()
        
        # Notify user
        sms = SMSService()
        sms.notify_stk_sent(phone, amount, purpose.replace('_', ' ').title())
        
        if result.get('simulated'):
            flash(f'M-Pesa STK Push SIMULATED for KES {amount:,.0f}. In live mode the phone would ring. Check console for details.', 'info')
            # Auto-complete simulation after a short delay is handled by a separate endpoint
        else:
            flash(f'M-Pesa prompt sent to {phone}. Please enter your PIN on your phone.', 'success')
    else:
        flash(f'M-Pesa error: {result.get("error", "Unknown error")}', 'danger')
    
    return redirect(request.referrer or url_for('chama_detail', chama_id=chama_id))


@app.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    """Safaricom STK callback – no auth required (Safaricom calls this)"""
    from services.mpesa import MpesaService
    from services.sms import SMSService
    
    try:
        data = request.get_json(force=True)
        parsed = MpesaService.parse_callback(data)
        
        checkout_id = parsed.get('checkout_request_id')
        if not checkout_id:
            return jsonify({'ResultCode': 1, 'ResultDesc': 'Missing CheckoutRequestID'}), 400
        
        txn = MpesaTransaction.query.filter_by(checkout_request_id=checkout_id).first()
        if not txn:
            # Still acknowledge to Safaricom
            return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
        if parsed.get('success'):
            txn.status = 'completed'
            txn.mpesa_receipt = parsed.get('mpesa_receipt')
            txn.result_desc = parsed.get('result_desc')
            txn.completed_at = datetime.utcnow()
            
            # Record the actual contribution or repayment
            if txn.purpose == 'contribution':
                contrib = Contribution(
                    chama_id=txn.chama_id,
                    user_id=txn.user_id,
                    amount=txn.amount,
                    contribution_date=date.today(),
                    month=date.today().strftime('%Y-%m'),
                    payment_method='M-Pesa',
                    mpesa_code=txn.mpesa_receipt,
                    notes=f'STK Auto | Ref: {txn.reference}',
                    recorded_by=txn.user_id
                )
                db.session.add(contrib)
                
                membership = get_membership(txn.user_id, txn.chama_id)
                if membership:
                    membership.total_savings += txn.amount
                
                # SMS confirmation
                user = User.query.get(txn.user_id)
                chama = Chama.query.get(txn.chama_id)
                if user and chama:
                    sms = SMSService()
                    sms.notify_contribution_received(
                        user.phone, user.name, txn.amount, 
                        chama.name, membership.total_savings if membership else 0
                    )
            
            elif txn.purpose == 'loan_repayment' and txn.loan_id:
                loan = Loan.query.get(txn.loan_id)
                if loan:
                    remaining = loan.total_repayable - loan.amount_paid
                    pay_amount = min(txn.amount, remaining)
                    
                    repayment = LoanRepayment(
                        loan_id=loan.id,
                        amount=pay_amount,
                        payment_method='M-Pesa',
                        mpesa_code=txn.mpesa_receipt,
                        recorded_by=txn.user_id
                    )
                    db.session.add(repayment)
                    loan.amount_paid += pay_amount
                    if loan.amount_paid >= loan.total_repayable:
                        loan.status = 'repaid'
                    
                    user = User.query.get(txn.user_id)
                    chama = Chama.query.get(txn.chama_id)
                    if user and chama:
                        sms = SMSService()
                        sms.notify_loan_repayment(
                            user.phone, user.name, pay_amount,
                            loan.total_repayable - loan.amount_paid, chama.name
                        )
        else:
            txn.status = 'failed'
            txn.result_desc = parsed.get('result_desc', 'Failed')
        
        db.session.commit()
        return jsonify({'ResultCode': 0, 'ResultDesc': 'Accepted'}), 200
        
    except Exception as e:
        print(f'M-Pesa callback error: {e}')
        return jsonify({'ResultCode': 1, 'ResultDesc': str(e)}), 500


@app.route('/mpesa/simulate_complete/<int:txn_id>', methods=['POST'])
@login_required
def mpesa_simulate_complete(txn_id):
    """For demo: manually complete a simulated STK transaction"""
    from services.sms import SMSService
    
    txn = MpesaTransaction.query.get_or_404(txn_id)
    if txn.user_id != current_user.id and not is_treasurer_or_chair(current_user, txn.chama_id):
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    if txn.status != 'pending':
        flash('Transaction already processed.', 'warning')
        return redirect(request.referrer or url_for('dashboard'))
    
    txn.status = 'completed'
    txn.mpesa_receipt = f'SIM{datetime.now().strftime("%H%M%S")}{txn.id}'
    txn.result_desc = 'Simulated successful payment'
    txn.completed_at = datetime.utcnow()
    
    if txn.purpose == 'contribution':
        contrib = Contribution(
            chama_id=txn.chama_id,
            user_id=txn.user_id,
            amount=txn.amount,
            contribution_date=date.today(),
            month=date.today().strftime('%Y-%m'),
            payment_method='M-Pesa',
            mpesa_code=txn.mpesa_receipt,
            notes='Simulated STK',
            recorded_by=current_user.id
        )
        db.session.add(contrib)
        membership = get_membership(txn.user_id, txn.chama_id)
        if membership:
            membership.total_savings += txn.amount
        
        user = User.query.get(txn.user_id)
        chama = Chama.query.get(txn.chama_id)
        if user and chama and membership:
            sms = SMSService()
            sms.notify_contribution_received(
                user.phone, user.name, txn.amount, chama.name, membership.total_savings
            )
    
    db.session.commit()
    flash(f'Simulated payment of KES {txn.amount:,.0f} completed! Receipt: {txn.mpesa_receipt}', 'success')
    return redirect(request.referrer or url_for('chama_detail', chama_id=txn.chama_id))


@app.route('/chama/<int:chama_id>/mpesa/transactions')
@login_required
def mpesa_transactions(chama_id):
    membership = get_membership(current_user.id, chama_id)
    if not membership:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    chama = Chama.query.get_or_404(chama_id)
    is_admin = is_treasurer_or_chair(current_user, chama_id)
    
    if is_admin:
        txns = MpesaTransaction.query.filter_by(chama_id=chama_id).order_by(MpesaTransaction.created_at.desc()).limit(50).all()
    else:
        txns = MpesaTransaction.query.filter_by(chama_id=chama_id, user_id=current_user.id).order_by(MpesaTransaction.created_at.desc()).limit(50).all()
    
    return render_template('mpesa_transactions.html', chama=chama, txns=txns, is_admin=is_admin)


# ==================== INIT DB & SEED ====================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Seed only if empty
        if User.query.count() == 0:
            # Create demo users
            admin = User(name='Jane Wanjiku', phone='0712345678', role='chairperson')
            admin.set_password('password123')
            
            treasurer = User(name='John Kamau', phone='0723456789', role='treasurer')
            treasurer.set_password('password123')
            
            member1 = User(name='Mary Akinyi', phone='0734567890')
            member1.set_password('password123')
            
            member2 = User(name='Peter Ochieng', phone='0745678901')
            member2.set_password('password123')
            
            member3 = User(name='Grace Njeri', phone='0756789012')
            member3.set_password('password123')
            
            db.session.add_all([admin, treasurer, member1, member2, member3])
            db.session.flush()
            
            # Create demo Chama
            chama = Chama(
                name='Umoja Women Chama',
                description='A savings and investment group for women in Nairobi. We meet every first Saturday of the month.',
                contribution_amount=2000,
                contribution_day=5,
                loan_interest_rate=5.0,
                max_loan_multiplier=3.0
            )
            db.session.add(chama)
            db.session.flush()
            
            # Memberships
            db.session.add(Membership(user_id=admin.id, chama_id=chama.id, role_in_chama='chairperson', total_savings=12000))
            db.session.add(Membership(user_id=treasurer.id, chama_id=chama.id, role_in_chama='treasurer', total_savings=10000))
            db.session.add(Membership(user_id=member1.id, chama_id=chama.id, role_in_chama='member', total_savings=8000))
            db.session.add(Membership(user_id=member2.id, chama_id=chama.id, role_in_chama='member', total_savings=6000))
            db.session.add(Membership(user_id=member3.id, chama_id=chama.id, role_in_chama='secretary', total_savings=10000))
            
            # Sample contributions
            today = date.today()
            for i, uid in enumerate([admin.id, treasurer.id, member1.id, member2.id, member3.id]):
                for month_offset in range(6):
                    d = today - relativedelta(months=month_offset)
                    contrib = Contribution(
                        chama_id=chama.id,
                        user_id=uid,
                        amount=2000,
                        contribution_date=d.replace(day=5),
                        month=d.strftime('%Y-%m'),
                        payment_method='M-Pesa' if i % 2 == 0 else 'Cash',
                        mpesa_code=f'QK{100000 + i*10 + month_offset}' if i % 2 == 0 else None,
                        recorded_by=treasurer.id
                    )
                    db.session.add(contrib)
            
            # Sample loan
            loan = Loan(
                chama_id=chama.id,
                user_id=member1.id,
                amount=15000,
                interest_rate=5.0,
                total_repayable=15750,
                amount_paid=5000,
                purpose='School fees',
                status='active',
                application_date=datetime.utcnow() - timedelta(days=30),
                approval_date=datetime.utcnow() - timedelta(days=28),
                due_date=today + relativedelta(months=2),
                approved_by=admin.id
            )
            db.session.add(loan)
            db.session.flush()
            
            db.session.add(LoanRepayment(
                loan_id=loan.id,
                amount=5000,
                payment_date=today - timedelta(days=10),
                payment_method='M-Pesa',
                mpesa_code='QL987654',
                recorded_by=treasurer.id
            ))
            
            # Merry Go Round
            mgr = MerryGoRound(
                chama_id=chama.id,
                name='Umoja MGR 2026',
                contribution_per_member=1000,
                frequency='monthly'
            )
            db.session.add(mgr)
            db.session.flush()
            
            members_list = [admin, treasurer, member1, member2, member3]
            for i, u in enumerate(members_list):
                rnd = MGRRound(
                    mgr_id=mgr.id,
                    round_number=i + 1,
                    recipient_id=u.id,
                    scheduled_date=today + relativedelta(months=i),
                    amount=5000,
                    status='paid' if i == 0 else 'upcoming',
                    paid_date=today if i == 0 else None
                )
                db.session.add(rnd)
            
            # Meeting
            meeting = Meeting(
                chama_id=chama.id,
                title='Monthly General Meeting - October',
                meeting_date=datetime.now() + timedelta(days=10),
                location='Community Hall, Eastlands',
                agenda='1. Review of contributions\n2. Loan applications\n3. Merry Go Round update\n4. AOB',
                created_by=admin.id
            )
            db.session.add(meeting)
            
            db.session.commit()
            print("✅ Database initialized with demo data!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
