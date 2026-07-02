from flask import render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Student, Course, Enrollment, Attendance
from datetime import datetime

def register_routes(app):
    
    @app.route('/')
    def index():
        if 'user_id' in session:
            if session.get('role') == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_profile'))
        return redirect(url_for('login_selection'))

    @app.route('/login')
    def login_selection():
        return render_template('login.html')

    @app.route('/login/admin', methods=['POST'])
    def login_admin():
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role='admin').first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('admin_dashboard'))
        flash('Invalid admin credentials', 'error')
        return redirect(url_for('login_selection'))

    @app.route('/login/student', methods=['POST'])
    def login_student():
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, role='student').first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('student_profile'))
        flash('Invalid student credentials', 'error')
        return redirect(url_for('login_selection'))

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login_selection'))

    # --- ADMIN ROUTES ---
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if session.get('role') != 'admin':
            return redirect(url_for('login_selection'))
        
        student_count = Student.query.count()
        course_count = Course.query.count()
        return render_template('admin/dashboard.html', student_count=student_count, course_count=course_count)

    @app.route('/admin/students', methods=['GET', 'POST'])
    def manage_students():
        if session.get('role') != 'admin':
            return redirect(url_for('login_selection'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
            elif Student.query.filter_by(email=email).first():
                flash('Email already exists', 'error')
            else:
                user = User(username=username, role='student')
                user.set_password(password)
                db.session.add(user)
                db.session.commit() # Commit to get user.id
                
                student = Student(user_id=user.id, first_name=first_name, last_name=last_name, email=email)
                db.session.add(student)
                db.session.commit()
                flash('Student added successfully', 'success')
                return redirect(url_for('manage_students'))
                
        students = Student.query.all()
        return render_template('admin/students.html', students=students)

    @app.route('/admin/courses', methods=['GET', 'POST'])
    def manage_courses():
        if session.get('role') != 'admin':
            return redirect(url_for('login_selection'))
            
        if request.method == 'POST':
            course_code = request.form.get('course_code')
            course_name = request.form.get('course_name')
            credits = request.form.get('credits')
            
            if Course.query.filter_by(course_code=course_code).first():
                flash('Course code already exists', 'error')
            else:
                course = Course(course_code=course_code, course_name=course_name, credits=int(credits))
                db.session.add(course)
                db.session.commit()
                flash('Course added successfully', 'success')
                return redirect(url_for('manage_courses'))
                
        courses = Course.query.all()
        return render_template('admin/courses.html', courses=courses)
        
    @app.route('/admin/enroll', methods=['POST'])
    def enroll_student():
        if session.get('role') != 'admin':
            return redirect(url_for('login_selection'))
            
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        
        if not Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first():
            enrollment = Enrollment(student_id=student_id, course_id=course_id)
            db.session.add(enrollment)
            db.session.commit()
            flash('Student enrolled successfully', 'success')
        else:
            flash('Student is already enrolled in this course', 'error')
            
        return redirect(url_for('manage_students'))

    @app.route('/admin/attendance', methods=['GET', 'POST'])
    def manage_attendance():
        if session.get('role') != 'admin':
            return redirect(url_for('login_selection'))
            
        courses = Course.query.all()
        selected_course = None
        enrollments = []
        
        course_id = request.args.get('course_id') or request.form.get('course_id')
        date_str = request.args.get('date') or request.form.get('date')
        
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
        if course_id:
            selected_course = Course.query.get(course_id)
            if selected_course:
                enrollments = Enrollment.query.filter_by(course_id=course_id).all()
                
        if request.method == 'POST' and selected_course:
            # Save attendance
            for enrollment in enrollments:
                status = request.form.get(f'status_{enrollment.student_id}')
                if status:
                    # Check if record exists
                    record = Attendance.query.filter_by(
                        student_id=enrollment.student_id, 
                        course_id=course_id, 
                        date=selected_date
                    ).first()
                    
                    if record:
                        record.status = status
                    else:
                        new_record = Attendance(
                            student_id=enrollment.student_id,
                            course_id=course_id,
                            date=selected_date,
                            status=status
                        )
                        db.session.add(new_record)
            db.session.commit()
            flash('Attendance saved successfully', 'success')
            return redirect(url_for('manage_attendance', course_id=course_id, date=date_str))
            
        # Get existing records for template rendering
        existing_records = {}
        if selected_course:
            records = Attendance.query.filter_by(course_id=course_id, date=selected_date).all()
            for r in records:
                existing_records[r.student_id] = r.status
                
        return render_template('admin/attendance.html', 
                               courses=courses, 
                               selected_course=selected_course, 
                               enrollments=enrollments,
                               selected_date=date_str,
                               existing_records=existing_records)

    # --- STUDENT ROUTES ---
    @app.route('/student/profile')
    def student_profile():
        if session.get('role') != 'student':
            return redirect(url_for('login_selection'))
            
        student = Student.query.filter_by(user_id=session['user_id']).first()
        if not student:
            return "Student profile not found", 404
            
        return render_template('student/profile.html', student=student)
