from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pymysql
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import hashlib
import secrets
from flask_wtf.csrf import CSRFProtect
from contextlib import contextmanager
import random
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # 请更改为一个安全的密钥
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mby123456@localhost/zhihu'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 初始化限速器
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# 初始化安全头
Talisman(app,
    force_https=False,  # 开发环境设为False，生产环境设为True
    strict_transport_security=True,
    session_cookie_secure=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval' cdn.bootcdn.net",
        'style-src': "'self' 'unsafe-inline' cdn.bootcdn.net",
        'img-src': "'self' data:",
        'font-src': "'self' cdn.bootcdn.net"
    }
)

# 话题模型
class Topic(db.Model):
    __tablename__ = 'Topic'
    TopicID = db.Column(db.Integer, primary_key=True)
    TopicName = db.Column(db.String(255), unique=True, nullable=False)
    # 明确定义Topic到Question的one-to-many关系
    questions = db.relationship('Question', back_populates='topic', lazy=True, cascade='all, delete-orphan')

# 问题模型
class Question(db.Model):
    __tablename__ = 'Question'
    QuestionID = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(255), nullable=False)
    Content = db.Column(db.Text, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    CreateTime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    TopicID = db.Column(db.Integer, db.ForeignKey('Topic.TopicID'), nullable=False)
    AnswerCount = db.Column(db.Integer, nullable=False, default=0)
    # 明确定义Question到Answer的one-to-many关系
    answers = db.relationship('Answer', back_populates='question', lazy=True, cascade='all, delete-orphan')
    # 明确定义Question到User的many-to-one关系
    user = db.relationship('User', back_populates='questions')
    # 明确定义Question到Topic的many-to-one关系
    topic = db.relationship('Topic', back_populates='questions')

# 回答模型
class Answer(db.Model):
    __tablename__ = 'Answer'
    AnswerID = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.Text, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    QuestionID = db.Column(db.Integer, db.ForeignKey('Question.QuestionID'), nullable=False)
    AnswerTime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    UpvoteCount = db.Column(db.Integer, nullable=False, default=0)
    # 明确定义Answer到User的many-to-one关系
    user = db.relationship('User', back_populates='answers')
    # 明确定义Answer到Question的many-to-one关系
    question = db.relationship('Question', back_populates='answers')
    # 明确定义Answer到Comment的one-to-many关系
    comments = db.relationship('Comment', back_populates='answer', lazy=True, cascade='all, delete-orphan')
    # 明确定义Answer到Upvote的one-to-many关系
    upvotes = db.relationship('Upvote', back_populates='answer', lazy=True, cascade='all, delete-orphan')

# 评论模型
class Comment(db.Model):
    __tablename__ = 'Comment'
    CommentID = db.Column(db.Integer, primary_key=True)
    Content = db.Column(db.Text, nullable=False)
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), nullable=False)
    AnswerID = db.Column(db.Integer, db.ForeignKey('Answer.AnswerID'), nullable=False)
    CommentTime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # 明确定义Comment到User的many-to-one关系
    user = db.relationship('User', back_populates='comments')
    # 明确定义Comment到Answer的many-to-one关系
    answer = db.relationship('Answer', back_populates='comments')

# 新增Upvote模型
class Upvote(db.Model):
    __tablename__ = 'Upvote'
    UserID = db.Column(db.Integer, db.ForeignKey('User.UserID'), primary_key=True)
    AnswerID = db.Column(db.Integer, db.ForeignKey('Answer.AnswerID'), primary_key=True)
    UpvoteTime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # 明确定义Upvote到User的many-to-one关系
    user = db.relationship('User', back_populates='upvotes')
    # 明确定义Upvote到Answer的many-to-one关系
    answer = db.relationship('Answer', back_populates='upvotes')

# 用户模型
class User(UserMixin, db.Model):
    __tablename__ = 'User'
    UserID = db.Column(db.Integer, primary_key=True)
    Username = db.Column(db.String(50), unique=True, nullable=False)
    Email = db.Column(db.String(255), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    RegistrationTime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    Profile = db.Column(db.Text)
    Avatar = db.Column(db.String(255))
    Gender = db.Column(db.Integer, nullable=False)
    QuestionCount = db.Column(db.Integer, nullable=False, default=0)
    AnswerCount = db.Column(db.Integer, nullable=False, default=0)
    CommentCount = db.Column(db.Integer, nullable=False, default=0)
    TotalUpvotes = db.Column(db.Integer, nullable=False, default=0)
    # 明确定义User到Question的one-to-many关系
    questions = db.relationship('Question', back_populates='user', lazy=True, cascade='all, delete-orphan')
    # 明确定义User到Answer的one-to-many关系
    answers = db.relationship('Answer', back_populates='user', lazy=True, cascade='all, delete-orphan')
    # 明确定义User到Comment的one-to-many关系
    comments = db.relationship('Comment', back_populates='user', lazy=True, cascade='all, delete-orphan')
    # 明确定义User到Upvote的one-to-many关系
    upvotes = db.relationship('Upvote', back_populates='user', lazy=True, cascade='all, delete-orphan')

    def get_id(self):
        return str(self.UserID)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 密码加密函数
def hash_password(password):
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

# 验证密码函数
def verify_password(stored_password, provided_password):
    try:
        # 尝试解析新格式的密码（salt$hash）
        salt, hash_value = stored_password.split('$')
        hash_obj = hashlib.sha256((provided_password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except ValueError:
        # 如果是旧格式的密码，直接比较
        return stored_password == provided_password

# 问题相关路由
@app.route('/question/new', methods=['GET', 'POST'])
@login_required
def new_question():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        topic_id = request.form.get('topic_id')
        
        if not all([title, content, topic_id]):
            flash('请填写所有必填字段')
            return redirect(url_for('new_question'))
            
        question = Question(
            Title=title,
            Content=content,
            UserID=current_user.UserID,
            TopicID=topic_id
        )
        
        db.session.add(question)
        db.session.commit()
        flash('问题发布成功')
        return redirect(url_for('question_detail', question_id=question.QuestionID))
        
    topics = Topic.query.all()
    return render_template('new_question.html', topics=topics)

@app.route('/question/<int:question_id>')
def question_detail(question_id):
    question = Question.query.get_or_404(question_id)
    return render_template('question_detail.html', question=question)

@app.route('/question/<int:question_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    if question.UserID != current_user.UserID:
        flash('您没有权限编辑此问题')
        return redirect(url_for('question_detail', question_id=question_id))
        
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        topic_id = request.form.get('topic_id')
        
        if not all([title, content, topic_id]):
            flash('请填写所有必填字段')
            return redirect(url_for('edit_question', question_id=question_id))
            
        question.Title = title
        question.Content = content
        question.TopicID = topic_id
        
        db.session.commit()
        flash('问题更新成功')
        return redirect(url_for('question_detail', question_id=question_id))
        
    topics = Topic.query.all()
    return render_template('edit_question.html', question=question, topics=topics)

@app.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    if question.UserID != current_user.UserID:
        flash('您没有权限删除此问题')
        return redirect(url_for('question_detail', question_id=question_id))
        
    db.session.delete(question)
    db.session.commit()
    flash('问题已删除')
    return redirect(url_for('index'))

# 回答相关路由
@app.route('/question/<int:question_id>/answer', methods=['POST'])
@login_required
@limiter.limit("20 per hour")  # 限制回答频率
def add_answer(question_id):
    question = Question.query.get_or_404(question_id)
    content = request.form.get('content')
    
    if not content:
        flash('回答内容不能为空')
        return redirect(url_for('question_detail', question_id=question_id))
        
    with transaction():
        answer = Answer(
            Content=content,
            UserID=current_user.UserID,
            QuestionID=question_id
        )
        db.session.add(answer)
        update_question_answer_count(question_id)
        update_user_stats(current_user.UserID)
    
    flash('回答发布成功')
    return redirect(url_for('question_detail', question_id=question_id))

# 评论相关路由
@app.route('/answer/<int:answer_id>/comment', methods=['POST'])
@login_required
def add_comment(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    content = request.form.get('content')
    
    if not content:
        flash('评论内容不能为空')
        return redirect(url_for('question_detail', question_id=answer.QuestionID))
        
    comment = Comment(
        Content=content,
        UserID=current_user.UserID,
        AnswerID=answer_id
    )
    
    db.session.add(comment)
    db.session.commit()
    flash('评论发布成功')
    return redirect(url_for('question_detail', question_id=answer.QuestionID))

# 点赞路由
@app.route('/answer/<int:answer_id>/upvote', methods=['POST'])
@login_required
def upvote_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    
    # 检查用户是否已经点赞过这个回答
    existing_upvote = Upvote.query.filter_by(UserID=current_user.UserID, AnswerID=answer_id).first()
    
    if existing_upvote:
        flash('您已经点赞过这个回答了！', 'warning')
    else:
        try:
            # 创建新的点赞记录
            new_upvote = Upvote(UserID=current_user.UserID, AnswerID=answer_id)
            db.session.add(new_upvote)
            
            # 增加回答的点赞数
            answer.UpvoteCount += 1
            db.session.commit()
            flash('点赞成功！', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'点赞失败: {str(e)}', 'error')

    return redirect(url_for('question_detail', question_id=answer.QuestionID))

# 删除回答路由
@app.route('/answer/<int:answer_id>/delete', methods=['POST'])
@login_required
def delete_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)

    # 检查当前用户是否有权限删除此回答
    if current_user.UserID != answer.UserID:
        flash('您没有权限删除此回答')
        return redirect(url_for('question_detail', question_id=answer.QuestionID))

    with transaction(): # 使用事务确保操作原子性
        db.session.delete(answer)
        # 触发器会自动更新相关统计数据
        db.session.commit()

    flash('回答已删除')
    return redirect(url_for('question_detail', question_id=answer.QuestionID))

# 原有的路由保持不变
@app.route('/')
def index():
    questions = Question.query.order_by(Question.CreateTime.desc()).all()
    # 获取热门问题数据
    hot_questions_cursor = db.session.execute(text('CALL GetHotQuestions(10)')) # 调用存储过程，获取10个热门问题
    hot_questions = hot_questions_cursor.fetchall()
    hot_questions_cursor.close() # 关闭cursor

    return render_template('index.html', questions=questions, hot_questions=hot_questions)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # 限制登录频率
def login():
    # 简单的算术验证码
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operator = random.choice(['+', '-'])
    if operator == '+':
        correct_answer = num1 + num2
        question = f'{num1} + {num2} = ?'
    else:
        # 确保结果不是负数
        if num1 < num2:
            num1, num2 = num2, num1
        correct_answer = num1 - num2
        question = f'{num1} - {num2} = ?'

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_answer = request.form.get('captcha')
        stored_answer = session.pop('captcha_answer', None)

        # 验证算术题答案
        if stored_answer is None or not user_answer or int(user_answer) != stored_answer:
            flash('算术题答案错误')
            return redirect(url_for('login'))

        user = User.query.filter_by(Username=username).first()

        if user and verify_password(user.Password, password):
            login_user(user)
            return redirect(url_for('index'))

        flash('用户名或密码错误')
        
    session['captcha_answer'] = correct_answer
    return render_template('login.html', captcha_question=question)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # 限制注册频率
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(Username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
            
        if User.query.filter_by(Email=email).first():
            flash('邮箱已被注册')
            return redirect(url_for('register'))
            
        new_user = User(
            Username=username,
            Email=email,
            Password=hash_password(password),  # 使用加密后的密码
            Gender=0
        )
        
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# 用户个人主页路由
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    questions = Question.query.filter_by(UserID=user_id).order_by(Question.CreateTime.desc()).all()
    answers = Answer.query.filter_by(UserID=user_id).order_by(Answer.AnswerTime.desc()).all()
    
    # 计算统计数据
    stats = {
        'questions_count': len(questions),
        'answers_count': len(answers),
        'comments_count': len(user.comments),
        'total_upvotes': sum(answer.UpvoteCount for answer in answers)
    }
    
    return render_template('user_profile.html', user=user, questions=questions, answers=answers, stats=stats)

@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    if current_user.UserID != user_id:
        flash('您没有权限编辑其他用户的资料', 'danger')
        return redirect(url_for('user_profile', user_id=user_id))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        profile = request.form.get('profile')
        gender = request.form.get('gender')

        # 检查昵称是否更改且是否唯一
        if new_username and new_username != user.Username:
            existing_user = User.query.filter_by(Username=new_username).first()
            if existing_user:
                flash('该昵称已被使用，请选择其他昵称', 'warning')
                return render_template('edit_profile.html', user=user) # 返回编辑页面并显示警告
            user.Username = new_username
        
        user.Profile = profile
        user.Gender = int(gender)
        
        db.session.commit()
        flash('个人资料更新成功', 'success')
        return redirect(url_for('user_profile', user_id=user_id))
        
    return render_template('edit_profile.html', user=user)

# 注销用户（删除账号）路由
@app.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # 确保当前用户只能注销自己的账号
    if current_user.UserID != user.UserID:
        flash('您没有权限注销此账号')
        return redirect(url_for('user_profile', user_id=current_user.UserID))

    # 先登出用户
    logout_user()

    with transaction(): # 使用事务确保操作原子性
        # 不再删除用户记录，而是更新信息标记为已注销
        user.Username = f'账号已注销_{user.UserID}' # 添加用户ID确保用户名唯一
        # 修改邮箱，使其不为NULL且唯一
        user.Email = f'deleted_{user.UserID}_{int(datetime.utcnow().timestamp())}@example.com' # 使用用户ID和时间戳保证唯一性
        user.Password = 'invalid_password_hash' # 设置为无效密码或清空
        # 可选：user.Profile = '' # 清空个人简介
        # 如果User模型有is_deleted字段，可以在这里设置 user.is_deleted = True
        db.session.add(user) # 更新用户记录
        db.session.commit()

    flash('您的账号已成功注销')
    return redirect(url_for('index')) # 通常重定向到首页或登录页

# 话题管理相关路由
@app.route('/topics')
def topic_list():
    topics = Topic.query.all()
    return render_template('topic_list.html', topics=topics)

@app.route('/topic/<int:topic_id>')
def topic_detail(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    questions = Question.query.filter_by(TopicID=topic_id).order_by(Question.CreateTime.desc()).all()
    return render_template('topic_detail.html', topic=topic, questions=questions)

@app.route('/topic/new', methods=['GET', 'POST'])
@login_required
def new_topic():
    if request.method == 'POST':
        topic_name = request.form.get('topic_name')
        
        if not topic_name:
            flash('话题名称不能为空')
            return redirect(url_for('new_topic'))
            
        if Topic.query.filter_by(TopicName=topic_name).first():
            flash('该话题已存在')
            return redirect(url_for('new_topic'))
            
        topic = Topic(TopicName=topic_name)
        db.session.add(topic)
        db.session.commit()
        
        flash('话题创建成功')
        return redirect(url_for('topic_detail', topic_id=topic.TopicID))
        
    return render_template('new_topic.html')

@app.route('/topic/<int:topic_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    
    if request.method == 'POST':
        topic_name = request.form.get('topic_name')
        
        if not topic_name:
            flash('话题名称不能为空')
            return redirect(url_for('edit_topic', topic_id=topic_id))
            
        existing_topic = Topic.query.filter_by(TopicName=topic_name).first()
        if existing_topic and existing_topic.TopicID != topic_id:
            flash('该话题名称已存在')
            return redirect(url_for('edit_topic', topic_id=topic_id))
            
        topic.TopicName = topic_name
        db.session.commit()
        
        flash('话题更新成功')
        return redirect(url_for('topic_detail', topic_id=topic_id))
        
    return render_template('edit_topic.html', topic=topic)

@app.route('/topic/<int:topic_id>/delete', methods=['POST'])
@login_required
def delete_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    
    # 检查是否有关联的问题
    if topic.questions:
        flash('无法删除该话题，因为存在关联的问题')
        return redirect(url_for('topic_detail', topic_id=topic_id))
        
    db.session.delete(topic)
    db.session.commit()
    
    flash('话题已删除')
    return redirect(url_for('topic_list'))

# 搜索相关路由
@app.route('/search')
def search():
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'question')  # 默认为问题搜索
    
    if not query:
        return redirect(url_for('index'))
        
    if search_type == 'question':
        # 搜索问题（标题和内容）
        questions = Question.query.filter(
            db.or_(
                Question.Title.like(f'%{query}%'),
                Question.Content.like(f'%{query}%')
            )
        ).order_by(Question.CreateTime.desc()).all()
        return render_template('search_results.html', 
                             query=query, 
                             search_type=search_type,
                             questions=questions)
    else:
        # 搜索话题
        topics = Topic.query.filter(
            Topic.TopicName.like(f'%{query}%')
        ).all()
        return render_template('search_results.html', 
                             query=query, 
                             search_type=search_type,
                             topics=topics)

# 添加调用存储过程的方法
def get_hot_questions(limit=10):
    result = db.session.execute(text('CALL GetHotQuestions(:limit)'), {'limit': limit})
    return result.fetchall()

# 更新问题回答数
def update_question_answer_count(question_id):
    db.session.execute(text('CALL UpdateQuestionAnswerCount(:question_id)'), {'question_id': question_id})
    db.session.commit()

# 更新用户统计信息
def update_user_stats(user_id):
    db.session.execute(text('CALL UpdateUserStats(:user_id)'), {'user_id': user_id})
    db.session.commit()

# 更新用户密码格式
def update_user_password_format():
    print("Updating user password format...")
    with app.app_context(): # 确保在应用上下文内执行
        users = User.query.all()
        for user in users:
            if user.Password.startswith("pbkdf2:sha256"):  # 检查是否已经是新的哈希格式
                print(f"User {user.Username} already has new password format.")
                continue
            try:
                # 重新哈希密码，这里假设旧密码是明文或者某种可逆加密，
                # 如果旧密码不可逆，这一步将失败，需要用户重置密码
                user.Password = generate_password_hash(user.Password)
                db.session.add(user)
                print(f"User {user.Username} password updated.")
            except Exception as e:
                print(f"Error updating password for {user.Username}: {str(e)}")
        db.session.commit()
    print("User password format update complete.")

# 添加CSRF保护
csrf = CSRFProtect(app)

# 添加数据库事务支持
@contextmanager
def transaction():
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

# 添加存储过程调用函数
def call_stored_procedure(procedure_name, params=None):
    """调用存储过程的通用函数"""
    try:
        print(f"Attempting to call stored procedure: {procedure_name} with params: {params}")
        
        if params:
            # 生成命名参数的占位符，例如 :p0, :p1, ...
            param_names = [f"p{i}" for i in range(len(params))]
            param_placeholders = ", ".join([f":{name}" for name in param_names])
            sql_query = f'CALL {procedure_name}({param_placeholders})'
            
            # 创建一个字典来绑定命名参数
            bound_params = {param_names[i]: p for i, p in enumerate(params)}
            
            result = db.session.execute(text(sql_query), bound_params)
        else:
            sql_query = f'CALL {procedure_name}()'
            result = db.session.execute(text(sql_query))
        
        # Fetch all results from the cursor
        fetched_results = result.fetchall()
        print(f"Stored procedure {procedure_name} returned: {fetched_results}")
        
        # Close the result cursor (important for some drivers/databases)
        result.close()
        
        return fetched_results
    except Exception as e:
        print(f"Error calling stored procedure {procedure_name}: {str(e)}")
        return None

# 添加新的API路由
@app.route('/api/topic/<int:topic_id>')
def api_topic_detail(topic_id):
    topic_data = call_stored_procedure('GetTopicWithQuestionCount', [topic_id])
    if not topic_data:
        return jsonify({'error': '话题不存在'}), 404
    
    # 将结果转换为字典
    topic_dict = dict(topic_data[0])
    return jsonify(topic_dict)

@app.route('/api/user/<int:user_id>/questions')
@login_required
def api_user_questions(user_id):
    questions_data = call_stored_procedure('GetUserQuestions', [user_id])
    if not questions_data:
        return jsonify([])
    
    # 将结果转换为字典列表
    questions_list = [dict(row) for row in questions_data]
    return jsonify(questions_list)

@app.route('/api/question/<int:question_id>')
def api_question_detail(question_id):
    question_data = call_stored_procedure('GetQuestionWithAnswerCount', [question_id])
    if not question_data:
        return jsonify({'error': '问题不存在'}), 404
    
    # 将结果转换为字典
    question_dict = dict(question_data[0])
    return jsonify(question_dict)

def get_hot_topics(limit=10):
    """获取热门话题"""
    try:
        result = call_stored_procedure('GetHotTopics', [limit])
        if result:
            return result
        return []
    except Exception as e:
        print(f"Error getting hot topics: {str(e)}")
        return []

@app.route('/api/hot-topics')
def api_hot_topics():
    """获取热门话题的API"""
    topics = get_hot_topics(10)
    topics_list = []
    for topic in topics:
        topic_dict = {
            'TopicID': topic.TopicID,
            'TopicName': topic.TopicName,
            'question_count': topic.question_count,
            'user_count': topic.user_count,
            'answer_count': topic.answer_count,
            'total_upvotes': topic.total_upvotes
        }
        topics_list.append(topic_dict)
    return jsonify(topics_list)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1')
