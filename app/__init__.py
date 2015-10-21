from flask import Flask 

#The script above simply creates the application object (of class Flask)
#and then imports the views module, which we haven't written yet
app = Flask(__name__)
from app import views 

