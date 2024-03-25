from flask import Flask


app = Flask(__name__, template_folder='templates')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Remplacez ceci par votre propre clé secrète



def runapp():

    if __name__ == '__main__':
        app.run(debug=False)