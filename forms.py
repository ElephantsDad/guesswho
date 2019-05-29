from flask_wtf import Form
from wtforms.fields import StringField, SubmitField, TextAreaField
from wtforms.validators import Required, Length, Email


class LoginForm(Form):
    """Accepts a nickname and a room."""
    name = StringField('Никнейм', validators=[Required(),Length(min=2, max=15)])
    room = StringField('Название игры', validators=[Required()], default='1')
    submit = SubmitField('Начать игру')

class SendMessageForm(Form):
    message = StringField('Сообщение:', validators=[Required(),Length(max=200)])
    submit = SubmitField('Отправить')

class ContactForm(Form):
    name = StringField('Имя', validators=[Required(),Length(min=2, max=30)])
    email = StringField('Email', validators=[Required(), Email()])
    subject = StringField('Тема', validators=[Required()])
    message = TextAreaField('Сообщение', validators=[Required(),Length(min=10, max=1000)])
    submit = SubmitField('Отправить')
