import sqlite3
import subprocess

from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify, g
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, SubmitField, validators
import os
from ask import ask_spark
from face_status_python3_demo import caution

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 添加一个密钥用于闪现消息

UPLOAD_FOLDER = 'videos'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 设置上传文件的最大尺寸为100MB
app.config['DATABASE'] = 'database.db'

ALLOWED_EXTENSIONS = {'mp4'}


# 连接数据库
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'], check_same_thread=False)
    return db


# 关闭数据库连接
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# 创建用户表和视频表
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        is_teacher BOOLEAN NOT NULL
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_id INTEGER NOT NULL,
                        video_name TEXT NOT NULL,
                        video_url TEXT NOT NULL
                        )''')
        db.commit()


# 用户注册表单
class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[validators.DataRequired()])
    password = PasswordField('密码', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='密码不匹配')
    ])
    confirm = PasswordField('确认密码')
    is_teacher = StringField('是否为老师（1为是，0为否）')
    submit = SubmitField('注册')


# 用户登录表单
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[validators.DataRequired()])
    password = PasswordField('密码', validators=[validators.DataRequired()])
    submit = SubmitField('登录')


# 视频上传表单
class VideoForm(FlaskForm):
    video_name = StringField('视频名称', validators=[validators.DataRequired()])
    video_url = StringField('视频链接', validators=[validators.DataRequired()])
    submit = SubmitField('上传')


# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        username = form.username.data
        password = generate_password_hash(form.password.data)
        is_teacher = form.is_teacher.data
        cursor.execute("INSERT INTO users (username, password, is_teacher) VALUES (?, ?, 0)", (username, password))
        db.commit()
        flash('注册成功！请登录。')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = get_db()
        cursor = db.cursor()
        username = form.username.data
        password = form.password.data
        user = cursor.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user[2], password):
            flash('登录成功！')
            if user[3]:
                return redirect(url_for('teacher_dashboard', user_id=user[0]))  # 使用teacher_dashboard
            else:  # 转到主菜单见面
                return redirect(url_for('menu'))  # 使用menu
        else:
            flash('用户名或密码错误。')
    return render_template('login.html', form=form)


# 新增的 menu 路由
@app.route('/menu')
def menu():
    videos = get_video_list()
    print(videos)  # 打印视频列表以检查是否正确生成
    return render_template('menu.html', videos=videos)


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/check_attention', methods=['GET'])
def check_attention():
    if caution():
        return jsonify({'attention': False})
    else:
        return jsonify({'attention': True})


@app.route('/ask_to_spark', methods=['POST'])
def ask_to_spark():
    if request.method == 'POST':
        data = request.json
        question = data.get('question')
        if not question:
            return jsonify({"error": "No question provided"}), 400

        answer = ask_spark(question)
        return jsonify({"answer": answer})


@app.route('/video/<filename>')
def video(filename):
    return render_template('video.html', filename=filename)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            return redirect(url_for('index'))
        else:
            flash('Allowed file types are mp4')
            return redirect(request.url)
    return render_template('upload.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_video_list():
    return [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.mp4')]


@app.route('/analyze_video', methods=['POST'])
def analyze_video():
    data = request.get_json()
    filename = data['filename']

    # 调用分析视频的脚本
    result = subprocess.run(['python3', 'wav_change_txt.py', filename], capture_output=True, text=True)

    return jsonify({"result": result.stdout})


if __name__ == '__main__':
    app.run(debug=True)
