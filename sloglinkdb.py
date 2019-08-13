from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cred_crypto import load_text, cred_crypto
from datetime import datetime

Base = declarative_base()


class Sloglink(Base):
    __tablename__ = 'slog_links'

    id = Column(Integer, primary_key=True)
    ref = Column(String, index=True)
    url = Column(String)
    created = Column(DateTime, index=True, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Sloglink(ref=%s, url=%s)>" % (
            self.ref, self.url)


def connect():
    # Retrieve and decrypt the PostgreSQL connection url
    text = load_text('creds')    # chmod these to 600!
    key = load_text('creds.key')
    url = cred_crypto(text, key, 'decrypt').decode(encoding='utf-8')

    engine = create_engine(url, client_encoding='utf-8', echo=True)
    Session = sessionmaker(bind=engine)

    return Session()
