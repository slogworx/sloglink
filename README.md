# slog.link
Link shortener service using NGINX + WSGI + Flask + SQLAlchemy.

Setup and configure your server to use NGINX, WSGI, Flask, SQLAlchemy, your favorite database, and your Python 3 virtual environment (It's not as daunting as it seems, and you can use duckduckgo.com to search for documentation if you're not sure how to do one or all of those things).

Run cred_crypto.py from the command line once the sloglink code has been extracted. The script will help you create a new key and use that key to encrypt your login string. It stores them in the files you name. Once they're created, you have to manually edit sloglinkdb.py to use these filenames in order for authentication to work with your database.

Some may be annoyed by having to create a key and encrypt credentials. Those people are free to re-write the code to avoid it. It would be easy to do, but I don't recommend it. Yes, the key is stored right beside the login string. The extra layer of encryption isn't just to make it more difficult to get at the credentials, it's to create a setup where developers helping you would need access and willfully have to decrypt the connection string to access the database. 

Once you complete all the things above, setup sloglink as a service on your virtual host (use duckduckgo.com to search on how to do this if you're not sure).
