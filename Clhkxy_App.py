import hashlib
import os
import random
import string

from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

FILE_STORAGE_ROOT = "data/"
# 配置上传文件的存储路径和允许的文件类型
UPLOAD_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'csv'}

# 初始化 Flask 实例
Clhkxy_App = Flask(__name__)
Clhkxy_App.secret_key = os.urandom(24)
Clhkxy_App.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Clhkxy_App.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 最大上传文件大小 100MB

csrf = CSRFProtect(Clhkxy_App)

# 初始化 SQLAlchemy
Base = declarative_base()
engine = create_engine('sqlite:///Clhkxy_App.db')
Session = sessionmaker(bind=engine)

# 定义 User 模型（原 Clhkxy_App.py 中的模型）
class User(Base):
    __tablename__ = 'users'
    username = Column(String, primary_key=True)
    password_hash = Column(String)

# 定义 Urls 模型（原 Short.py 中的模型）
class Urls(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True, autoincrement=True)
    short_url = Column(Text, unique=True, nullable=False)
    long_url = Column(Text, nullable=False)

# 创建所有表结构
Base.metadata.create_all(engine)

# 初始化文件存储根目录
if not os.path.exists(FILE_STORAGE_ROOT):
    os.makedirs(FILE_STORAGE_ROOT)

# 原 Clhkxy_App.py 中的函数
def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def save_url(long_url, short_url):
    db_session = Session()
    try:
        new_link = Urls(long_url=long_url, short_url=short_url)
        db_session.add(new_link)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
    finally:
        db_session.close()

def check_if_short_url_exists(short_url):
    db_session = Session()
    try:
        return db_session.query(Urls).filter_by(short_url=short_url).first() is not None
    finally:
        db_session.close()

def create_short_url(long_url, custom_suffix=None):
    # 合并长链接与自定义后缀，确保 URL 格式正确
    if custom_suffix:
        combined_url = long_url.rstrip('/') + '/' + custom_suffix.lstrip('/')
    else:
        combined_url = long_url

    # 使用哈希生成短链接，并检查该短链接是否已存在
    short_url = hashlib.md5(combined_url.encode()).hexdigest()[:6]

    # 确保短链接唯一
    while check_if_short_url_exists(short_url):
        short_url = generate_random_string(6)  # 如果短链接已存在，则重新生成

    return short_url, combined_url

# 判断文件是否允许上传
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@Clhkxy_App.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large():
    return "文件太大，请上传小于 100MB 的文件。", 413

# 原 Clhkxy_App.py 中的路由
@Clhkxy_App.route("/")
def index():
    if "username" in session:
        return redirect(url_for("file_list"))
    return redirect(url_for("login"))

# 首页路由（新合并）
@Clhkxy_App.route('/file_index')
def file_index():
    # 获取上传的文件列表（分页展示）
    page = request.args.get('page', 1, type=int)
    files_per_page = 5
    all_files = os.listdir(Clhkxy_App.config['UPLOAD_FOLDER'])
    all_files = [file for file in all_files if allowed_file(file)]  # 过滤不允许的文件
    files_to_display = all_files[(page - 1) * files_per_page : page * files_per_page]
    total_files = len(all_files)
    total_pages = (total_files + files_per_page - 1) // files_per_page  # 总页数

    return render_template('index.html', files=files_to_display, total_pages=total_pages, current_page=page)

# 文件上传路由（新合并）
@Clhkxy_App.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(Clhkxy_App.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('file_index'))
    return "Invalid file format"

# 文件下载路由（新合并）
@Clhkxy_App.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(Clhkxy_App.config['UPLOAD_FOLDER'], filename)

# 复制文件下载链接路由（新合并）
@Clhkxy_App.route('/copy_link/<filename>')
def copy_link(filename):
    file_url = url_for('download_file', filename=filename, _external=True)
    return file_url

# 登录
@Clhkxy_App.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db_session = Session()
        try:
            user = db_session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                session["username"] = username
                return redirect(url_for("file_list"))
            else:
                return render_template("login.html", error="Invalid username or password")
        finally:
            db_session.close()
    return render_template("login.html")

# 注册
@Clhkxy_App.route("/Clhkxy_Register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        password_hash = generate_password_hash(password)

        db_session = Session()
        try:
            new_user = User(username=username, password_hash=password_hash)
            db_session.add(new_user)
            db_session.commit()

            # 创建用户文件目录
            user_dir = os.path.join(FILE_STORAGE_ROOT, username)
            os.makedirs(user_dir, exist_ok=True)

            return redirect(url_for("login"))
        except Exception as err:
            db_session.rollback()
            return render_template("register.html", error=f"Error: {err}")
        finally:
            db_session.close()
    return render_template("register.html")

# 修改密码
@Clhkxy_App.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")

        db_session = Session()
        try:
            user = db_session.query(User).filter_by(username=session["username"]).first()

            if user and check_password_hash(user.password_hash, current_password):
                new_password_hash = generate_password_hash(new_password)
                user.password_hash = new_password_hash
                db_session.commit()
                return redirect(url_for("file_list"))
            else:
                return render_template("change_password.html", error="Invalid current password")
        finally:
            db_session.close()
    return render_template("change_password.html")

# 原 Short.py 中的路由：主页，显示输入框
@Clhkxy_App.route("/short", methods=["GET", "POST"])
@Clhkxy_App.route("/short/", methods=["GET", "POST"])
def short_index():
    if request.method == "POST":
        long_url = request.form["long_url"]
        custom_suffix = request.form["custom_suffix"]

        if not long_url:
            return render_template("short.html", error="请输入一个有效的长链接！")

        # 检查长链接是否已存在
        db_session = Session()
        try:
            existing_link = db_session.query(Urls).filter_by(long_url=long_url).first()
            if existing_link:
                # 如果长链接已存在，直接返回现有的短链接
                short_url = existing_link.short_url
            else:
                # 创建短链接和合并后的长链接
                short_url, combined_url = create_short_url(long_url, custom_suffix)
                # 将链接保存到数据库
                save_url(combined_url, short_url)
            return render_template("short.html", short_url=short_url)
        finally:
            db_session.close()

    return render_template("short.html")

# 原 Short.py 中的路由：处理短链接访问
@Clhkxy_App.route("/short/<short_url>")
def redirect_to_long_url(short_url):
    db_session = Session()
    try:
        link = db_session.query(Urls).filter_by(short_url=short_url).first()
        if link:
            # 确保 long_url 是字符串类型
            long_url = str(link.long_url)
            # 重定向到长链接
            return redirect(long_url)
        else:
            # 如果找不到短链接，返回 404
            return "Short URL not found!", 404
    finally:
        db_session.close()


# 文件列表
@Clhkxy_App.route("/files", methods=["GET", "POST"])
def file_list():
    if "username" not in session:
        return redirect(url_for("login"))

    user_dir = os.path.join(FILE_STORAGE_ROOT, str(session["username"]))
    # 检查用户目录是否存在
    if not os.path.exists(user_dir):
        print(f"用户目录 {user_dir} 不存在")
        os.makedirs(user_dir, exist_ok=True)

    files = os.listdir(user_dir)

    if request.method == "POST":

        filename = request.form.get("filename")
        print(f"接收到的文件名: {filename}")
        if filename and filename.isidentifier():
            file_path = os.path.join(user_dir, filename)
            try:
                with open(file_path, "w") as f:
                    f.write("")
                print(f"文件 {file_path} 创建成功")
            except Exception as e:
                print(f"创建文件 {file_path} 时出错: {e}")
        else:
            print("无效的文件名")
        return redirect(url_for("file_list"))

    return render_template("file_list.html", files=files)

# 文件查看与编辑
@Clhkxy_App.route("/files/<filename>", methods=["GET", "POST"])
def edit_file(filename):
    if "username" not in session:
        return redirect(url_for("login"))

    user_dir = os.path.join(FILE_STORAGE_ROOT, str(session["username"]))
    # 确保 filename 是字符串类型并验证合法性
    if not isinstance(filename, str) or not filename.isidentifier():
        return "Invalid filename", 400
    file_path = os.path.join(user_dir, filename)

    if request.method == "POST":
        content = request.form.get("content")
        with open(file_path, "w") as f:
            f.write(content)
        return redirect(url_for("file_list"))

    with open(file_path, "r") as f:
        content = f.read()

    return render_template("file_edit.html", filename=filename, content=content)

# 2FA 路由
@Clhkxy_App.route("/2fa", methods=["GET"])
@Clhkxy_App.route("/2fa/<path:secret>", methods=["GET"])
def two_factor_auth(secret=None):
    secret_param = request.args.get('secret', secret)
    return render_template("2fa.html", secret=secret_param)

# 注销
@Clhkxy_App.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
@Clhkxy_App.route("/some_route", methods=["POST"])
@csrf.exempt  # 排除 CSRF 保护
def some_route():
    # 处理请求
    return "Response"



if __name__ == "__main__":
    Clhkxy_App.run(debug=True,host="0.0.0.0", port=5000)
