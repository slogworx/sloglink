import sloglinkdb
from cred_crypto import load_text, cred_crypto
from sqlalchemy import create_engine

# These need to be changed to what was created with cred_crypto.py
text = load_text('.dev.creds')
key = load_text('.dev.key')
url = cred_crypto(text, key, 'decrypt').decode(encoding='utf-8')

engine = create_engine(url, echo=False)
sloglinkdb.Base.metadata.create_all(engine)

print('The database tables have been created!')