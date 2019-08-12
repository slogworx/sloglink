from flask import Flask, redirect
import random
import string


app = Flask(__name__)


def gen_linkstr(n):
    possible = string.digits + string.ascii_letters
    generated = ""
    for p in range(int(n)):
        generated = generated + random.choice(possible)
    return generated


def lookup_link(url_code):
    pass  # TODO: Query the link database and return the redirect link.


@app.route('/add_link')
def add_link():
    pass  # TODO: Add a form to add links and short references to them into the database.


@app.route('/<url_code>')
def sloglink(url_code):

    link = lookup_link(url_code)
    return redirect(link)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
