import requests
from bs4 import BeautifulSoup
from enum import Enum
from os import getenv

try:
   from account import GSAccount
except ModuleNotFoundError:
   from .account import GSAccount

try:
   from course import GSCourse, LoadedCapabilities
except ModuleNotFoundError:
   from .course import GSCourse, LoadedCapabilities

class ConnState(Enum):
    INIT = 0
    LOGGED_IN = 1

class GSConnection():
    '''The main connection class that keeps state about the current connection.'''
        
    def __init__(self):
        '''Initialize the session for the connection.'''
        self.session = requests.Session()
        self.state = ConnState.INIT
        self.account = None

        # fake the user agent
        self.session.headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0' })

    def login(self, email, pswd):
        '''
        Login to gradescope using email and password.
        Note that the future commands depend on account privilages.
        '''
        init_resp = self.session.get("https://www.gradescope.com/")
        parsed_init_resp = BeautifulSoup(init_resp.text, 'html.parser')
        for form in parsed_init_resp.find_all('form'):
            if form.get("action") == "/login":
                for inp in form.find_all('input'):
                    if inp.get('name') == "authenticity_token":
                        auth_token = inp.get('value')

        login_data = {
            "utf8": "✓",
            "session[email]": email,
            "session[password]": pswd,
            "session[remember_me]": 0,
            "commit": "Log In",
            "session[remember_me_sso]": 0,
            "authenticity_token": auth_token,
        }
        login_resp = self.session.post("https://www.gradescope.com/login", params=login_data)
        if len(login_resp.history) != 0:
            if login_resp.history[0].status_code == requests.codes.found:
                self.state = ConnState.LOGGED_IN
                self.account = GSAccount(email, self.session)
                return True
        else:
            return False

    def get_account(self):
        '''
        Gets and parses account data after login. Note will return false if we are not in a logged in state, but 
        this is subject to change.
        '''
        if self.state != ConnState.LOGGED_IN:
            return False # Should raise exception
        # Get account page and parse it using bs4
        account_resp = self.session.get("https://www.gradescope.com/account")
        parsed_account_resp = BeautifulSoup(account_resp.text, 'html.parser')

        # Get instructor course data
        instructor_courses = parsed_account_resp.find('h1', class_ ='pageHeading').next_sibling
        
        for course in instructor_courses.find_all('a', class_ = 'courseBox'):
            shortname = course.find('h3', class_ = 'courseBox--shortname').text
            name = course.find('h4', class_ = 'courseBox--name').text
            cid = course.get("href").split("/")[-1]
            year = None
            print(cid, name, shortname)
            for tag in course.parent.previous_siblings:
                if 'courseList--term' in tag.get("class"):
                    year = tag.string
                    break
            if year is None:
                return False # Should probably raise an exception.
            self.account.add_class(cid, name, shortname, year, instructor = True)

# THIS IS STRICTLY FOR DEVELOPMENT TESTING :( Sorry for leaving it in.
if __name__=="__main__":
    conn = GSConnection()

    print(conn.login(getenv("STANFORD_GRADESCOPE_USER"), getenv("STANFORD_GRADESCOPE_PASSWORD")))
    print(conn.state)
    print(conn.get_account())

    course_it = filter(lambda c: c.name == getenv("STANFORD_GRADESCOPE_COURSE_NAME") and c.shortname == getenv("STANFORD_GRADESCOPE_COURSE_SHORTNAME"), conn.account.instructor_courses.values())
    course_list = list(course_it)
    if len(course_list) != 1:
        raise Exception(f"Found {len(course_list)} courses instead of exactly one.")

    course = course_list[0]
    course._check_capabilities({LoadedCapabilities.ASSIGNMENTS})

    project_it = filter(lambda p: p.name == getenv("STANFORD_GRADESCOPE_ASSIGNMENT_NAME"), course.assignments.values())
    project_list = list(project_it)
    if len(project_list) != 1:
        raise Exception(f"Found {len(project_list)} projects instead of exactly one.")

    project = project_list[0]
    project.configure_autograder()
    project.check_gradescope_autograder_image(getenv("STANFORD_AUTOGRADER_IMAGE_NAME"), getenv("STANFORD_AUTOGRADER_IMAGE_TAG"))