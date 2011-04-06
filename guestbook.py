import re
import os
import cgi
import datetime
import wsgiref.handlers
import uuid
import hashlib
import logging

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Greeting(db.Model):
  author = db.StringProperty()
  content = db.TextProperty()
  date = db.DateTimeProperty(auto_now_add=True)

class User(db.Model):
  email = db.EmailProperty()
  password = db.StringProperty()
  name = db.StringProperty()
  salt = db.StringProperty()

class MainPage(webapp.RequestHandler):
  def get(self):
    MESSAGES = {
        'regSuccessful': 'You are successfully registered.',
        'loginSuccessful': ''
    }
    ERROR_MESSAGES = {
        'tooLongValue': 'Your message is too long.',
        'emptyField': 'Message can\'t be empty.',
    }

    user = self.__userName()
    
    greetings_query = Greeting.all().order('-date')
    greetings = greetings_query.fetch(10)

    template_values = {
      'greetings': greetings,
      'message': MESSAGES.get(self.request.get('message')),
      'error': ERROR_MESSAGES.get(self.request.get('error')),
      'user': user
      }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    self.content = self.request.get('content')

    error = self.__error()
    if error:
      self.redirect('/?error=' + error)

    else:
      user = self.__userName()
      greeting = Greeting()

      if user:
        greeting.author = user.name

      greeting.content = self.content
      greeting.put()
      self.redirect('/')

  def __error(self):
    if len(self.content) > 500:
      return 'tooLongValue'
    if len(self.content) == 0:
      return 'emptyField'

  def __userName(self):
    sessionId = self.request.cookies.get('sid')
    if sessionId:
      userId = memcache.get(sessionId)
      if userId is not None:
        return User.get_by_id(userId)


class Login(webapp.RequestHandler):
  def get(self):
    self.ERROR_MESSAGES = {
        'wrongPassword': 'Password is incorrect.',
        'incorrectEmail': 'Please, enter valid email address.',
        'wrongEmail': 'Email not found.'
    }

    template_values = {
        'error': self.ERROR_MESSAGES.get(self.request.get('error')),
        'email': self.request.get('email')
        }
    path = os.path.join(os.path.dirname(__file__), 'login.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    xhr = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if xhr:
      logging.info('xhr')

    self.email = self.request.get('email')
    error = self.__error()
    if error:
      if error == 'incorrectEmail':
        self.email = ''

      if xhr:
        # self.response.out.write({"error": error, "email": self.email})
        self.response.out.write("{\"error\": \"%s\", \"email\": \"%s\"}" % \
                                (self.ERROR_MESSAGES[error], self.email))
      else:
        self.redirect('/login?error=' + error + '&email=' + self.email)
      return

    sessionId = str(uuid.uuid4()).replace('-','')
    memcache.set(sessionId, self.user.key().id(), 36000)
    self.response.headers.add_header('Set-Cookie',
        'sid=%s; path=/' % sessionId)
    if xhr:
      # self.response.out.write({"name": str(self.user.name)})
      # json
      self.response.out.write("{\"name\": \"%s\"}" % str(self.user.name))
    else:
      self.redirect('/')

  def __error(self):
    if re.match('^[-.\w]+@(?:[a-z\d][-a-z\d]+\.)+[a-z]{2,6}$', self.email) is None:
      return 'incorrectEmail'

    self.user = User.all().filter('email =', self.email).get()
    if self.user is None:
      return 'wrongEmail'

    salt = self.user.salt
    password = self.request.get('password')
    if re.match('^\w+$', password) is None:
      password = ''
    passwordHash = hashlib.sha1(password + salt).hexdigest()

    if self.user.password != passwordHash:
      return 'wrongPassword'

class Logout(webapp.RequestHandler):
  def get(self):
    sessionId = self.request.cookies.get('sid')
    logging.info(sessionId)
    # if sessionId:
    memcache.delete(sessionId)
    self.response.headers.add_header('Set-Cookie', 'sid=; path=/')

    if self.request.headers.get('X-Requested-With') != 'XMLHttpRequest':
      self.redirect('/')

class Register(webapp.RequestHandler):
  
  def get(self):
    ERROR_MESSAGES = {
        'tooLongValue': 'The value is too long.',
        'emptyField': 'Required fields are not filled.',
        'wrongEmail': 'Sorry, such email already exists.',
        'incorrectEmail': 'Please, enter valid email address.',
        'wrongPassword': 'Password should contain only English letters, numbers or underscores.',
        'wrongConfirmation': 'Passwords don\'t match.',
        'wrongName': 'Sorry, name should contain only English letters, numbers or underscores.'
    }

    template_values = {
        'error' : ERROR_MESSAGES.get(self.request.get('error')),
        'errorMessages' : ERROR_MESSAGES,
        'form' : [
            {
              'label': 'Email',
              'type': 'text',
              'name': 'email',
              'value': self.request.get('email')
            },
            {
              'label': 'Password',
              'type': 'password',
              'name': 'password',
            },
            {
              'label': 'Confirm password',
              'type': 'password',
              'name': 'confirmPassword',
            },
            {
              'label': 'Name',
              'type': 'text',
              'name': 'name',
              'value': self.request.get('name')
            }
          ]
        }
    path = os.path.join(os.path.dirname(__file__), 'registration.html')
    self.response.out.write(template.render(path, template_values))

  def __error(self):
    for i in [self.email, self.password, self.confirmPassword, self.name]:
      if len(i) > 100:
        return 'tooLongValue'
      if len(i) == 0:
        return 'emptyField'

    if re.match('^[-.\w]+@(?:[a-z\d][-a-z\d]+\.)+[a-z]{2,6}$', self.email) is None:
      return 'incorrectEmail'

    if User.all().filter('email =', self.email).get() is not None:
      return 'wrongEmail'

    if re.match('^\w+$', self.password) is None:
      return 'wrongPassword'

    if self.password != self.confirmPassword:
      return 'wrongConfirmation'

    if re.match('^\w+$', self.name) is None:
      return 'wrongName'


  def post(self):
    self.email = self.request.get('email')
    self.password = self.request.get('password')
    self.confirmPassword = self.request.get('confirmPassword')
    self.name = self.request.get('name')

    error = self.__error()
    if error:
      errorUrl = '/register?error=' + error
      if error != 'tooLongValue' and error != 'incorrectEmail':
        errorUrl += '&email=' + self.email
        if error != 'wrongName':
          errorUrl += '&name=' + self.name
      self.redirect(errorUrl)

    else:
      salt = str(uuid.uuid4()).replace('-','')
      passwordHash = hashlib.sha1(self.password + salt).hexdigest()

      user = User()
      user.email = self.email
      user.password = str(passwordHash)
      user.salt = salt
      user.name = self.name
      user.put()

      self.redirect('/?message=regSuccessful')

application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/register', Register),
  ('/login', Login),
  ('/logout', Logout)
], debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
