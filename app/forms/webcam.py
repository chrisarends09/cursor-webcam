from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, URL, Length

class WebcamForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=64)])
    description = TextAreaField('Description', validators=[Length(max=256)])
    url = StringField('URL', validators=[DataRequired(), URL(), Length(max=512)])
    type = SelectField('Type', choices=[
        ('direct_image', 'Direct Image'),
        ('wetmet', 'Wetmet'),
        ('camstreamer', 'Camstreamer'),
        ('nest', 'Nest'),
        ('api', 'API'),
        ('mjpeg', 'MJPEG'),
        ('click2stream', 'Click2Stream'),
        ('html_image', 'HTML Image')
    ], validators=[DataRequired()])
    resort = StringField('Resort', validators=[Length(max=64)])
    submit = SubmitField('Add Webcam') 