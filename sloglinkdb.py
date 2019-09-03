from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cred_crypto import load_text, cred_crypto
from datetime import datetime

Base = declarative_base()


class Sloglink(Base):
    __tablename__ = 'slog_links'

    id = Column(Integer, primary_key=True)
    linkstr = Column(String, index=True, unique=True)
    long_link = Column(String, index=True, unique=True)
    created = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)
    create_ip = Column(String, index=True)

    def __repr__(self):
        return "<Sloglink(linkstr=%s, long_link=%s)>" % (self.linkstr, self.long_link)


def connect():
    # Retrieve and decrypt the PostgreSQL connection url
    text = load_text('.yt.creds')    # chmod these to 600!
    key = load_text('.yt.creds.key')
    url = cred_crypto(text, key, 'decrypt').decode(encoding='utf-8')

    engine = create_engine(url, client_encoding='utf-8', echo=False)
    Session = sessionmaker(bind=engine)

    return Session()
