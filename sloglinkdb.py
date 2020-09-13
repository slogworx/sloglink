from sqlalchemy import Column, String, Integer, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from cred_crypto import load_text, cred_crypto
from datetime import datetime

Base = declarative_base()


class Sloglink(Base):
    __tablename__ = 'slog_links'

    id = Column(Integer, primary_key=True)
    link_key = Column(String, index=True, unique=True)
    long_link = Column(String, index=True, unique=True)
    created = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Sloglink(link_key=%s, long_link=%s)>" % (self.link_key, self.long_link)


def connect():
    # These need to be changed to what was created with cred_crypto.py
    text = load_text('.dev.creds')
    key = load_text('.dev.key')
    url = cred_crypto(text, key, 'decrypt').decode(encoding='utf-8')

    engine = create_engine(url, echo=False)  # May need to add "client_encoding='utf-8'" as an argument. 
    Session = sessionmaker(bind=engine)

    return Session()


if __name__ == "__main__":
    pass
