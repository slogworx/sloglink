# slog.link
Link shortener service using NGINX + WSGI + Flask + SQLAlchemy.

## Quick Setup

shell:~$ python3 -m venv sloglink_venv
shell:~$ source sloglink_venv/bin/activate
shell:~$ pip install -r requirements.txt

NOTE: sloglink utilizes SQLAlchemy, and may require that you install an adapter for your flavor of database.

Run cred_crypto.py from the command line.

shell:~$ python3 cred_crypto.py

 The script will ask you for the filename in which you would like to store your key, as well as the file to store your credentials. Once they're created, you have to manually edit sloglinkdb.py and setup_db.py to reference the files you created.

Some may be annoyed by having to create a key and encrypt/decrypt credentials, those people are free to rewrite the code to avoid it. I personally believe it it makes the credentials more difficult to obtain for an intruder unfamiliar with the code, but more importantly it protects against accidental viewing from anyone that may have access to the directory.

Next you will need to create the sloglink tables using the SQLAlchemy engine.

shell:~$ python3 setup_db.py

If you receive the message that the database tables have been created, then you are all set. You just need to make sure nginx and wsgi are installed and configured for the site. You will probably want to configure the app as a service, which should run it via your virtual environment (e.g. /home/user/sloglink_venv/bin/uwsgi --ini /home/user/sloglink/sloglink.ini)
