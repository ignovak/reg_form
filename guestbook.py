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
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Greeting(db.Model):
  author = db.StringProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)

class User(db.Model):
  email = db.StringProperty()
  password = db.StringProperty()
  name = db.StringProperty()
  salt = db.StringProperty()

class MainPage(webapp.RequestHandler):
  def get(self):
    user = self.__userName()
    
    greetings_query = Greeting.all().order('-date')
    greetings = greetings_query.fetch(10)

    template_values = {
      'greetings': greetings,
      'user': user
      }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    user = self.__userName()
    greeting = Greeting()

    if user:
      greeting.author = user.name

    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/')

  def __userName(self):
    sessionId = self.request.cookies.get('sid')
    if sessionId:
      userId = memcache.get(sessionId)
      if userId is not None:
        return User.get_by_id(userId)


class Login(webapp.RequestHandler):
  def get(self):
    ERROR_MESSAGES = {
        'wrongPassword': 'Password is incorrect.',
        'wrongEmail': 'Email not found.'
    }
    template_values = {
        'error' : ERROR_MESSAGES.get(self.request.get('error'))
        }
    path = os.path.join(os.path.dirname(__file__), 'login.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    email = self.request.get('email')
    user = User.all().filter('email =', email).get()
    if user is not None:
      salt = user.salt
      password = self.request.get('password')
      if re.match('^\w+$', password) is None:
        password = ''
      passwordHash = hashlib.sha1(password + salt).hexdigest()

      if user.password == passwordHash:
        sessionId = str(uuid.uuid4()).replace('-','')
        memcache.set(sessionId, user.key().id(), 36000)
        self.response.headers.add_header('Set-Cookie',
            'sid=%s; path=/' % sessionId)
        self.redirect('/')

      else:
        self.redirect('/login?error=wrongPassword')

    else:
      self.redirect('/login?error=wrongEmail')

class Logout(webapp.RequestHandler):
  def get(self):
    sessionId = self.request.cookies.get('sid')
    if sessionId:
      memcache.delete(sessionId)
      self.response.headers.add_header('Set-Cookie', 'sid=; path=/')

    self.redirect('/')

class Register(webapp.RequestHandler):
  
  def get(self):
    ERROR_MESSAGES = {
        'wrongEmail': 'Sorry, such email already exists.',
        'wrongPassword': 'Password should contain only English letters, numbers or underscores.',
        'wrongConfirmation': 'Passwords don\'t match.'
    }
    template_values = {
        'error' : ERROR_MESSAGES.get(self.request.get('error')),
        'form' : [
            {
              'label': 'Email',
              'type': 'email',
              'name': 'email'
            },
            {
              'label': 'Password',
              'type': 'password',
              'name': 'password'
            },
            {
              'label': 'Confirm password',
              'type': 'password',
              'name': 'confirmPassword'
            },
            {
              'label': 'Name',
              'type': 'text',
              'name': 'name'
            }
          ]
        }
    path = os.path.join(os.path.dirname(__file__), 'registration.html')
    self.response.out.write(template.render(path, template_values))

  def __error(self):
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
      self.redirect('/register?error=' + error)
    else:
      salt = str(uuid.uuid4()).replace('-','')
      passwordHash = hashlib.sha1(self.password + salt).hexdigest()

      user = User()
      user.email = self.email
      user.password = str(passwordHash)
      user.salt = salt
      user.name = self.name
      user.put()

      self.redirect('/')

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
