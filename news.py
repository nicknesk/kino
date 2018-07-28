from sqlalchemy import Column, String, Integer, Text, Sequence, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import func

Base = declarative_base()

class NewsFeed(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    header = Column(Text)
    body = Column(Text)
    date = Column(Date)
    type = Column(Integer)

    def __init__(self, header, body, date, news_type):
        self.header = header
        self.body = body
        self.date = date
        self.type = news_type


class News:
    def __init__(self, session):
        self.session = session

    def get_news_feed_headers(self, max_lines, offset, news_type):
        return self.session.query(NewsFeed.id, NewsFeed.date, NewsFeed.header).filter(NewsFeed.type == news_type).\
                                 order_by(NewsFeed.date.desc()).limit(max_lines).offset((offset-1)*max_lines)

    def get_feed_length(self, news_type):
        return self.session.query(func.count(NewsFeed.id)).filter(NewsFeed.type == news_type).scalar()

    def get_news(self, id):
        return self.session.query(NewsFeed.type, NewsFeed.date, NewsFeed.header, NewsFeed.body).\
                                 filter(NewsFeed.id == id).one()
