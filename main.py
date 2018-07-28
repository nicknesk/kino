#!/usr/bin/env python

import os
import tornado.httpserver
import tornado.httpclient
import tornado.auth
import tornado.simple_httpclient
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.template
import tornado.gen
import tornado.locale
import uimodule
from tornado.options import define, options

import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from users_database import UsersDatabase
from films import Films
from news import News

from constants import *
import pagination
from text_to_bits_convert import *
from gmail import send_email

LOCAL = False
DEBUG = False

def hash(password):
# TODO: write code to hash the password
    return password


def random_string():
    rand_chr = []
    for i in range(15):
        rand_chr.append(chr(random.randint(65, 90)+32*random.randint(0, 1)))
    return "".join(rand_chr)


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db_engine(self):
        if not self.application._db_engine:
            self.application._db_engine = create_engine(CONN_STRING_REMOTE, pool_size=50, max_overflow=0,
                                                                            pool_timeout=5, pool_recycle=3600)
        return self.application._db_engine

    @property
    def session(self):
        if not hasattr(BaseHandler, '_session'):
            Session = sessionmaker()
            Session.configure(bind=self.db_engine)
            BaseHandler._session = Session()
        return BaseHandler._session

    @property
    def films(self):
        if not hasattr(BaseHandler, '_films'):
            BaseHandler._films = Films(self.session)
        return BaseHandler._films

    @property
    def users(self):
        if not hasattr(BaseHandler, '_users'):
            BaseHandler._users = UsersDatabase(self.session)
        return BaseHandler._users

    @property
    def news(self):
        if not hasattr(BaseHandler, '_news'):
            BaseHandler._news = News(self.session)
        return BaseHandler._news

    def check_credentials(self, login, password):
        if hash(password) == self.users.get_password(login):
            self.set_secure_cookie('login', login)
            self.set_cookie('login_status', 'OK')
        else:
            self.clear_cookie('login')
            self.set_cookie('login_status', 'error')

    def authorization_required(self):
        required = self.get_cookie('authorization')
        if not required:
            return False
        else:
            self.clear_cookie('authorization')
            return True

    def get_current_user(self):
        login = self.get_secure_cookie('login')
        return tornado.escape.xhtml_escape(login) if login else None

    def get_user_locale(self):
        if self.get_cookie('locale'):
            return tornado.locale.get(tornado.escape.xhtml_escape(self.get_cookie('locale')))
        browser_locale = self.get_browser_locale()
        if browser_locale.code == 'ru_RU':
            self.set_cookie('locale', 'ru_RU')
            return tornado.locale.get('ru_RU')
        else:
            self.set_cookie('locale', 'en_US')
            return tornado.locale.get('en_US')

    def toggle_locale(self):
        lang = tornado.escape.xhtml_escape(self.get_cookie('locale'))
        if lang == 'ru_RU':
            self.set_cookie('locale', 'en_US')
        else:
            self.set_cookie('locale', 'ru_RU')

    def get_locale_code(self):
        if self.get_cookie('locale'):
            return tornado.escape.xhtml_escape(self.get_cookie('locale'))
        browser_local = self.get_browser_locale()
        if browser_local.code == 'ru_RU':
            return 'ru_RU'
        else:
            return 'en_US'

    def get_current_user_name(self):
        login = self.get_current_user()
        return self.users.get_user_name(login) if login else None

    def get_current_user_access(self):
        login = self.get_current_user()
        return self.users.get_user_access(login) if login else None

    def get_login_status(self):
        status = self.get_cookie('login_status')
        if not status:
            return ''
        else:
            self.clear_cookie('login_status')
            return tornado.escape.xhtml_escape(status)

    def save_user_and_send_email_confirmation(self, login, password, name, email, access):
        rnd_str = random_string()
        if send_email(email, rnd_str):
            self.users.save_user(login, hash(password), name, email, access, rnd_str)

    def validate_sign_up_input(self, login, name, email, password, password_confirm):
        link_to_redirect = '/signin?status='
        if password != password_confirm:
            link_to_redirect += 'error&message=passwords_doesnt_match'
            return False, link_to_redirect
        elif self.users.user_exists(login, email):
            link_to_redirect += 'error&message=user_exists'
            return False, link_to_redirect
        else:
            link_to_redirect += 'success&message=email_confirmation_sent'
            return True, link_to_redirect

    def redirected_from_paginator_handler(self):
        if self.get_cookie('paginator_redirect'):
            self.clear_cookie('paginator_redirect')
            return True
        else:
            return False

    def get_paginator_status(self):
        if self.get_cookie('page_pgn_offset'):
            return self.get_cookie('page_pgn_offset')
        else:
            return '1'

    def save_page_status(self, url, page_parameter, page_pgn_offset):
        self.set_cookie('url', url)
        if page_parameter:
            self.set_cookie('parameter', text_to_bits(page_parameter))
        else:
            self.clear_cookie('parameter')
        if page_pgn_offset:
            self.set_cookie('page_pgn_offset', str(page_pgn_offset))
        else:
            self.clear_cookie('page_pgn_offset')

    def retrieve_from_cookies(self):
        return text_from_bits(self.get_cookie('parameter')), self.get_cookie('page_pgn_offset')

    def get_cinema_news_curr_page(self):
        try:
            return tornado.escape.xhtml_escape(self.get_cookie('layout_pager_page'))
        except TypeError:
            self.set_cookie('layout_pager', '1')
            return '1'

    def layout_content(self):
        content = {}
        content['current_user_name'] = self.get_current_user_name()
        content['rating_page'] = False
        content['login_status'] = self.get_login_status()
        content['local'] = self.get_locale_code()
        content['authorization_required'] = self.authorization_required()
        content['layout_pager'] = pagination.pager(int(self.get_cinema_news_curr_page()),
                                                   pagination.pages_count(self.news.get_feed_length(CINEMA_NEWS_TYPE),
                                                   MAX_LINES_IN_NEWS_FEED))
        content['news_feed'] = self.news.get_news_feed_headers(MAX_LINES_IN_NEWS_FEED,
                                                               int(self.get_cinema_news_curr_page()),
                                                               CINEMA_NEWS_TYPE)
        content['top_rating_films'] = self.films.get_top_rating_list(MAX_LINES_IN_TOP_RATING_LIST, FILM_TYPE)
        content['top_rating_movie_series'] = self.films.get_top_rating_list(MAX_LINES_IN_TOP_RATING_LIST,
                                                                            MOVIE_SERIES_TYPE)
        return content

    def index_content(self):
        content = self.layout_content()
        content['new_films'] = self.films.get_new_films_or_movie_series(FILM_TYPE, ICON_PATH, 8)
        content['new_movie_series'] = self.films.get_new_films_or_movie_series(MOVIE_SERIES_TYPE, ICON_PATH, 8)
        return content

    def show_content(self, film_id):
        content = self.layout_content()
        content['film_id'] = film_id
        content['favorite'] = self.films.is_favorite(self.get_current_user(), film_id)
        content['film_info'] = self.films.film_info(film_id)
        content['comments'] = self.films.get_comments(film_id)
        return content

    def films_content(self, film_type, current_page):
        content = self.layout_content()
        films_list, films_count = self.films.get_films_list(int(film_type),
                                                            int(current_page),
                                                            MAX_FILMS_PER_PAGE, ICON_PATH)
        content['film_type'] = str(film_type)
        content['films_list'] = films_list
        content['paginator'] = pagination.paginator(int(current_page),
                                                    pagination.pages_count(films_count, MAX_FILMS_PER_PAGE))
        return content

    def search_content(self, chunk, current_page):
        content = self.layout_content()
        films_list, films_count = self.films.search(chunk, current_page)
        content['chunk'] = chunk
        content['films_list'] = films_list
        content['paginator'] = pagination.paginator(current_page, pagination.pages_count(films_count, MAX_FILMS_PER_PAGE))
        return content

    def news_content(self, news_id):
        content = self.layout_content()
        news_type, date, header, body = self.news.get_news(int(news_id))
        content['news_type'] = str(news_type)
        content['news_date'] = date
        content['news_header'] = header
        content['news_body'] = body
        return content

    def rating_content(self, film_type):
        content = self.layout_content()
        current_page = int(self.get_paginator_status())
        rating_list_len, rating_list = self.films.get_rating_list(int(film_type), current_page)
        content['film_type'] = str(film_type)
        content['rating_page'] = True
        content['paginator'] = pagination.paginator(current_page,
                                                    pagination.pages_count(rating_list_len, MAX_LINES_IN_RATING_PAGE))
        content['rating_list'] = rating_list
        return content


class MainHandler(BaseHandler):
    def get(self):
        if not self.redirected_from_paginator_handler():
            self.save_page_status('/', None, None)
        self.render('index.html', content=self.index_content())


class ViewHandler(BaseHandler):
    def get(self):
        if self.redirected_from_paginator_handler():
            movie_id, paginator_current_page = self.retrieve_from_cookies()
        else:
            movie_id = self.get_argument('id')
        self.save_page_status('/view', movie_id, None)
        self.render('show.html', content=self.show_content(movie_id))

    def post(self):
        movie_id = self.get_argument('id')
        body = self.get_argument('comment_body')
        self.films.add_comment(self.get_current_user_name(), body, movie_id)
        self.redirect('/view?id=' + movie_id)


class FavoriteHandler(BaseHandler):
    def get(self):
        movie_id = self.get_argument('id')
        self.films.toggle_favorite(self.get_current_user(), movie_id)
        self.redirect('/view?id=' + movie_id)


class FilmsHandler(BaseHandler):
    def get(self):
        if self.redirected_from_paginator_handler():
            film_type, paginator_current_page = self.retrieve_from_cookies()
        else:
            film_type = self.get_argument('film_type')
            paginator_current_page = '1'
            try:
                paginator_current_page = int(self.get_argument('curr_page'))
            except tornado.web.HTTPError:
                pass
        self.save_page_status('/films', film_type, paginator_current_page)
        self.render('films.html', content=self.films_content(film_type, paginator_current_page))


class ContactHandler(BaseHandler):
    def get(self):
        if not self.redirected_from_paginator_handler():
            self.save_page_status('/contact', None, None)
        self.render('contact.html', content=self.layout_content())


class RatingHandler(BaseHandler):
    def get(self):
        if self.redirected_from_paginator_handler():
            film_type, paginator_current_page = self.retrieve_from_cookies()
        else:
            paginator_current_page = '1'
            film_type = self.get_argument('film_type')
        self.save_page_status('/rating', film_type, paginator_current_page)
        self.render('rating.html', content=self.rating_content(film_type))


class AboutHandler(BaseHandler):
    def get(self):
        # demo download blocking
        file_name = 'Igra_v_imitaciu_2014_BDRip_by_Dalemake.avi'
        buf_size = 16384
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
        with open('assets/img/'+file_name, 'rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)
                self.flush()
        self.finish()


class CredentialsHandler(BaseHandler):
    def get(self):
        self.set_cookie('authorization', 'required')
        self.redirect('/paginator?curr_page='+self.get_paginator_status())


class SignUpHandler(BaseHandler):
    def get(self):
        if not self.redirected_from_paginator_handler():
            self.save_page_status('/signin', None, None)
        try:
            status = self.get_argument('status')
            message = self.get_argument('message')
        except tornado.web.HTTPError:
            status = None
            message = None
        self.render('checkin.html', content=self.layout_content(),
                    status=status, message=message)

    def post(self):
        login = self.get_argument('login')
        name = self.get_argument('name')
        email = self.get_argument('email')
        password = self.get_argument('password')
        password_confirm = self.get_argument('password_confirm')
        correct, link = self.validate_sign_up_input(login, name, email, password, password_confirm)
        if correct:
            self.save_user_and_send_email_confirmation(login, hash(password), name, email, PERMISSION_USER)
        self.redirect(link)


class CheckCredentialsHandler(BaseHandler):
    def get(self):
        self.clear_all_cookies('login')
        self.redirect('/')

    def post(self):
        try:
            login = self.get_argument("login")
            password_entered = self.get_argument("password")
            self.check_credentials(login, password_entered)
        except tornado.web.HTTPError:
            self.clear_cookie('login')
        finally:
            self.redirect('/paginator?curr_page='+self.get_paginator_status())


class SearchHandler(BaseHandler):
    def get(self):
        if self.redirected_from_paginator_handler():
            chunk, current_page = self.retrieve_from_cookies()
        else:
            chunk = self.get_argument('chunk')
            current_page = self.get_argument('curr_page')
            self.save_page_status('/search', chunk, str(current_page))
        self.render('search.html', content=self.search_content(str(chunk), int(current_page)))

    def post(self):
        chunk = self.get_argument("chunk")
        self.redirect('/search?chunk={}&curr_page=1'.format(chunk))


class VerifyHandler(BaseHandler):
    def get(self):
        try:
            confirmation_string = self.get_argument('q')
            self.users.confirm_user_profile_updates(confirmation_string)
        except tornado.web.HTTPError as err:
            print(err)
        finally:
            self.redirect('/')


class NewsPaginatorHandler(BaseHandler):
    def get(self):
        try:
            curr_page = self.get_argument('pager_page')
        except tornado.web.HTTPError:
            curr_page = '1'
        self.set_cookie('paginator_redirect', 'news_pagination_handler')
        self.set_cookie('layout_pager_page', curr_page)
        self.redirect(tornado.escape.xhtml_escape(self.get_cookie('url')))


class ReadNewsHandler(BaseHandler):
    def get(self):
        if self.redirected_from_paginator_handler():
            news_id, pager_page = self.retrieve_from_cookies()
        else:
            news_id = self.get_argument('news_id')
        self.save_page_status('/news', news_id, None)
        self.render('read_news.html', content=self.news_content(news_id))


class Paginator(BaseHandler):
    def get(self):
        try:
            curr_page = self.get_argument('curr_page')
        except tornado.web.HTTPError:
            curr_page = '1'
        self.set_cookie('paginator_redirect', 'news_pagination_handler')
        self.set_cookie('page_pgn_offset', curr_page)
        self.redirect(tornado.escape.xhtml_escape(self.get_cookie('url')))


class DownloadHendler(BaseHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        filename = self.get_argument('filename')
        url = 'http://localhost:8000/?filename=' + filename
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + filename)
        self.flush()

        # Async streaming
        def streaming_callback(chunk):
            self.write(chunk)
            self.flush()

        client = tornado.simple_httpclient.AsyncHTTPClient(max_body_size=10485760000)
        yield client.fetch(tornado.httpclient.HTTPRequest(url, request_timeout=1000,
                           streaming_callback=streaming_callback))
        self.finish('OK')


class UploadHendler(BaseHandler):
    @tornado.web.authenticated
    def get(self, args=None):
        if not self.redirected_from_paginator_handler():
            self.save_page_status('/upload', None, None)
        if args:
            filename = args[0]
            status = args[1]
            err_mess = args[2]
        else:
            status = None
            filename = None
            err_mess = None
        self.render('upload.html', content=self.layout_content(), status=status, file=filename, err_mess=err_mess)

    @tornado.web.authenticated
    def post(self):
        fileinfo = self.request.files['filearg'][0]
        fname = fileinfo['filename']
        try:
            with open(UPLOADS_PATH + fname, 'wb') as fh:
                fh.write(fileinfo['body'])
            self.get([fname, 'OK', ''])
        except Exception as err:
            self.get([fname, 'error', err])


class ToggleLangHandler(BaseHandler):
    def get(self):
        self.toggle_locale()
        self.redirect('/paginator?curr_page=' + self.get_paginator_status())


class TwitterLoginHandler(BaseHandler,
                          tornado.auth.TwitterMixin):
        @tornado.gen.coroutine
        def get(self):
            if self.get_argument("oauth_token", None):
                user = yield self.get_authenticated_user()
                # Save the user using e.g. set_secure_cookie()
                if not user:
                    self.clear_all_cookies()
                    self.set_cookie('login_status', 'error')
                    self.redirect('/')
                self.set_secure_cookie('user_id', str(user['id']))
                self.set_secure_cookie('oauth_token', user['access_token']['key'])
                self.set_secure_cookie('oauth_secret', user['access_token']['secret'])
                self.set_cookie('login_status', 'twitter')
                self.set_secure_cookie('login', str(user['id']))
                self.users.maybe_add_user(str(user['id']), str(user['name']), 'twitter')
                self.redirect('/paginator?curr_page=' + self.get_paginator_status())
            else:
                yield self.authorize_redirect()


class FacebookGraphLoginHandler(BaseHandler,
                                tornado.auth.FacebookGraphMixin):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument("code", False):
            user = yield self.get_authenticated_user(
                                                      redirect_uri=self.settings["facebook_redirect"],
                                                      client_id=self.settings["facebook_api_key"],
                                                      client_secret=self.settings["facebook_secret"],
                                                      code=self.get_argument("code")
                                                       )

            # Save the user with e.g. set_secure_cookie
            self.set_secure_cookie('user_id', str(user['id']))
            self.set_cookie('login_status', 'facebook')
            self.set_secure_cookie('login', str(user['id']))
            self.users.maybe_add_user(str(user['id']), str(user['first_name']), 'facebook')
            self.redirect('/paginator?curr_page=' + self.get_paginator_status())
        else:
           yield self.authorize_redirect(
                                          redirect_uri=self.settings["facebook_redirect"],
                                          client_id=self.settings["facebook_api_key"],
                                          extra_params={"scope": "public_profile"}
                                        )


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler),
                    (r"/home", MainHandler),
                    (r"/about", AboutHandler),
                    (r"/view", ViewHandler),
                    (r"/view/toggle_favorite", FavoriteHandler),
                    (r"/films", FilmsHandler),
                    (r"/rating", RatingHandler),
                    (r"/contact", ContactHandler),
                    (r"/login", CredentialsHandler),
                    (r"/auth", CheckCredentialsHandler),
                    (r"/search", SearchHandler),
                    (r"/signin", SignUpHandler),
                    (r"/verify", VerifyHandler),
                    (r"/paginator", NewsPaginatorHandler),
                    (r"/news", ReadNewsHandler),
                    (r"/paginator/general", Paginator),
                    (r"/download", DownloadHendler),
                    (r"/upload", UploadHendler),
                    (r"/toggle_lang", ToggleLangHandler),
                    (r"/twitter_login", TwitterLoginHandler),
                    (r"/facebook_login", FacebookGraphLoginHandler),
                    (r'/(favicon\.ico)', tornado.web.StaticFileHandler, {'path': 'assets/'})]

        settings = dict(template_path=os.path.join(os.path.dirname(__file__), 'assets/templates'),
                        static_path=os.path.join(os.path.dirname(__file__), 'assets'),
                        xsrf_cookies=True,
                        cookie_secret="ncdYhd@cb9sqkkG1d?GBlkn3ahQf#_jd",
                        login_url="/login",
                        debug=True,
                        ui_modules=uimodule,
                        twitter_consumer_key="RkuZuGLLL9gkSwxghTiP075OH",
                        twitter_consumer_secret="efHha2hBspxVjeL9zqhh4PcVbF7MHjrJTDTETKjJIlGA3EXAYo",
                        facebook_api_key="252820041885243",
                        facebook_secret="840c964f84de9c907dd1d4fdc78da84b",
                        facebook_redirect=LOCAL_URI_REDIRECT if LOCAL else REMOTE_URI_REDIRECT
                        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self._db_engine = create_engine(CONN_STRING_REMOTE, pool_size=50, max_overflow=0,
                                                            pool_timeout=5, pool_recycle=3600)



def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    translationsPath = os.path.join(os.path.dirname(__file__), 'assets/local')
    tornado.locale.load_translations(translationsPath)

    define("port", default=5000, help="run on the given port", type=int)
    options.parse_command_line()
    port = options.port if LOCAL else int(os.environ.get("PORT", 5000))
    print(port)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
