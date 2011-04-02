import os
import cgi
import datetime
import wsgiref.handlers

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

class Greeting(db.Model):
  author = db.UserProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)

class User(db.Model):
  email = db.StringProperty()
  password = db.StringProperty()
  name = db.StringProperty()

class MainPage(webapp.RequestHandler):
  def get(self):
    greetings_query = Greeting.all().order('-date')
    greetings = greetings_query.fetch(10)

    if users.get_current_user():
      url = users.create_logout_url(self.request.uri)
      url_linktext = 'Logout'
    else:
      url = users.create_login_url(self.request.uri)
      url_linktext = 'Login'

    template_values = {
      'greetings': greetings,
      'url': url,
      'url_linktext': url_linktext,
      }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
  def post(self):
    greeting = Greeting()

    if users.get_current_user():
      greeting.author = users.get_current_user()

    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/')

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
      self.response.out.write('Thank you')
      self.redirect('/')
    else:
      self.response.out.write('Error')
      self.redirect('/login')


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
    # self.response.headers['Content-Type'] = 'text/plain'
    # self.response.out.write('Email: %s\n' % email)
    # self.response.out.write('Password: %s\n' % password)
    # self.response.out.write('Name: %s\n' % name)

application = webapp.WSGIApplication([
  ('/', MainPage),
  ('/register', Register),
  ('/login', Login)
  # ('/sign', Guestbook)
], debug=True)


def main():
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
