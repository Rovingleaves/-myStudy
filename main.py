import os, info
from decimal import Decimal
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, IntegerField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets.html5 import NumberInput
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

@app.route('/hello', methods=['GET','POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known']=False
            if app.config['OPPYUBB_ADMIN']:
                send_email(app.config['OPPYUBB_ADMIN'],'New User','mail/new_user',user=user)
        else:
            session['known']=True
        session['name']=form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('hello.html',
                           name = session.get('name'),
                           form = form,
                           known=session.get('known',False),
                           current_time=datetime.utcnow())

@app.route('/tools', methods=['GET'])
def tools_list():
    return render_template('tools.html')

class CVCForm(FlaskForm): #Carton Valume Calculator
    height = DecimalField('Height (cm)', widget=NumberInput(step=0.01),validators = [DataRequired(),NumberRange(min=1, max=1000)])
    width = DecimalField('Width (cm)', widget=NumberInput(step=0.01),validators = [DataRequired(),NumberRange(min=1, max=1000)])
    depth = DecimalField('Depth (cm)', widget=NumberInput(step=0.01),validators = [DataRequired(),NumberRange(min=1, max=1000)])
    gross_weight = DecimalField('Gross Weight (kg)', default=0, widget=NumberInput(step=0.01),validators = [NumberRange(min=0, max=100)])
    submit = SubmitField('Submit')

@app.route('/tools/Carton_Volume_Calculator', methods=['GET','POST'])
def CVC():
    form = CVCForm()
    del form.gross_weight
    result = 0
    if form.validate_on_submit():
        height = form.height.data
        width = form.width.data
        depth = form.depth.data
        result = Decimal((height*width*depth)/Decimal(28316.85)).quantize(Decimal('0.00'))
    return render_template('Carton_Volumn_Calculator.html',
                           form = form,
                           result = result)

class CWCForm(CVCForm): 
    pass
@app.route('/tools/Chargeable_Weight_Calculator', methods=['GET','POST'])
def CWC():
    form = CWCForm()
    gross_weight = 0
    volume_weight = 0
    charageable_weight_is_gross_weight = None
    if form.validate_on_submit():
        height = form.height.data
        width = form.width.data
        depth = form.depth.data
        gross_weight = form.gross_weight.data
        volume_weight = Decimal((height*width*depth)/5000).quantize(Decimal('0.00'))
        if gross_weight > volume_weight or gross_weight == volume_weight:
            charageable_weight_is_gross_weight = True
        else:
            charageable_weight_is_gross_weight = False
    return render_template('Chargeable_Weight_Calculator.html',
                           form = form,
                           gross_weight = gross_weight,
                           volume_weight = volume_weight,
                           charageable_weight_is_gross_weight = charageable_weight_is_gross_weight)

class SCCForm(FlaskForm): #Shipping Cost Calculator
    total_weight = DecimalField('Chareable Weight (KG)', widget=NumberInput(step=0.01),validators = [DataRequired(),NumberRange(min=1, max=100000)])
    local = IntegerField('Local Transportation Cost (NTD)', default=0,validators = [NumberRange(min=0, max=100000)])
    shipping = DecimalField('Air Freight Cost per Kilogram (NTD)',validators = [DataRequired(),NumberRange(min=1, max=100000)])
    BAF = IntegerField('BAF (Bunker Adjustment Factor) per Kilogram (NTD)', default=0,validators = [NumberRange(min=0, max=100000)])
    war = IntegerField('War Insurance Tax per Kilogram (NTD)', default=0,validators = [NumberRange(min=0, max=100000)])
    customs = IntegerField('Customs Clearance Fee (NTD)', default=600,validators = [NumberRange(min=0, max=100000)])
    CAS = IntegerField('CAS (Clearance Automatic Server) (NTD)', default=240,validators = [NumberRange(min=0, max=100000)])
    AMS = IntegerField('AMS (Automatic Manifest Server) (NTD)', default=0,validators = [NumberRange(min=0, max=100000)])
    warehouse = IntegerField('Warehouse Rental Fee per Kilogram (NTD)',default=6, validators = [NumberRange(min=1, max=100000)])
    warehouse_exceed = IntegerField('+300 Warehouse Rental Fee per Kilogram (NTD)', default=0,validators = [NumberRange(min=0, max=100000)])
    other = IntegerField('Other Cost (NTD)', default=0,validators = [NumberRange(min=0, max=100000)])
    submit = SubmitField('Submit')

@app.route('/tools/CIF_Calculator_Air', methods=['GET','POST'])
def CCA():
    form = SCCForm()
    result = 0
    rent = 0
    if form.validate_on_submit():
        total_weight = form.total_weight.data
        local = form.local.data
        shipping = form.shipping.data*total_weight
        BAF = form.BAF.data*total_weight
        war = form.war.data*total_weight
        customs = form.customs.data
        CAS = form.CAS.data
        AMS = form.AMS.data
        warehouse = form.warehouse.data
        warehouse_exceed = form.warehouse_exceed.data
        other = form.other.data
        if total_weight < 300:
            rent = total_weight*warehouse
        else:
            rent = (warehouse*300) + ((total_weight-300)*warehouse_exceed)

        result = local + shipping + BAF + war + customs + CAS + AMS + rent +other
        result = Decimal(result).quantize(Decimal('0'))
        result = format(result, '0,.0f')
    return render_template('CIF_Calculator_Air.html',
                           form = form,
                           result = result)

@app.route('/tools/USD_to_NTD_Exchange_Rate',methods=['GET','POST'])
def US_to_NTD_Exchange_Rate():
    today_rate = info.today_USD_rate()
    last_rate = info.last_day_USD_rate()
    time = info.scraping_time()
    day = info.last_business_day()

    return render_template('USD_to_NTD_Exchange_Rate.html',
                           today = today_rate,
                           last = last_rate,
                           time = time,
                           day = day)
    

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'),500
