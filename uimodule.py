import tornado.web


class Rating(tornado.web.UIModule):
    def render(self, block_header, top_ratings):   # rating_list):
        return self.render_string('top_rating.html', block_header=block_header, ratings=top_ratings)


class FilmBlock(tornado.web.UIModule):
    def render(self, id, name, file_name):
        return self.render_string('film_block.html', id=id, name=name, file_name=file_name)


class Favorite(tornado.web.UIModule):
    def render(self, favorite, film_id):
        return self.render_string('favorite.html', favorite=favorite, film_id=film_id)


class NewsFeed(tornado.web.UIModule):
    def render(self, pager, news):
        return self.render_string('news_feed.html', pager=pager, news=news)


class Paginator(tornado.web.UIModule):
    def render(self, paginator):
        return self.render_string('paginator.html', paginator=paginator)


class ModalWindow(tornado.web.UIModule):
    def render(self, title, body):
        return self.render_string('modal.html', title=title, body=body)


class ModalWindowLogIn(tornado.web.UIModule):
    def render(self):
        return self.render_string('modal_login.html')


class ModalWindowLogOut(tornado.web.UIModule):
    def render(self):
        return self.render_string('modal_logout.html')
