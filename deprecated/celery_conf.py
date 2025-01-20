"""
Moved the Celery app and it's configuration here to make tasks import and naming structure simplier
"""
from celery import Celery


app = Celery('tasks', broker="amqp://guest@localhost", backend="rpc://")
# we need to add our files with tasks to the imports manually cause they aren't called tasks.py
#app.conf.update(imports=('data_analysis.data_analysis_driver', 'machine_learning_analysis.ml_analysis'))
app.conf.update(imports=('driver.ml_driver'))
