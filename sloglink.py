from flask import Flask, redirect, render_template, request
from sqlalchemy.exc import IntegrityError
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen
from datetime import datetime
from random import choice
from pathlib import Path
from cred_crypto import load_text
import logging
import sloglinkdb as db
import random
import string

HOSTNAME = '127.0.0.1:5000'  # Change this to your host
RESTRICTED_KEYS = (  # Reserved or Nope
    'kkk',  # Nope
    'KKK',  # Nope
    'blm',  # Reserved
    'BLM',  # Reserved
    'housekeeping',  # Reserved
    'long',  # Reserved
)
logging.basicConfig(filename='log/sloglink.log', level=logging.INFO)
app = Flask(__name__)


def valid_link(link):
    url = urlparse(link)
    if url.scheme == '':
        return False  # No http or https was used, or something is weird
    elif url.hostname == HOSTNAME:
        return False  # Don't make short links to short links

    try:
        url_resp = urlopen(link)
    except HTTPError as e:  # Can't go to link for some reason
        if e.getcode() == 503:  # Link is valid but Cloudflare didn't like the header or link timed out
            logging.info(f'[{str(datetime.now())}]: {link} is valid, but returned error 503.')
            return True
        elif e.getcode() == 403:
            logging.info(f'[{str(datetime.now())}]: {link} is valid, but returned error 403.')
            return True
        else:
            logging.warning(f'[{str(datetime.now())}]: {link} is an invalid url, returned HTTPError {e.getcode()}.')
            return False
    except Exception:
        logging.warning(f'[{str(datetime.now())}]: {link} is an invalid url, unknown exception.')
        return False  # No idea what happened

    logging.info(f'[{str(datetime.now())}]: Valid link {link} returned {url_resp.getcode()}.')
    return True  # Link OK!


def link_key_exists(link_key):
    session = db.connect()

    try:
        session.query(db.Sloglink).filter(db.Sloglink.link_key == link_key).one()
    except Exception:  # TODO: test for the exact exception
        return False
    return True


def long_link_exists(long_link):
    session = db.connect()
    link_key = HOSTNAME

    try:
        link_key = session.query(db.Sloglink).filter(
            db.Sloglink.long_link == long_link).one().link_key
    except Exception:
        return False

    logging.warning(f'[{str(datetime.now())}]: {long_link} was submitted but already exists in the database.')
    return f'{HOSTNAME}/{link_key}'


def get_link_key(n):
    possible = string.digits + string.ascii_letters
    generated = ""
    for p in range(n):
        generated = generated + random.choice(possible)
    return generated


def archive_link(link_key, long_link):  # TODO: Check exceptions? Does this need to return success/failure value?
    session = db.connect()
    new_link = db.Sloglink(link_key=link_key, long_link=long_link)
    session.add(new_link)
    session.commit()
    logging.info(f'[{str(datetime.now())}]: {long_link} successfully added using key of {link_key}.')


def delete_link(link_key):
    session = db.connect()
    slog_link = session.query(db.Sloglink).filter(db.Sloglink.link_key == link_key)
    success = slog_link.delete()
    if success:
        session.commit()
        logging.info(f'[{str(datetime.now())}]: Deleted link with link key {link_key}.')
    else:
        logging.warning(f'[{str(datetime.now())}]: Failed to delete link with link key {link_key}.')


def lookup_link(url_code):
    session = db.connect()
    try:
        long_link = session.query(db.Sloglink).filter(db.Sloglink.link_key == url_code).one().long_link
    except Exception:
        long_link = None
    
    return long_link


def lookup_url(long_url):
    session = db.connect()
    try:
        link_key = session.query(db.Sloglink).filter(db.Sloglink.long_link == long_url).one().link_key
    except Exception:
        link_key = None
    return link_key


def get_all_links():
    session = db.connect()
    return reversed(session.query(db.Sloglink.link_key, db.Sloglink.long_link, db.Sloglink.last_used).order_by(db.Sloglink.last_used).all())


def update_link_use(link_key):
    session = db.connect()
    try:
        updated_link = session.query(db.Sloglink).filter(db.Sloglink.link_key == link_key).one()
    except Exception:  # TODO: test for the exact exception  
         return False
    updated_link.last_used = datetime.utcnow()
    session.commit()
    logging.info(f'[{str(datetime.now())}]: Key {link_key} last_used updated.')
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
            short_link = HOSTNAME
            long_link = f"""
                Unable to add link ({long_link}). Please confirm it is valid,
                it begins with 'https://', and that it DOES NOT require
                authentication to view."""
            return render_template(
                'add_link.html', short_link=short_link,
                long_link=long_link, all_links=all_links)

        old_link_key = True
        attempts = 0  # Count how many times we find a used link
        link_size = 2  # Start at link size 2
        while old_link_key:  # Only use link_key if it's new
            if attempts == 3:  # If try more than 3 times, up link_size
                link_size += 1
                logging.warning(
                    f'[{str(datetime.now())}]: Link key length required an upgrade to {link_size}!')
                attempts = 0
            link_key = get_link_key(link_size)
            if link_key in RESTRICTED_KEYS:  # Keeps RESTRICTED_KEYS from being generated
                continue
            old_link_key = link_key_exists(link_key)
            attempts += 1
        short_link = f'{HOSTNAME}/{link_key}'
        try:
            archive_link(link_key, long_link)
        except IntegrityError:  # This shouldn't ever happen, but...
            short_link = HOSTNAME
            long_link = 'duplicate link element cannot be archived.'
            logging.warning(
                f'[{str(datetime.now())}]: Duplicate link key {link_key} was generated but not detected!')

        return render_template(
            'add_link.html', short_link=short_link,
            long_link=long_link, all_links=all_links)
    else:
        return render_template(
            'add_link.html',
            short_link=HOSTNAME,
            long_link='Paste a long link above and click Submit.', all_links=all_links)


# Make sure to comment this out before publishing until auth is created for it!
# TODO: houskeeping auth
'''
@app.route('/housekeeping',methods=['POST', 'GET'])
def slogadmin():
    valid_link_response = ''
    if request.method == 'POST':
        delete_list = request.form.getlist("delete_list")
        if len(delete_list):
            for key in delete_list:
                delete_link(key)
        long_link = request.form.get("long_link")
        vanity_link = request.form.get("vanity_link")
        try:
            if len(long_link) and len(vanity_link):  # Vanity link form was used
                if valid_link(long_link):  # Link must be valid
                    short_link = long_link_exists(long_link)  # Link must not already exist
                    if not short_link:
                        if not link_key_exists(vanity_link):  # Link key must not be in use
                            archive_link(vanity_link, long_link)
                            valid_link_response = f'Added "{vanity_link}" =>  "{long_link}".'
                            logging.info(valid_link_response)
                        else:
                            valid_link_response = f'{vanity_link} is already in use.'
                    else:
                        valid_link_response = f'"{long_link}" is already linked via "{short_link}".'
                else:
                    valid_link_response = f'"{long_link}" is not a valid URL.'
        except TypeError:
            pass
    slog_links = []
    for link in get_all_links():
        slog_links.append(link)

    return render_template('slogadmin.html',slog_links=slog_links,link_response=valid_link_response)
'''


# Black Lives Matter!
@app.route('/BLM')
@app.route('/blm')
def blm():
    black_authors = []
    with open('static/black_authors', 'r') as black_authors_file:
        for name in black_authors_file:
            black_authors.append(name.strip('\n'))
    logging.info(f'[{str(datetime.now())}]: BLM Author Suggestion!')
    return redirect(f"https://duckduckgo.com/?q={choice(black_authors).replace(' ','+')}+Author+Book")    


@app.route('/<url_code>')
def sloglink(url_code):
    redir_fail = '/add_link'
    link = lookup_link(url_code)
    if update_link_use(url_code):
        logging.info(f'[{str(datetime.now())}]: Redirected {url_code} to {link}.')
        return redirect(link)
    else:
        # The requested key was not valid, so log it
        # But first check for invalid characters to keep logs from getting cluttered by hackbots
        log_use = True
        for symbol in list(string.punctuation):
            if symbol in list(url_code):
                log_use = False
        if log_use:
            logging.warning(
                f'[{str(datetime.now())}]: Link key {url_code} was requested but has not been assigned to a link!')
        return redirect(redir_fail)


@app.route('/long', methods=['POST'])
def return_url_code():
    long_link = request.form.get("long_link")
    link_key = lookup_url(long_link)
    if link_key is None:
        return 'None'
    else:
        return link_key


@app.route('/')
def go_add():
    return redirect('/add_link')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
