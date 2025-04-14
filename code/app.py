from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, login_user, current_user, login_required, UserMixin


app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_master.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader #to load the current user
def load_user(user_id):
    return db.session.get(User, int(user_id))


#Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    scores = db.relationship('Score', backref='user', cascade="all, delete-orphan")

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    chapters = db.relationship('Chapter', back_populates="subject", lazy=True, cascade="all, delete-orphan")

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    subject = db.relationship('Subject', back_populates="chapters")
    quizzes = db.relationship('Quiz', backref='chapter', cascade="all, delete-orphan")

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id', ondelete='CASCADE'), nullable=False)
    date_of_quiz = db.Column(db.DateTime, nullable = False)
    time_duration = db.Column(db.Integer, nullable = False)
    total_questions = db.Column(db.Integer, default = 0, nullable = False)
    questions = db.relationship('Question', backref='quiz', lazy=True)

    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    scores = db.relationship('Score', backref='quiz', lazy=True, cascade="all, delete-orphan")
    

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.String(255), nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    total_scored = db.Column(db.Integer, nullable = False)

def create_admin():

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@quizmaster.com').first():
            admin = User(
                full_name='Admin', 
                email='admin@quizmaster.com', 
                password='admin@123',  
                qualification='N/A', 
                dob=datetime(2000, 1, 1), 
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password:  
            login_user(user)
            
            
            if user.role == 'admin':  
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))


    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        qualification = request.form['qualification']
        dob = request.form['dob']

        user = User(full_name=full_name, email=email, password=password, qualification=qualification, dob=datetime.strptime(dob, '%Y-%m-%d'))

        try:
            db.session.add(user)
            db.session.commit()

        except :
            flash('User mail already registered')
            return redirect(url_for('login'))

        flash('New user registered!')
        return redirect(url_for('login'))
    
    return render_template('register.html')

from flask_login import login_required, current_user

@app.route('/admin/dashboard')
@login_required

def admin_dashboard():

    if not current_user.is_authenticated or current_user.role != 'admin':
        return redirect(url_for('login'))

    subjects = Subject.query.all()

    return render_template('admin_dashboard.html', subjects=subjects)


@app.route('/admin/scores', methods=['GET'])
@login_required

def admin_scores():
    
    search_query = request.args.get('search', '')

    if search_query:
        users = User.query.filter(
            (User.full_name.ilike(f"%{search_query}%")) |
            (User.email.ilike(f"%{search_query}%"))
        ).all()
    else:
        users = User.query.all()  
    return render_template('admin_scores.html', users=users)

@app.route('/admin/users', methods=['GET'])
@login_required

def admin_users():
    search_query = request.args.get('search', '')

    if search_query:
        users = User.query.filter(
            (User.full_name.ilike(f"%{search_query}%")) |
            (User.email.ilike(f"%{search_query}%"))
        ).all()
    else:
        users = User.query.all()

    return render_template('admin_users.html', users=users)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required

def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.role = request.form['role']
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))

    return render_template('edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required

def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'danger')
    return redirect(url_for('admin_users'))


@app.route('/admin/add_subject', methods=['GET', 'POST'])
@login_required

def add_subject():
     #to allow the admin only
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if name and description:
            new_subject = Subject(name=name, description=description)
            db.session.add(new_subject)
            db.session.commit()
            flash('New subject added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Please fill all fields.', 'danger')

    return render_template('admin_add_subject.html')

@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required

def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        subject.name = request.form['name']
        subject.description = request.form['description']
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_subject.html', subject=subject)

@app.route('/delete_subject/<int:subject_id>', methods=['GET'])
@login_required

def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/add_chapter/<int:subject_id>', methods=['POST'])
@login_required

def add_chapter(subject_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    name = request.form['name']
    description = request.form['description']

    if name and description:
        new_chapter = Chapter(name=name, description=description, subject_id=subject_id)
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter added successfully!', 'success')
    else:
        flash('Please fill all fields.', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
@login_required

def edit_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    if request.method == 'POST':
        chapter.name = request.form['name']
        chapter.description = request.form['description']
        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_chapter.html', chapter=chapter)

@app.route('/delete_chapter/<int:chapter_id>', methods=['GET'])
@login_required

def delete_chapter(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'danger')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/quizzes')
@login_required

def admin_quizzes():
    quizzes = Quiz.query.options(db.joinedload(Quiz.questions)).all()  #loading quizzes with questions
    return render_template('admin_quiz.html', quizzes=quizzes)


@app.route('/admin/add_quiz', methods=['GET', 'POST'])
@login_required

def add_quiz():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':

        chapter_id = request.form['chapter_id']
        date_of_quiz = request.form['date_of_quiz']
        duration = request.form['duration']
        

        if date_of_quiz:
            date_of_quiz = date_of_quiz.replace("T", " ")  
            date_of_quiz = datetime.strptime(date_of_quiz, "%Y-%m-%d %H:%M")  

        new_quiz = Quiz(chapter_id=chapter_id, date_of_quiz=date_of_quiz, time_duration=duration)

        db.session.add(new_quiz)
        db.session.commit()
        
        flash('Quiz created successfully!', 'success')

        return redirect(url_for('admin_quizzes'))  

    chapters = Chapter.query.all()

    return render_template('admin_add_quiz.html', chapters=chapters)

@app.route('/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required

def delete_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Delete all related questions first
    Question.query.filter_by(quiz_id=quiz_id).delete()
    
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz and all related questions deleted successfully!', 'success')
    
    return redirect(url_for('admin_quizzes'))


@app.route('/admin/add_questions/<int:quiz_id>', methods=['GET', 'POST'])
@login_required

def add_questions(quiz_id):

    if not current_user.is_authenticated or current_user.role != 'admin':

        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        question_text = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']
        action = request.form.get('action')  #to get the button clicked

        new_question = Question(
            quiz_id=quiz_id, 
            question_statement=question_text, 
            option1=option1, 
            option2=option2, 
            option3=option3, 
            option4=option4, 
            correct_option=int(correct_option)
        )
        db.session.add(new_question)

        quiz.total_questions += 1  
        db.session.commit()

        flash('Question added successfully!', 'success')

        if action == "save_exit":
            return redirect(url_for('admin_quizzes'))  

        return redirect(url_for('add_questions', quiz_id=quiz_id))  
    
    return render_template('admin_add_questions.html', quiz=quiz)

@app.route('/admin/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id  
    
    if request.method == 'POST':
        question.question_statement = request.form['question']  
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.option4 = request.form['option4']
        question.correct_option = int(request.form['correct_option'])

        db.session.commit()  

        flash('Question updated successfully!', 'success')
        return redirect(url_for('admin_quizzes', quiz_id=quiz_id))  

    return render_template('edit_question.html', question=question)




@app.route('/admin/delete_question/<int:quiz_id>/<int:question_id>', methods=['POST'])
@login_required
def delete_question(quiz_id, question_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    question = Question.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(quiz_id)

    db.session.delete(question)

    
    if quiz.total_questions > 0:
        quiz.total_questions -= 1

    db.session.commit()

    flash('Question deleted successfully!', 'success')
    return redirect(url_for('admin_quizzes', quiz_id=quiz_id))



@app.route('/user/dashboard')
@login_required

def user_dashboard():
    quizzes = Quiz.query.all()
    return render_template('user_dashboard.html', quizzes=quizzes, current_user=current_user)


@app.route('/logout')

def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/user/scores', methods=['GET'])
@login_required

def user_scores():
    scores = Score.query.filter_by(user_id=current_user.id).all()
    return render_template('user_scores.html', scores=scores)

@app.route('/quiz/start/<int:quiz_id>', methods=['GET'])
@login_required

def start_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()

    return render_template('quiz_attempt.html', quiz=quiz, questions=questions)


@app.route('/quiz/submit/<int:quiz_id>', methods=['POST'])
@login_required  

def submit_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz.id).all()

    score = 0
    for question in questions:
        selected_answer = request.form.get(f'question_{question.id}')
        if selected_answer and int(selected_answer) == question.correct_option:
            score += 1  

    user_id = current_user.id

    new_score = Score(
        user_id=user_id, 
        quiz_id=quiz.id,
        total_scored=score
    )

    db.session.add(new_score)

    db.session.commit()

    flash('Quiz submitted successfully!', 'success')
    return redirect(url_for('user_scores'))



if __name__ == '__main__':
    create_admin()
    app.run(debug=True)
