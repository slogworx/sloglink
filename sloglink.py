from flask import Flask, redirect, render_template, request
from sqlalchemy.exc import IntegrityError
import sloglinkdb as db
import random
import string


app = Flask(__name__)


def get_linkstr(n):
    possible = string.digits + string.ascii_letters
    generated = ""
    for p in range(n):
        generated = generated + random.choice(possible)
    return generated


def archive_link(linkstr, long_link):
    session = db.connect()
    new_link = db.Sloglink(linkstr=linkstr, long_link=long_link)
    session.add(new_link)
    # TODO: If linkstr is in use, remove if it hasn't been used in 1 year
    # TODO: If total number of linkstr in db > half possible combos,
    # bump up n for get_linkstr
    # TODO: Ensure a valid link is provided before archiving
    # TODO: Check db for long_link. If it exits, use existing linkstr
    session.commit()


def lookup_link(url_code):
    session = db.connect()
    return session.query(db.Sloglink).filter(db.Sloglink.linkstr == url_code).one().long_link


@app.route('/add_link', methods=['POST', 'GET'])
def add_link():
    if request.method == 'POST':
        long_link = request.form.get("new_link")
        linkstr = get_linkstr(2)
        short_link = f'https://slog.link/{linkstr}'
        try:
            archive_link(linkstr, long_link)
        except IntegrityError:
            short_link = 'short link exists for url: '

        return render_template('add_link.html', short_link=short_link, long_link=long_link)
    else:
        return render_template('add_link.html', short_link='slog.link', long_link='paste a long link above')


@app.route('/<url_code>')
def sloglink(url_code):
    link = lookup_link(url_code)
    return redirect(link)


@app.route('/')
def go_add():
    return redirect('https://slog.link/add_link')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
