import sqlite3
import json
from collections import OrderedDict
from settings import DB_FILE, QNA_FILE, FLASK_DEBUG

# load question
with open(QNA_FILE, 'r') as f:
    qna = json.loads(f.read())

class DbConnector(object):
    def __init__(self, db=None):
        self.cache = {}
        self._db = db or DB_FILE
        self._conn = None
        self._cursor = None

    def connect(self):
        self._conn = self._conn or sqlite3.connect(self._db)
        if FLASK_DEBUG:
            print('DB connection opened.')

    def connect_cursor(self):
        self._cursor = self._cursor or self._conn.cursor()
        if FLASK_DEBUG:
            print('DB cursor opened.')

    @property
    def connection(self):
        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def clear_user_cache(self, user_id):
        self.cache.pop(user_id)

    def clear_cache(self):
        self.cache = {}

    def copy_from_cache(self, user_id):
        for field in self.cache[user_id]:
            self.update_user(user_id, field, self.cache[user_id][field])
        self.clear_user_cache(user_id)

    def close_cursor(self, commit=True):
        if commit and self.connection:
            self.connection.commit()
        self.cursor.close()
        self._cursor = None
        if FLASK_DEBUG:
            print('DB cursor closed.')

    def close(self, commit=True):
        if commit and self.connection:
            self.connection.commit()
        self.connection.close()
        self._conn = None
        if FLASK_DEBUG:
            print('DB connection closed.')

    def save(self, user_id=None):
        "Copy from cache, commit and close connection."
        if user_id: self.copy_from_cache(user_id)
        self.close()

    def sqlquery(func):
        def wrapper(self, *args):
            if FLASK_DEBUG:
                print("Calling {0} with {1} args".format(func, args))
            self.connect_cursor()
            ret = func(self, *args)
            self.close_cursor()
            if ret:
                return ret
        return wrapper

    @sqlquery
    def insert(self, table_name, field, value):
        sql = '''INSERT INTO {0} ({1}) VALUES ('{2}')
              '''.format(table_name, field, value)
        self.cursor.execute(sql)

    @sqlquery
    def create_table(self, table_name, fields):
        ''' Create table table_name.
            fields is a dictionary with keys as field names and values
            as field types. '''
        sql = '''CREATE TABLE IF NOT EXISTS {0} ({1})
              '''.format(table_name, ', '.join([field + ' ' + fields[field] \
                                                for field in fields]))
        self.cursor.execute(sql)

    @sqlquery
    def get_name(self, table, uuid):
        sql = "SELECT name FROM {0} WHERE id = {1}".format(table, uuid)
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        return row[0]

    @sqlquery
    def get_matches(self, user_id, city_id, goal_id, gender_id, lookfor_id):
        sql = '''SELECT id, first_name, description, photo
            FROM users WHERE city_id = {0} AND lookfor_id IN ({2},3)
            AND id != {3}'''.format(city_id, goal_id, gender_id, user_id)
        if lookfor_id < 3:
            # user does care about gender
            sql += " AND gender_id = {}".format(lookfor_id)
        if goal_id < 3:
            # user does care about goal
            sql += " AND goal_id IN ({},3)".format(goal_id)
        self.cursor.execute(sql)
        matches = self.cursor.fetchall()
        return matches

    @sqlquery
    def get_confirmed_matches(self, user_id):
        sql = '''SELECT match_id as id FROM matches
            WHERE user_id = {}'''.format(user_id)
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        matches = []
        for row in rows:
            if len(row) > 0:
                matches.append(row[0])
        return matches

    @sqlquery
    def add_confirmed_match(self, user_id, match_id):
        sql = '''INSERT INTO  matches (user_id, match_id)
            VALUES ({0}, {1})'''.format(user_id, match_id)
        self.cursor.execute(sql)

    @sqlquery
    def remove_confirmed_match(self, user_id, match_id):
        sql = '''DELETE FROM matches
            WHERE user_id = {0} AND
            match_id = {1}'''.format(user_id, match_id)
        self.cursor.execute(sql)

    @sqlquery
    def get_user(self, user_id):
        sql = "SELECT * FROM users WHERE id = {}".format(user_id)
        self.cursor.execute(sql)
        user = self.cursor.fetchone()
        return user

    @sqlquery
    def create_user(self, user_id):
        sql = "INSERT INTO users (id) VALUES ('{}')".format(user_id)
        self.cursor.execute(sql)

    @sqlquery
    def update_user(self, user_id, field, value):
        sql = '''UPDATE users SET {0}='{1}'
            WHERE id={2}'''.format(field, value, user_id)
        self.cursor.execute(sql)

    @sqlquery
    def delete_user(self, user_id):
        sql = "DELETE FROM users WHERE id={}".format(user_id)
        self.cursor.execute(sql)

    @sqlquery
    def get_city(self, user_id):
        sql = '''SELECT city_id FROM users
            WHERE id={}'''.format(user_id)
        self.cursor.execute(sql)
        city_id = self.cursor.fetchone()
        if city_id:
            return city_id[0]
        else:
            return None

    @sqlquery
    def set_city(self, user_id, city_id):
        sql = '''UPDATE users SET city_id={0}
            WHERE id={1}'''.format(city_id, user_id)
        self.cursor.execute(sql)

    @sqlquery
    def get_goal(self, user_id):
        sql = '''SELECT goal_id FROM users
            WHERE id={}'''.format(user_id)
        self.cursor.execute(sql)
        goal_id = self.cursor.fetchone()
        if goal_id:
            return goal_id[0]
        else:
            return None

    @sqlquery
    def set_goal(self, user_id, goal_id):
        sql = '''UPDATE users SET goal_id={0}
            WHERE id={1}'''.format(goal_id, user_id)
        self.cursor.execute(sql)

    @sqlquery
    def get_lookfor(self, user_id):
        sql = '''SELECT lookfor_id FROM users
            WHERE id={}'''.format(user_id)
        self.cursor.execute(sql)
        lookfor_id = self.cursor.fetchone()
        if lookfor_id:
            return lookfor_id[0]
        else:
            return None

    @sqlquery
    def set_lookfor(self, user_id, lookfor_id):
        sql = '''UPDATE users SET lookfor_id={0}
            WHERE id={1}'''.format(lookfor_id, user_id)
        self.cursor.execute(sql)

    @sqlquery
    def get_gender(self, user_id):
        sql = '''SELECT gender_id FROM users
            WHERE id={}'''.format(user_id)
        self.cursor.execute(sql)
        gender_id = self.cursor.fetchone()
        if gender_id:
            return gender_id[0]
        else:
            return None

    @sqlquery
    def set_description(self, user_id, desc):
        sql = '''UPDATE users SET description='{0}'
            WHERE id={1}'''.format(desc, user_id)
        self.cursor.execute(sql)

    @sqlquery
    def set_photo(self, user_id, photo_url):
        sql = '''UPDATE users SET photo='{0}'
            WHERE id={1}'''.format(photo_url, user_id)
        self.cursor.execute(sql)

    def new_db(self):
        ''' Create DB from self._db file.
            Run this method ONLY AND ONLY IF you need to create a new database.
            Causes complete data loss in case a DB already exists!
        '''
        self.connect()
        # create tables
        self.create_table("cities", {"id":"integer primary key autoincrement",
                                     "name":"text"})
        self.create_table("goals", {"id":"integer primary key autoincrement",
                                     "name":"text"})
        self.create_table("genders", {"id":"integer primary key autoincrement",
                                     "name":"char(1)"})
        users_fields = [("id","integer primary key not null"),
            ("first_name", "text"),
            ("last_name", "text"),
            ("description", "text"),
            ("photo", "text"),
            ("city_id", "integer"),
            ("goal_id", "integer"),
            ("lookfor_id", "integer"),
            ("gender_id", "integer"),
            ("foreign key(city_id)", "references cities(id)"),
            ("foreign key(goal_id)", "references goals(id)"),
            ("foreign key(lookfor_id)", "references genders(id)"),
            ("foreign key(gender_id)", "references genders(id)")]
        self.create_table("users", OrderedDict(users_fields))
        # insert choices
        for q in qna:
            table = q["table"]
            if table:
                for value in q["opts"]:
                    self.insert(table, "name", value[3:])  # strip 'n) ' 
        self.close()

    def test_users(self):
        ''' Fill DB with 100 fake users '''
        self.connect()
        for i in range(100):
            self.create_user(i)
            data = {"first_name":"Test"+str(i),
                    "last_name":"Test"+str(i),
                    "description":"test",
                    "photo":"photo218786773_456239630",
                    "city_id":i%2+1,
                    "goal_id":i%3+1,
                    "lookfor_id":i%3+1,
                    "gender_id":i%3+1}
            for key in data:
                self.update_user(i, key, data[key])
        self.close()
