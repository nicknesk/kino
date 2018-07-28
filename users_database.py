from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import or_

Base = declarative_base()


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
    third_party_auth = Column(String(10))

    def __init__(self, login, password, name, email=None, access=16, confirmation_code=None, pending_password=None,
                       pending_user_name=None, pending_email=None, third_party_auth=None):
        self.login = login
        self.password = password
        self.user_name = name
        self.email = email
        self.confirmation_code = confirmation_code
        self.pending_password = pending_password
        self.pending_user_name = pending_user_name
        self.pending_email = pending_email
        self.access = access
        self.third_party_auth = third_party_auth


class UsersDatabase:
    def __init__(self, session):
        self.session = session

    def save_user(self, login, hash_password, name, email, access, confirmation_code):
        user = User(login, None, name, email, access, confirmation_code, hash_password)
        self.session.add(user)
        self.session.commit()

    def user_exists(self, login, email):
        user = self.session.query(User).filter(or_(User.login == login, User.email == email)).first()
        if user:
            return True
        else:
            return False

    def get_password(self, login):
        return self.session.query(User.password).filter(User.login == login).scalar()

    def confirm_user_profile_updates(self, confirmation_code):
        try:
            user = self.session.query(User).filter(User.confirmation_code == confirmation_code).one()
        except Exception as err:
            print("Duplicated confirmation_code: ", confirmation_code)
            print(err)
            return False
        if user:
            user.confirmation_code = None
            if user.pending_password:
                user.password = user.pending_password
                user.pending_password = None
            if user.pending_email:
                user.email = user.pending_email
                user.pending_email = None
            if user.pending_user_name:
                user.user_name = user.pending_user_name
                user.pending_user_name = None
            self.session.commit()
            return True

    def get_user_name(self, login):
        return self.session.query(User.user_name).filter(User.login == login).scalar()

    def get_user_access(self, login):
        return int(self.session.query(User.access).filter(User.login == login).scalar())

    def maybe_add_user(self, login, name, third_party_auth):
        user = self.session.query(User).filter(User.login == login, third_party_auth == User.third_party_auth).first()
        if user: return
        user = User(login, None, name)
        user.third_party_auth = third_party_auth
        self.session.add(user)
        self.session.commit()
