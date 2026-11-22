"""Utilidades compartidas por las pruebas de las historias de usuario."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app


class HistoriaTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / 'test.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.db_path, 'SECRET_KEY': 'only-for-tests'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def post(self, path, data, client=None, follow=True):
        target = client or self.client
        target.get('/')
        with target.session_transaction() as state:
            token = state['_csrf']
        return target.post(path, data={'_csrf': token, **data}, follow_redirects=follow)

    def register(self, email='ana@example.test', name='Ana', client=None):
        return self.post('/registro', {'name': name, 'email': email, 'password': 'ClaveSegura123!'}, client)

    def login(self, email='ana@example.test', password='ClaveSegura123!', client=None):
        return self.post('/login', {'email': email, 'password': password}, client)

    def new_client(self):
        return self.app.test_client()

    def query(self, sql, args=()):
        connection = sqlite3.connect(self.db_path)
        try:
            return connection.execute(sql, args).fetchall()
        finally:
            connection.close()

    def make_admin(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'admin')",
            ('Admin', 'admin@example.test', generate_password_hash('ClaveAdmin123!')),
        )
        connection.commit()
        connection.close()
        admin = self.new_client()
        self.login('admin@example.test', 'ClaveAdmin123!', admin)
        return admin

    def create_business(self, client=None, name='Confecciones Andinas', category='Confección'):
        return self.post('/mi-negocio', {
            'name': name, 'category': category,
            'gallery': 'Galería Norte 12', 'description': 'Prendas de algodón y confección a pedido.',
        }, client)
