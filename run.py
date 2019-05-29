#C:\Users\Asus\Projects\Environments\flasksocketiochat\Scripts\activate.bat
#cd C:\Users\Asus\guesswho
from flask import Flask
from flask import session, redirect, url_for, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_mail import Mail, Message
from forms import LoginForm, SendMessageForm, ContactForm
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import uuid

app = Flask(__name__)

app.debug = True
app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = 'guesswhospy2019@gmail.com'
app.config["MAIL_PASSWORD"] = '111password111'
app.config["MAIL_DEFAULT_SENDER"] = 'guesswhospy2019@gmail.com'


socketio = SocketIO(app)
db = SQLAlchemy(app)
migrate = Migrate(app,db)
mail = Mail(app)

N = 3

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), nullable=False)
    session_id = db.Column(db.String(200), nullable=False)
    isready = db.Column(db.Integer, default='0')
    isspy = db.Column(db.Integer, default='0')
    votes = db.Column(db.Integer, default='0')
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))

    def __repr__(self):
        return f"User('{self.username}', '{self.session_id}')"

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(15), nullable=False)
    image_file = db.Column(db.String(20))
    room = db.relationship('Rooms', backref='place', lazy=False)
    def __repr__(self):
        return f"Location('{self.name}', '{self.image_file}')"

class Rooms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    s_id = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    spy_id = db.Column(db.Integer, default=1)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))
    users = db.relationship('User', backref='player', lazy=False)

    def __repr__(self):
        return f"Rooms('{self.location}', '{self.spy}')"

def RandomLocation():
    import random
    x = random.randint(1,9)
    r_location = db.session.query(Location).filter_by(id=x).first()
    loc_id = r_location.id
    return loc_id

def RandomSpy(a_room, new_user):
    import random
    ifspy = 0
    count = 0
    for user in a_room.users:
        if user.isspy == 1:
            ifspy = 1
            break
        else:
            count += 1
    if count == N:
        new_user.isspy = 1
        db.session.commit()
    else:
        if not ifspy:
            x = random.randint(0,1)
            new_user.isspy = x
            db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        count = 1
        session['name'] = form.name.data
        session['room'] = form.room.data
        room_empty = db.session.query(Rooms).filter_by(status='active').count()
        session_id = str(uuid.uuid1())
        if room_empty == 0:
            a_room = Rooms(s_id=session_id, status='active')
            db.session.add(a_room)
            db.session.commit()
            new_user = User(username=session.get('name', ''), session_id=session_id, room_id=a_room.id)
            db.session.add(new_user)
            db.session.commit()
            a_room.location_id = RandomLocation()
            db.session.commit()
            session['room'] = a_room.s_id
        else:
            a_room = db.session.query(Rooms).filter_by(status='active').first()
            session['room'] = a_room.s_id
            new_user = User(username=session.get('name', ''), session_id=session_id, room_id=a_room.id)
            db.session.add(new_user)
            db.session.commit()
            count = 0
            print(a_room.users)
            for user in a_room.users:
                count = count + 1
                print(count)
            if count >= N:
                a_room.status = 'closed'
                db.session.commit()
        room = session.get('room')
        session['start'] = count
        RandomSpy(a_room, new_user)
        db.session.commit()
        session['cur_user_id'] = new_user.id
        return redirect(url_for('.game'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
    return render_template('index.html', form=form)

@app.route('/rules')
def rules():
    return render_template('rules.html', title="Правила игры")

@app.route('/locations')
def locations():
    return render_template('locations.html', title="Локации")

@app.route('/about', methods=['GET', 'POST'])
def about():
    form = ContactForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            print(form.name.data, 'message was sent')
            msg = Message(form.subject.data, recipients=['bigmeawmeawarmy@gmail.com'])
            msg.body = """
            От: %s <%s>
            %s
            """ % (form.name.data, form.email.data, form.message.data)
            mail.send(msg)
            return redirect(url_for('about'))
        else:
            print('error')
            return render_template('about.html', title="О разработчиках", form=form)
    elif request.method == 'GET':
        return render_template('about.html', title="О разработчиках", form=form)

@app.route('/game')
def game():
    """Chat room. The user's name and room must be stored in
    the session."""
    form = SendMessageForm()
    name = session.get('name', '')
    room = session.get('room', '')
    start = session.get('start', '')
    cur_user_id = session.get('cur_user_id', '')
    current_user = db.session.query(User).filter_by(id=cur_user_id).first()
    room_obj = db.session.query(Rooms).filter_by(s_id=room).first()
    location_id = room_obj.location_id
    location = db.session.query(Location).filter_by(id=location_id).first()
    start_time = room_obj.start_time
    session['time'] = str(start_time)
    spy = db.session.query(User).filter_by(room_id=room_obj.id, isspy=1).first()
    if name == '' or room == '':
        return redirect(url_for('.index'))
    return render_template('game.html', name=name, form=form, room=room, room_obj=room_obj, title="Игра",
                            current_user=current_user, location=location, start=start, spy=spy)

@socketio.on('joined', namespace='/game')
def joined(message):
    """Отправляется клиентом, когда он заходит в комнату.
    Статус отправляется всем пользователям в комнате."""
    room = session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('name') + ' присоединился/ась к игре '}, room=room)

@socketio.on('add_user', namespace='/game')
def add_user(message):
    """ Обновляет список игроков у всех в комнате """
    room = session.get('room')
    emit('new_user', {'msg': session.get('name')}, room=room)

@socketio.on('text', namespace='/game')
def text(message):
    """Отправялется клиентом, когда он отправляет сообщение
    Сообщение отправляется всем пользователям в комнате"""
    room = session.get('room')
    emit('message', {'msg': session.get('name') + ': ' + message['msg']}, room=room)

@socketio.on('left', namespace='/game')
def left(message):
    """Отправялется клиентом, когда он покидает комнату
    Статус отправляется всем пользователям в комнате."""
    room = session.get('room')
    leave_room(room)
    emit('status', {'msg': session.get('name') + ' покинул/а чат.'}, room=room)

@socketio.on('disconnect', namespace='/game')
def test_disconnect():
    room = session.get('room')
    name = session.get('name')
    print(room)
    print(name)
    room_obj = db.session.query(Rooms).filter_by(s_id=room).first()
    room_id = room_obj.id
    leaving_user = db.session.query(User).filter_by(room_id=room_id, username=name).first()
    db.session.query(User).filter_by(id=leaving_user.id).delete()
    db.session.commit()
    print('Client was deleted from database')
    count = 0
    for user in room_obj.users:
        count += 1
    if count == 0:
        db.session.query(Rooms).filter_by(id=room_obj.id).delete()
        db.session.commit()
        print('Room was deleted from database')

@socketio.on('vote', namespace='/game')
def voteHandler(ballot):
    room = session.get('room', '')
    print(ballot)
    room_obj = db.session.query(Rooms).filter_by(s_id=room).first()
    room_id = room_obj.id
    user = db.session.query(User).filter_by(room_id=room_id, id=ballot).first()
    user.votes = user.votes + 1
    u = ['','','']
    v = ['','','']
    i = 0
    for us in room_obj.users:
        u[i] = us.username
        v[i] = str(us.votes)
        i += 1
    result_1 = u[0] + ' - ' + v[0]
    result_2 = u[1] + ' - ' + v[1]
    result_3 = u[2] + ' - ' + v[2]
    print(user.votes)
    db.session.commit()
    emit('vote', {'result_1' : result_1, 'result_2' : result_2, 'result_3' : result_3}, broadcast=True, room=room)


@socketio.on('endofgame', namespace='/game')
def endofgame(result):
    room = session.get('room', '')
    room_obj = db.session.query(Rooms).filter_by(s_id=room).first()
    room_id = room_obj.id
    max_vote = db.session.query(db.func.max(User.votes)).filter_by(room_id=room_id).scalar()
    users = db.session.query(User).filter_by(votes=max_vote).count()
    victim = db.session.query(User).filter_by(votes=max_vote).first()
    spy = db.session.query(User).filter_by(room_id=room_id, isspy=1).first()
    if users > 1:
        result = 'Победил шпион!'
    elif spy.id == victim.id:
        result = 'Победили нешпионы!'
    else:
        result = 'Победил шпион!'
    print(max_vote)
    emit('endofgame', {'result': result} , broadcast=True, room=room)

@socketio.on('locationguess', namespace='/game')
def locationguess(result):
    room = session.get('room', '')
    emit('locationguess', result , broadcast=True, room=room)

@socketio.on('gamestarted', namespace='/game')
def gamestarted():
    room = session.get('room', '')
    count = session.get('start', '')
    emit('player', {'count':count }, room=room, namespace='/game')

if __name__ == '__main__':
    socketio.run(app)
