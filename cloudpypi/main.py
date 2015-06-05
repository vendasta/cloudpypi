import os
import logging
import base64

import jinja2
import webapp2
from webapp2_extras.routes import RedirectRoute
from webapp2_extras.security import generate_password_hash, check_password_hash
from webob import Request, Response

from google.appengine.api import users
from google.appengine.ext import ndb

import package_api

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class configuration(object):
    def __init__(self):
        self.fallback_url = "http://pypi.python.org/simple"
        self.bucket = "packages"
        self.redirect_to_fallback = True
        self.overwrite = False
        self.pepper = "7Y52g;ygCX_rK@$96qQ,"


config = configuration()


class UserPrefs(ndb.Model):
    username = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)

    def check_password(self, guess):
        return check_password_hash(guess, self.password, pepper=config.pepper)

    @classmethod
    def create_user(cls, username, password):
        password = generate_password_hash(password,
                                          method='sha1',
                                          length=22,
                                          pepper=config.pepper)
        user = cls(username=username, password=password)
        user.put()
        return user

    @classmethod
    def delete_user(cls, username):
        user = cls.lookup_user(username)
        user.key.delete()

    @classmethod
    def lookup_user(cls, username):
        return cls.query(cls.username == username).get()


class AuthenticationMiddleware(object):
    """
    Authenticate the current request. There are two authentication methods.
    1) AppEngine Users API:
        - If the user has visited using a browser they will be directed to the
          standard AppEngine login page.
    2) pip:
        - If a basic auth request is made from a User previously registered
          within the application.
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        """
        Authenticate using AppEngine users API or basic authentication.
        """
        request = Request(environ)
        user = users.get_current_user()

        # If we already have a browser based session, proceed
        if user:
            logging.info("App Engine user found: %s", user)
            response = request.get_response(self.app)
            return response(environ, start_response)
        else:
            # Prompt to login if no authorization header
            logging.info(
                "No App Engine user. Checking HTTP basic authentication.")
            if not request.authorization:
                logging.info("No Auth header")
                response = Response(status=302,
                                    location=users.create_login_url('/'))
                return response(environ, start_response)

            auth_type, credentials = request.authorization

            # If we are not basic auth, redirect to login screen
            if auth_type != "Basic":
                logging.info("Not basic auth!")
                response = Response(status=403)
                return response(environ, start_response)

            username, password = base64.b64decode(credentials).split(':')

            user = UserPrefs.lookup_user(username)
            if not user:
                logging.info("No user %s" % username)
                response = Response(status=403)
                return response(environ, start_response)

            if not user.check_password(password):
                logging.info("Wrong password %s" % username)
                response = Response(status=403)
                return response(environ, start_response)

            logging.info("Authenticated %s" % username)
            response = request.get_response(self.app)
            return response(environ, start_response)


class IndexHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({}))

    def post(self):
        try:
            action = self.request.params[':action']
        except KeyError:
            return self.abort(400, detail=":action field not found")

        if action != "file_upload":
            raise self.abort(400, detail="action not supported: %s" % action)

        try:
            content = self.request.params['content']
        except KeyError:
            raise self.abort(400, detail="content file field not found")

        if "/" in content.filename:
            raise self.abort(400, detail="bad filename")

        if not config.overwrite and package_api.exists(config.bucket,
                                                       content.filename):
            raise self.abort(409, detail="file already exists")

        package_api.write(config.bucket, content.filename, content.value)
        self.response.write("")


class SimpleIndexHandler(webapp2.RequestHandler):
    def get(self):
        prefixes = sorted(package_api.list_package_names(config.bucket))

        context = {'prefixes': prefixes}
        logging.info('Matching prefixes: %s', prefixes)
        template = JINJA_ENVIRONMENT.get_template('simple.html')
        self.response.write(template.render(**context))


class SimpleListHandler(webapp2.RequestHandler):
    def get(self, package):
        packages = sorted(package_api.list_packages(config.bucket, package))
        if not packages:
            if config.redirect_to_fallback:
                return self.redirect("%s/%s/" %
                                     (config.fallback_url.rstrip("/"),
                                      package))
            return self.abort(404)

        context = {
            'package': package,
            'packages': [
                {'url': webapp2.uri_for('packages',
                                        package=p),
                 'filename': p} for p in packages
            ],
        }
        template = JINJA_ENVIRONMENT.get_template('links.html')
        self.response.write(template.render(**context))


class PackageDownloadHandler(webapp2.RequestHandler):
    def get(self, package):
        self.response.headers['Content-Type'] = 'application/x-gzip'
        self.response.headers['Content-Disposition'] = 'attachment; filename=%s' % package  # noqa

        data = package_api.read(config.bucket, package)
        logging.info('Downloading %s' % package)
        self.response.write(data)


class UserIndexHandler(webapp2.RequestHandler):
    def get(self):
        users = UserPrefs.query().fetch()

        context = {
            'users': users,
            'user_delete_url': webapp2.uri_for('users-delete'),
            'user_create_url': webapp2.uri_for('users-create'),
        }
        template = JINJA_ENVIRONMENT.get_template('users.html')
        self.response.write(template.render(**context))


class UserCreateHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('users_create.html')
        self.response.write(template.render({}))

    def post(self):
        username = self.request.POST.get('username')
        if not username:
            return self.abort(400, detail="username is required.")
        password = self.request.POST.get('password')
        if not password:
            return self.abort(400, detail="Password is required.")

        UserPrefs.create_user(username=username, password=password)

        self.redirect_to("users")


class UserDeleteHandler(webapp2.RequestHandler):
    def post(self):
        username = self.request.POST.get('username')
        if not username:
            return self.abort(400, detail="username is required.")

        UserPrefs.delete_user(username)

        self.redirect_to("users")


app = webapp2.WSGIApplication([webapp2.Route("/",
                                             name='index',
                                             handler=IndexHandler),
                               RedirectRoute("/simple/",
                                             name="simple",
                                             handler=SimpleIndexHandler,
                                             strict_slash=True),
                               RedirectRoute("/simple/<package>/",
                                             name="simple-list",
                                             handler=SimpleListHandler,
                                             strict_slash=True),
                               RedirectRoute("/packages/<package>/",
                                             name="packages",
                                             handler=PackageDownloadHandler,
                                             strict_slash=True),
                               RedirectRoute("/users/",
                                             name="users",
                                             handler=UserIndexHandler,
                                             strict_slash=True),
                               RedirectRoute("/users/create/",
                                             name="users-create",
                                             handler=UserCreateHandler,
                                             strict_slash=True),
                               RedirectRoute("/users/delete/",
                                             name="users-delete",
                                             handler=UserDeleteHandler,
                                             strict_slash=True), ],
                              debug=True)
application = AuthenticationMiddleware(app)
