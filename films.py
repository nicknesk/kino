from sqlalchemy import Column, String, Integer, Text, Sequence, ForeignKey, Date
from sqlalchemy.dialects.postgresql import BYTEA, REAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import func
from datetime import datetime
from constants import *


Base = declarative_base()
#COMMENT_ID_SEQ = Sequence('user_id_seq')  # define sequence explicitly
#MOVIE_ID_SEQ = Sequence('movie_id_seq')


class User(Base):
    __tablename__ = 'users'
    login = Column(String(50), primary_key=True)
    password = Column(String(50))
    user_name = Column(String(50))
    email = Column(String(50))
    confirmation_code = Column(String(20))
    pending_password = Column(String(50))
    pending_user_name = Column(String(50))
    pending_email = Column(String(50))
    access = Column(Integer)

    def __init__(self, login, password, name, email, access, confirmation_code=None, pending_password=None,
                       pending_user_name=None, pending_email=None):
        self.login = login
        self.password = password
        self.user_name = name
        self.email = email
        self.confirmation_code = confirmation_code
        self.pending_password = pending_password
        self.pending_user_name = pending_user_name
        self.pending_email = pending_email
        self.access = access


class Movies(Base):
    __tablename__ = 'films'
    movie_id = Column(Integer, primary_key=True) #, server_default=MOVIE_ID_SEQ.next_value())
    name = Column(String)
    year = Column(Integer)
    director = Column(String)
    summary = Column(Text)
    trailer_link = Column(String)
    icon_file_name = Column(String)
    icon = Column(BYTEA)
    film_janre = Column(Integer)
    movie_type = Column(Integer)
    rating = Column(REAL)

    def __init__(self, name, year, director, summary, trailer_link,
                       icon_file_name, icon, film_janre, movie_type, rating):
        self.name = name
        self.year = year
        self.director = director
        self.summary = summary
        self.trailer_link = trailer_link
        self.icon_file_name = icon_file_name
        self.icon = icon
        self.film_janre = film_janre
        self.movie_type = movie_type
        self.rating = rating


class NewFilms(Base):
    __tablename__ = 'new_films'
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('films.movie_id'))  # This is the Movies.movie_id
    datetime = Column(Date)
    film = relationship(Movies, backref='new_films')

    def __init__(self, movie_id, datetime):
        self.movie_id = movie_id
        self.datetime = datetime


class Comments(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    author = Column(String)
    body = Column(Text)
    movie_id = Column(Integer, ForeignKey('films.movie_id'))
    date = Column(Date)
    film = relationship(Movies, backref='comments')

    def __init__(self, author, body, movie_id, datetime):
        self.author = author
        self.body = body
        self.datetime = datetime
        self.movie_id = movie_id



class Favorite(Base):
    __tablename__ = 'favorite'

    id = Column(Integer, primary_key=True)
    login = Column(String, ForeignKey('users.login'))
    movie_id = Column(Integer, ForeignKey('films.movie_id'))
    user = relationship(User)
    film = relationship(Movies)

    def __init__(self, login=None, movie_id=None):
        self.login = login
        self.movie_id = movie_id


class Films:
    def __init__(self, session):
        self.__session = session

    def __del__(self):
        self.__session.close()

    def __maybe_write_icon(self, id, icon_file_name):
        """ Check if icon exists in 'img' folder, if not write the icon"""
        path_to_icon = 'assets/img/'
        path_to_icon += icon_file_name
        try:
            with open(path_to_icon, 'rb') as file:
                return
        except FileNotFoundError as exp:
            film = self.__session.query(Movies.icon).filter(Movies.movie_id == id).one()
            with open(path_to_icon, 'wb') as file:
                file.write(film.icon)

    def get_new_films_or_movie_series(self, film_type, icon_path, lines_count):
        films = self.__session.query(NewFilms.id, Movies.movie_id, Movies.name, Movies.icon_file_name).\
               join(Movies).filter(Movies.movie_type == film_type).order_by(NewFilms.datetime.desc()).limit(lines_count)

   #     films = self.__session.query(Movies.movie_id, Movies.name, Movies.icon_file_name).filter(Movies.movie_type == film_type).all()
        new_films = []
        count = 0
        for film in films:
            new_films.append((count, film.movie_id, film.name, icon_path + film.icon_file_name))
            self.__maybe_write_icon(film.movie_id, film.icon_file_name)
            count += 1
        return new_films

    def get_films_list(self, film_type, current_page, films_per_page, icon_path):
        films_count = self.__session.query(func.count(Movies.movie_id)).filter(Movies.movie_type == film_type).scalar()
        films = self.__session.query(Movies.movie_id, Movies.name, Movies.year,
                                   Movies.director, Movies.summary, Movies.icon_file_name).\
                                   filter(Movies.movie_type == film_type).limit(films_per_page).\
                                   offset((current_page-1)*films_per_page)
        results = list()
        for film in films:
            self.__maybe_write_icon(film.movie_id, film.icon_file_name)
            results.append((film.movie_id, film.name, film.year, film.director,
                            film.summary, icon_path + film.icon_file_name))
        return results, films_count

    def get_top_rating_list(self, count, film_type):
        films = self.__session.query(Movies.movie_id, Movies.name, Movies.rating).\
                      filter(Movies.movie_type == film_type).\
                      order_by(Movies.rating.desc()).limit(count)
        result = []
        for film in films:
            result.append((film.movie_id, film.name, '{0:.2f}'.format(film.rating)))
        return result

    def get_rating_list(self, film_type, curr_page):
        films_count = self.__session.query(func.count(Movies.movie_id)).filter(Movies.movie_type == film_type).scalar()
        films = self.__session.query(Movies.movie_id, Movies.name, Movies.year,
                                     Movies.icon_file_name, Movies.rating).\
                               filter(Movies.movie_type == film_type). \
                               order_by(Movies.rating.desc()).limit(MAX_LINES_IN_RATING_PAGE).\
                               offset((curr_page-1)*MAX_LINES_IN_RATING_PAGE)
        rating_list = []
        for film in films:
            self.__maybe_write_icon(film.movie_id, film.icon_file_name)
            rating_list.append((film.movie_id, film.name, film.year,
                                ICON_PATH+film.icon_file_name, '{0:.2f}'.format(film.rating)))
        return films_count, rating_list

    def search(self, chunk, current_page):
        search_string = '%{}%'.format(chunk.upper())
        films_count = self.__session.query(func.count(Movies.movie_id)). \
                                          filter(func.upper(Movies.name).like(search_string)).scalar()

        films = self.__session.query(Movies.movie_id, Movies.name, Movies.year,
                                     Movies.director, Movies.summary, Movies.icon_file_name).\
                               filter(func.upper(Movies.name).like(search_string)). \
                               limit(MAX_FILMS_PER_PAGE).offset((current_page - 1) * MAX_FILMS_PER_PAGE)
        results = []
        for film in films:
            self.__maybe_write_icon(film.movie_id, film.icon_file_name)
            results.append((film.movie_id, film.name, film.year, film.director,
                            film.summary, ICON_PATH + film.icon_file_name))
        return results, films_count


    def film_info(self, film_id):
        film = self.__session.query(Movies.name, Movies.year, Movies.director, Movies.summary,
                                  Movies.trailer_link, Movies.icon_file_name, Movies.rating).\
                    filter(Movies.movie_id == film_id).all()
        return film

    def add_comment(self, author, body,  movie_id):
        comment = Comments(author, body, movie_id, datetime.today())
        self.__session.add(comment)
        self.__session.commit()

    def get_comments(self, movie_id):
        comments = self.__session.query(Comments.author, Comments.body).\
                        filter(Comments.movie_id == movie_id).all()
        return comments

    def is_favorite(self, login, movie_id):
        if not login:
            return False
        id = self.__session.query(Favorite.id).filter(Favorite.login == login, Favorite.movie_id == movie_id).scalar()
        if id:
            return True
        else:
            return False

    def toggle_favorite(self, login, movie_id):
        if not login:
            return None
        id = self.__session.query(Favorite.id).filter(Favorite.login == login, Favorite.movie_id == movie_id).scalar()
        if id:
            self.__session.query(Favorite).filter(Favorite.id == id).delete()
        else:
            self.__session.add(Favorite(login, movie_id))
        self.__session.commit()


    def insert_film(self, name, year, director, summary, trailer_link,
                         icon_file_name, icon, film_janre, movie_type, rating):
        film = Movies(name, year, director, summary, trailer_link,
                      icon_file_name, icon, film_janre, movie_type, rating)
        self.__session.add(film)
        self.__session.commit()

    def data_to_insert(self):
        name = 'Во все тяжкие'
        year = 2008
        director = 'Мишель МакЛарен'
        summary = """
        Школьный учитель химии Уолтер Уайт узнаёт, что болен раком лёгких. Учитывая сложное финансовое состояние дел семьи,
         а также перспективы, Уолтер решает заняться изготовлением метамфетамина. Для этого он привлекает своего бывшего ученика 
         Джесси Пинкмана, когда-то исключённого из школы при активном содействии Уайта. Пинкман сам занимался «варкой мета»,
          но накануне, в ходе рейда УБН, он лишился подельника и лаборатории…
                 """
        trailer_link = 'https://www.youtube.com/embed/tRT3bAINsjE'
        icon_file = 'breakingbad.png'
        with open('assets/img/breakingbad.png', 'rb') as f:
            icon = f.read()
        film_janre = 1
        movie_type = 1
        rating = 8.86
        self.insert_film(name, year, director, summary, trailer_link,
                         icon_file, icon, film_janre, movie_type, rating)

    def save_icons(self, path):
        films = self.__session.query(Movies)
        for film in films:
            with open(path+film.icon_file_name, 'rb') as f:
                film.icon = f.read()
        self.__session.commit()



