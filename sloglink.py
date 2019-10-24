from flask import Flask, redirect, render_template, request
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse
from urllib.request import urlopen
import sloglinkdb as db
import random
import string


app = Flask(__name__)


def linkstr_unused(linkstr, months=6):  # TODO: Has a link been unused for months?
    return False


def delete_link(linkstr, session):  # TODO: Delete a link from the database
    # del_link = db.Sloglink(linkstr=linkstr)
    # session.delete(del_link)
    # session.commit()
    pass


def valid_link(link):
    url = urlparse(link)
    if url.scheme == '':
        return False  # No http or https was used, or something is weird

    try:
        url = urlopen(link)
    except Exception:
        return False

    if url.getcode() == 200:  # URL is working
        return True
    else:
        return False


def linkstr_exists(linkstr):
    session = db.connect()
    try:
        session.query(db.Sloglink).filter(db.Sloglink.linkstr == linkstr).one()
    except Exception:  # TODO: test for the exact no-exist error
        return False
    # It exists, but...
    if linkstr_unused(linkstr):  # If not used, pretend it didn't exist
        delete_link(linkstr, session)
        return False
    return True


def long_link_exists(long_link):
    session = db.connect()
    linkstr = ''

    try:
        linkstr = session.query(db.Sloglink).filter(
            db.Sloglink.long_link == long_link).one().linkstr
    except Exception:
        return False

    return f'https://slog.link/{linkstr}'


def get_linkstr(n):
    possible = string.digits + string.ascii_letters
    generated = ""
    for p in range(n):
        generated = generated + random.choice(possible)
    return generated


def archive_link(linkstr, long_link, create_ip):
    session = db.connect()
    new_link = db.Sloglink(linkstr=linkstr, long_link=long_link, create_ip=create_ip)
    session.add(new_link)
    session.commit()


def lookup_link(url_code):
    session = db.connect()
    return session.query(db.Sloglink).filter(
        db.Sloglink.linkstr == url_code).one().long_link


@app.route('/add_link', methods=['POST', 'GET'])
def add_link():
    if request.method == 'POST':
        long_link = request.form.get("new_link")
        short_link = long_link_exists(long_link)
        create_ip = request.remote_addr
        if short_link:
            return render_template(
                'add_link.html', short_link=short_link, long_link=long_link)
        if not valid_link(long_link):  # TODO: Don't allow slog.link addresses
            short_link = 'https://slog.link'
            long_link = f"""
                The provided link ({long_link}) is invalid.
                Please confirm it is a working link, that it
                begins with 'https://', and does not require authentication to view."""
            return render_template(
                'add_link.html', short_link=short_link, long_link=long_link)

        old_linkstr = True
        attempts = 0  # Count how many times we find a used link
        link_size = 2  # Start at link size 2
        while old_linkstr:  # Only use linkstr if it's new
            if attempts == 3:  # If try more than 3 times, up the length
                link_size += 1
            linkstr = get_linkstr(link_size)
            old_linkstr = linkstr_exists(linkstr)
            attempts += 1
        short_link = f'https://slog.link/{linkstr}'
        try:
            archive_link(linkstr, long_link, create_ip)
        except IntegrityError:  # This shouldn't ever happen, but...
            short_link = 'https://slog.link'
            long_link = 'duplicate link element cannot be archived.'
        return render_template(
            'add_link.html', short_link=short_link, long_link=long_link)
    else:
        return render_template(
            'add_link.html',
            short_link='https://slog.link',
            long_link='paste a long link above')


@app.route('/<url_code>')
def sloglink(url_code):
    link = lookup_link(url_code)
    return redirect(link)


@app.route('/')
def go_add():
    return redirect('https://slog.link/add_link')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
