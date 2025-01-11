from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, URL, Length

class WebcamForm(FlaskForm):
    id = HiddenField('ID')  # For editing existing webcams
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
    submit = SubmitField('Save Webcam') 