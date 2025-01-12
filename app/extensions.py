from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
import logging

# Configure APScheduler logging
logging.getLogger('apscheduler').setLevel(logging.INFO)

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
scheduler = BackgroundScheduler({
    'apscheduler.timezone': 'America/Los_Angeles',
    'apscheduler.job_defaults.coalesce': True,
    'apscheduler.job_defaults.max_instances': 1,
    'apscheduler.misfire_grace_time': 15*60,
    'apscheduler.job_defaults.next_run_time_format': '%Y-%m-%d %I:%M:%S %p %Z'
}) 