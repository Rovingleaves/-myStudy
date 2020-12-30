import os
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_mail import Message
from threading import Thread

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['OPPYUBB_MAIL_SUBJECT_PREFIX'] = '[oppyubb] '
app.config['OPPYUBB_MAIL_SENDER'] = 'oppyubb Admin<oppyubb@gmail.com>'
app.config['OPPYUBB_ADMIN'] = os.environ.get('OPPYUBB_ADMIN')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'rovin_flask'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
migrate = Migrate(app, db)
mail = Mail(app)

class Role(db.Model):
    __tablename__= 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64),unique=True)
    users = db.relationship('User',backref='role', lazy='dynamic')
    
    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique = True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    def __repr__(self):
        return '<User %r>' %self.username

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators = [DataRequired()])
    submit = SubmitField('Submit')
    
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    msg = Message(app.config['OPPYUBB_MAIL_SUBJECT_PREFIX']+subject,\
          sender=app.config['OPPYUBB_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template+ '.txt', **kwargs)
    msg.html = render_template(template+ '.html',**kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr

@app.route('/', methods=['GET','POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            #db.session.commit()
            session['known']=False
            if app.config['OPPYUBB_ADMIN']:
                send_email(app.config['OPPYUBB_ADMIN'],'New User','mail/new_user',user=user)
        else:
            session['known']=True
        session['name']=form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html',
                           name = session.get('name'),
                           form = form,
                           known=session.get('known',False),
                           current_time=datetime.utcnow())

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'),500