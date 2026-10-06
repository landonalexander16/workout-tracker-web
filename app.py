from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "..."

@app.route("/test")
def list_test():
    return "test successful"

if __name__ == "__main__":
    app.run(debug=True)