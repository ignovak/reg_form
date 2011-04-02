import os
import cgi
import datetime
import wsgiref.handlers
import uuid
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
    self.response.out.write("""
      <html>
        <body>
          <form action='/login' method='post'>
            <div><input type='email' name='email' /></div>
            <div><input type='password' name='password' /></div>
            <div><input type='submit' value='Log In'></div>
          </form>
        </body>
      </html>""")

  def post(self):
    email = self.request.get('email')
    password = self.request.get('password')
    user = User.all().filter('email =', email) \
            .filter('password =', password).get()
    if user is not None:
      sessionId = str(uuid.uuid4()).replace('-','')
      memcache.set(sessionId, user.key().id(), 36000)
      self.response.headers.add_header('Set-Cookie',
          'sid=%s; path=/' % sessionId)
      self.redirect('/')
    else:
      self.response.out.write('Error')
      self.redirect('/login')

class Logout(webapp.RequestHandler):
  def get(self):
    sessionId = self.request.cookies.get('sid')
    if sessionId:
      memcache.delete(sessionId)
      self.response.headers.add_header('Set-Cookie', 'sid=; path=/')

    self.redirect('/')

class Register(webapp.RequestHandler):
  def get(self):
    template_values = {
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
              'label': 'Name',
              'type': 'text',
              'name': 'name'
            }
          ]
        }
    path = os.path.join(os.path.dirname(__file__), 'registration.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    user = User()
    user.email = self.request.get('email')
    user.password = self.request.get('password')
    user.name = self.request.get('name')
    user.put()

    self.response.out.write('Thank you')
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
