from flask import Flask, redirect, render_template, request
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse
from urllib.request import urlopen
from datetime import datetime
import sloglinkdb as db
import random
import string


app = Flask(__name__)


def valid_link(link):
    url = urlparse(link)
    if url.scheme == '':
        return False  # No http or https was used, or something is weird
    elif url.hostname == 'slog.link':
        return False  # Don't make slog.link links to slog.link
    try:
        url = urlopen(link)
    except Exception:  # Can't go to link
        return False
    if url.getcode() == 200:  # URL is working, but always has to be 200?
        return True
    else:
        return False


def linkstr_exists(linkstr):
    session = db.connect()
    try:
        session.query(db.Sloglink).filter(db.Sloglink.linkstr == linkstr).one()
    except Exception:  # TODO: test for the exact no-exist error
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


def get_all_links():
    session = db.connect()
    return reversed(session.query(db.Sloglink.linkstr, db.Sloglink.long_link).all())


def update_link_use(linkstr):
    session = db.connect()
    try:
        updated_link = session.query(db.Sloglink).filter(db.Sloglink.linkstr == linkstr).one()
    except Exception:  # TODO: test for the exact no-exist error   
         return False
    updated_link.last_used = datetime.utcnow()
    session.commit()
    return True


@app.route('/add_link', methods=['POST', 'GET'])
def add_link():
    all_links = get_all_links()
    if request.method == 'POST':
        long_link = request.form.get("new_link").replace(" ","")  # Get rid of replace if break
        short_link = long_link_exists(long_link)
        create_ip = request.remote_addr
        if short_link:
            return render_template(
                'add_link.html', short_link=short_link,
                long_link=long_link, all_links=all_links)
        if not valid_link(long_link):
            short_link = 'https://slog.link'
            long_link = f"""
                The provided link ({long_link}) is invalid.
                Please confirm it is a working link, that it
                begins with 'https://', and does not require authentication to view."""
            return render_template(
                'add_link.html', short_link=short_link,
                long_link=long_link, all_links=all_links)

        old_linkstr = True
        attempts = 0  # Count how many times we find a used link
        link_size = 2  # Start at link size 2
        while old_linkstr:  # Only use linkstr if it's new
            if attempts == 3:  # If try more than 3 times, up link_size
                link_size += 1
                attempts = 0
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
            'add_link.html', short_link=short_link,
            long_link=long_link, all_links=all_links)
    else:
        return render_template(
            'add_link.html',
            short_link='https://slog.link',
            long_link='paste a long link above to create a short link', all_links=all_links)


@app.route('/<url_code>')
def sloglink(url_code):
    redir_fail = 'https://slog.link'
    link = lookup_link(url_code)
    if update_link_use(url_code):
        return redirect(link)
    else:
        return redirect(redir_fail)


@app.route('/')
def go_add():
    return redirect('https://slog.link/add_link')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
