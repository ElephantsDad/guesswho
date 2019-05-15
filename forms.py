from flask_wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import Required, Length


class LoginForm(Form):
    """Accepts a nickname and a room."""
    name = StringField('Никнейм', validators=[Required(),Length(min=2, max=15)])
    room = StringField('Название игры', validators=[Required()], default='1')
    submit = SubmitField('Начать игру')

class SendMessageForm(Form):
    message = StringField('Сообщение:', validators=[Required(),Length(max=200)])
    submit = SubmitField('Отправить')
