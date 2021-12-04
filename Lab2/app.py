from datetime import datetime
from flask import Flask, request,render_template,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from enum import unique
from flask_bcrypt import Bcrypt, check_password_hash, generate_password_hash
from flask_login import LoginManager, login_required, current_user, login_user, logout_user, UserMixin

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"
app.config["SECRET_KEY"] = "supersecret"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model):
    id = db.Column(db.Integer ,primary_key=True)
    email=db.Column(db.String(50),unique=True,nullable=False)
    username = db.Column(db.String(50),unique=True ,nullable=False)
    password = db.Column(db.String(50),nullable=False)
    todos=db.relationship('Todo',lazy=True,backref='user')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def get_id(self):
        return self.id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        return True

class Todo(db.Model):
    id=db.Column(db.Integer ,primary_key=True)
    title=db.Column(db.String(50),nullable=False)
    description=db.Column(db.String(50), nullable=False)
    created_at=db.Column(db.DateTime, nullable=False,default=datetime.utcnow)
    is_done= db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=True,)
todos =[]
# def get_id():
#     id=1
#     if len(todos) > 0:
#         id =todos[-1]["id"] +1
#     return id 
# db.create_all()
@app.route("/")
def index():
    if current_user.is_authenticated:
        todos=current_user.todos
        return render_template("index.html",todos=todos)
    else:
        return render_template("login.html")

@app.route("/unactivate")
def index_unactive():
    todos=Todo.query.filter_by(user_id=current_user.id ,is_done=False).all()

    return render_template("index.html",todos=todos)



@app.route("/todo", methods=["GET","POST"])
@login_required
def create_todo():
    if request.method =="POST":
        print(request.form.get("is_done"))
        todo=Todo(
            title=request.form.get("title"),
            description=request.form.get("description"),
            is_done=True if request.form.get("is_done") == "on" else False ,
            user_id=current_user.id,)
        db.session.add(todo)
        db.session.commit()
        
        return redirect(url_for("index"))
    return render_template("todo_form.html")

@app.route("/todo/<int:id>", methods=["GET"])
def get_todo(id):
    todo =Todo.query.filter_by(user_id=current_user.id,id=id).first()
    if not todo:
        return render_template("notfound.html")
    return render_template("todo.html",todo=todo)


@app.route("/todo/<int:id>/edit",methods=["GET","POST"])
@login_required
def edit_todo(id):
    # todo= list(filter(lambda todo: todo["id"] == id ,todos))
    
    todo = Todo.query.filter_by(user_id=current_user.id, id=id).first()
    if not todo:
        return render_template("notfound.html")
    if request.method == "POST":
        todo.title= request.form.get("title")
        todo.description=request.form.get("description")
        

        db.session.add(todo)
        db.session.commit()
        return redirect(url_for("index", id=id))
    print (todo.description)
    return render_template("todo_form.html",todo=todo)



@app.route("/todo/<int:id>/done",methods=["GET","POST"])
@login_required
def done_todo(id):
    # todo= list(filter(lambda todo: todo["id"] == id ,todos))
    
    todo = Todo.query.filter_by(user_id=current_user.id, id=id).first()
    print(todo.is_done)
    if not todo:
        return render_template("notfound.html")
    if request.method == "GET":
        if todo.is_done==False:
            todo.is_done= True
        else:
            todo.is_done= False
        db.session.add(todo)
        db.session.commit()
        todos=current_user.todos
    return render_template("index.html",todos=todos)


@app.route("/todo/<int:id>/delete", methods=["GET"])
@login_required
def delete_todo(id):
    todo = Todo.query.filter_by(user_id=current_user.id, id=id).first()
    db.session.delete(todo)
    db.session.commit()


    if not todo:
        return render_template("notfound.html")
    todos=current_user.todos
    return render_template("index.html",todos=todos)


@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()
        if not user or not user.check_password(request.form.get("password")):
            return redirect(url_for("login"))
        login_user(user)
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method=="POST":
        if request.form.get("password") != request.form.get("confirm_password"):
            return redirect(url_for('register'))
        user=User(username=request.form.get("username"),
        email=request.form.get("email")
        
        )
        user.set_password(request.form.get("password"))
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            print(e.args)
            print("User already exists")
            return redirect(url_for('register'))
        login_user(user)
        return redirect(url_for('index'))
    return render_template("register.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template("login.html")



if __name__ == '__main__':
    app.run("127.0.0.1","8000",debug=True)