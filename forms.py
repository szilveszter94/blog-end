from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Bejegyzés címe", validators=[DataRequired()])
    subtitle = StringField("Alcím", validators=[DataRequired()])
    img_url = StringField("Háttérkép URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Bejegyzés tartalma", validators=[DataRequired()])
    submit = SubmitField("Közzététel")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Jelszó", validators=[DataRequired()])
    name = StringField("Név", validators=[DataRequired()])
    submit = SubmitField("Regisztrálás!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Jelszó", validators=[DataRequired()])
    submit = SubmitField("Bejelentkezés!")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Hozzászólás", validators=[DataRequired()])
    submit = SubmitField("Küldés")
