from flask import Flask, redirect, render_template, request
from sqlalchemy.exc import IntegrityError
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen
from datetime import datetime
from pathlib import Path
import logging
import sloglinkdb as db
import random
import string


logging.basicConfig(filename='log/sloglink.log', level=logging.INFO)
app = Flask(__name__)


def valid_link(link):
    url = urlparse(link)
    if url.scheme == '':
        return False  # No http or https was used, or something is weird
    elif url.hostname == 'slog.link':
        return False  # Don't make slog.link links to slog.link
    
    try:
        url_resp = urlopen(link)
    except HTTPError as e:  # Can't go to link for some reason
        if e.getcode() == 503:  # Link is valid but Cloudflare didn't like the header or link timed out
            logging.info(f'[{str(datetime.now())}]: {link} is valid, but returned error 503.')
            return True
        else:
            logging.warning(f'[{str(datetime.now())}]: {link} is an invalid url, returned HTTPError {e.getcode()}.')
            return False
    except Exception:
        logging.warning(f'[{str(datetime.now())}]: {link} is an invalid url, unknown exception.')
        return False  # No idea what happened
    
    logging.info(f'[{str(datetime.now())}]: Valid link {link} returned {url_resp.getcode()}.')
    return True  # Link OK!


def linkstr_exists(linkstr):
    session = db.connect()
    try:
        session.query(db.Sloglink).filter(db.Sloglink.linkstr == linkstr).one()
    except Exception:  # TODO: test for the exact exception
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
    
    logging.warning(f'[{str(datetime.now())}]: {long_link} was submitted but already exists in the database.')
    return f'https://slog.link/{linkstr}'


def get_linkstr(n):
    possible = string.digits + string.ascii_letters
    generated = ""
    for p in range(n):
        generated = generated + random.choice(possible)
    return generated


def archive_link(linkstr, long_link):  # TODO: Check exceptions? Does this need to return success/failure value?
    session = db.connect()
    new_link = db.Sloglink(linkstr=linkstr, long_link=long_link)
    session.add(new_link)
    session.commit()
    logging.info(f'[{str(datetime.now())}]: {long_link} successfully added using key of {linkstr}.')


def lookup_link(url_code):
    session = db.connect()
    try:
        long_link = session.query(db.Sloglink).filter(db.Sloglink.linkstr == url_code).one().long_link
    except Exception:
        long_link = None
    
    return long_link


def get_all_links():
    session = db.connect()
    return reversed(session.query(db.Sloglink.linkstr, db.Sloglink.long_link, db.Sloglink.last_used).order_by(db.Sloglink.last_used).all())


def update_link_use(linkstr):
    session = db.connect()
    try:
        updated_link = session.query(db.Sloglink).filter(db.Sloglink.linkstr == linkstr).one()
    except Exception:  # TODO: test for the exact exception  
         return False
    updated_link.last_used = datetime.utcnow()
    session.commit()
    logging.info(f'[{str(datetime.now())}]: Key {linkstr} last_used updated.')
    return True


@app.route('/add_link', methods=['POST', 'GET'])
def add_link():
    all_links = get_all_links()
    if request.method == 'POST':
        long_link = request.form.get("new_link").replace(" ","")
        short_link = long_link_exists(long_link)
        if short_link:
            return render_template(
                'add_link.html', short_link=short_link,
                long_link=long_link, all_links=all_links)
        if not valid_link(long_link):
            short_link = 'https://slog.link'
            long_link = f"""
                Unable to add link ({long_link}). Please confirm it is valid, it 
                begins with 'https://', and that it DOES NOT require authentication to view."""
            return render_template(
                'add_link.html', short_link=short_link,
                long_link=long_link, all_links=all_links)

        old_linkstr = True
        attempts = 0  # Count how many times we find a used link
        link_size = 2  # Start at link size 2
        while old_linkstr:  # Only use linkstr if it's new
            if attempts == 3:  # If try more than 3 times, up link_size
                link_size += 1
                logging.warning(
                    f'[{str(datetime.now())}]: Link key length required an upgrade to {link_size}!')
                attempts = 0
            linkstr = get_linkstr(link_size)
            old_linkstr = linkstr_exists(linkstr)
            attempts += 1
        short_link = f'https://slog.link/{linkstr}'
        try:
            archive_link(linkstr, long_link)
        except IntegrityError:  # This shouldn't ever happen, but...
            short_link = 'https://slog.link'
            long_link = 'duplicate link element cannot be archived.'
            logging.warning(
                f'[{str(datetime.now())}]: Duplicate link key {linkstr} was generated but not detected!')
        
        return render_template(
            'add_link.html', short_link=short_link,
            long_link=long_link, all_links=all_links)
    else:
        return render_template(
            'add_link.html',
            short_link='https://slog.link',
            long_link='Paste a long link above and click Submit.', all_links=all_links)


@app.route('/<url_code>')
def sloglink(url_code):
    redir_fail = 'https://slog.link'
    link = lookup_link(url_code)
    if link == None:
        pass  # TODO: Figure out how to message the user that they used an invalid link key
    if update_link_use(url_code):
        logging.info(f'[{str(datetime.now())}]: Redirected {url_code} to {link}.')
        return redirect(link)
    else:
        logging.warning(
            f'[{str(datetime.now())}]: Link key {url_code} was requested but has not been assigned to a link!')
        return redirect(redir_fail)


@app.route('/')
def go_add():
    return redirect('https://slog.link/add_link')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
