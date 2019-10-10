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

    def get_book_names(self):
        with self.connection:
            book_names = self.cursor.execute("SELECT Name FROM Library").fetchall()
            return book_names

    def get_book_list_by_genre(self, genre):
        with self.connection:
            genres = self.cursor.execute('SELECT * FROM Library WHERE Genre=?', (genre,)).fetchall()
            return genres

    def get_book_list_by_book_name(self, book_name):
        books = self.cursor.execute('SELECT * FROM Library WHERE Name=?', (book_name,)).fetchall()
        return books

    def take_book(self, book_id, user_name):
        with self.connection:
            self.cursor.execute('UPDATE Library SET Owner=? WHERE id=?', (user_name, book_id))

    def return_book(self, book_id):
        with self.connection:
            self.cursor.execute('UPDATE Library SET Owner=NULL WHERE id=?', (book_id,))

    def close(self):
        self.connection.close()
