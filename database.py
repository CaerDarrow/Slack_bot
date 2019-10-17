import sqlite3

class LibraryDB:
    def __init__(self, database='library.db'):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def add_book(self, book_name, author, genre):
        with self.connection:
            self.cursor.execute('INSERT INTO Library(Name, Author) VALUES(?, ?, ?)', (book_name, author, genre))
        return str(self.cursor.lastrowid)

    def get_genres(self):
        with self.connection:
            genres = self.cursor.execute("SELECT DISTINCT Genre FROM Library").fetchall()
            return genres

    def get_surnames(self):
        with self.connection:
            surnames = self.cursor.execute("SELECT DISTINCT Author_surname FROM Library").fetchall()
            return surnames

    def get_book_names(self):
        with self.connection:
            book_names = self.cursor.execute("SELECT Name FROM Library").fetchall()
            return book_names

    def get_selectors(self, action):
        with self.connection:
            selectors = self.cursor.execute("SELECT DISTINCT ? FROM Library", (action,)).fetchall()
            return selectors

    def get_book_list_by_genre(self, genre):
        with self.connection:
            genres = self.cursor.execute('SELECT * FROM Library WHERE Genre=?', (genre,)).fetchall()
            return genres

    def get_book_list_by_book_names(self, book_name):
        with self.connection:
            books = self.cursor.execute('SELECT * FROM Library WHERE Name=?', (book_name,)).fetchall()
            return books

    def get_book_list_by_surnames(self, book_name):
        with self.connection:
            books = self.cursor.execute('SELECT * FROM Library WHERE Author_surname=?', (book_name,)).fetchall()
            return books

    def get_book_by_id(self, book_id):
        with self.connection:
            book = self.cursor.execute('SELECT * FROM Library WHERE id=?', (book_id,)).fetchone()
            return book

    def take_book(self, book_id, user_name, user_id):
        with self.connection:
            self.cursor.execute('UPDATE Library SET Owner=?, Owner_id=?, Cluster=NULL WHERE id=?', (user_name, user_id,
                                                                                                    book_id))

    def return_book(self, book_id, cluster):
        with self.connection:
            self.cursor.execute('UPDATE Library SET Owner=NULL, Owner_id=NULL, Cluster=? WHERE id=?', (cluster,
                                                                                                       book_id))

    def close(self):
        self.connection.close()
