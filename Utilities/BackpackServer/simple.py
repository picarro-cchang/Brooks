from flask import Flask
from flask import make_response, render_template, request

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def hello():
    return 'Hello from flask'
   
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)
