import sqlite3
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

from app import create_app


class GamarraAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / 'test.sqlite3')
        self.app = create_app({'TESTING': True, 'DATABASE': self.db_path, 'SECRET_KEY': 'only-for-tests'})
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def post(self, path, data, client=None):
        target = client or self.client
        target.get('/')
        with target.session_transaction() as state:
            token = state['_csrf']
        return target.post(path, data={'_csrf': token, **data}, follow_redirects=True)

    def register_and_login(self, email='ana@example.test', name='Ana'):
        result = self.post('/registro', {'name': name, 'email': email, 'password': 'ClaveSegura123!'})
        self.assertIn('Cuenta creada'.encode(), result.data)
        return self.post('/login', {'email': email, 'password': 'ClaveSegura123!'})

    def make_admin(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,'admin')",
            ('Admin', 'admin@example.test', generate_password_hash('ClaveAdmin123!')),
        )
        connection.commit()
        connection.close()

    def test_registration_login_and_password_hash(self):
        response = self.register_and_login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Mi negocio', response.data)
        connection = sqlite3.connect(self.db_path)
        stored_hash = connection.execute('SELECT password_hash FROM users WHERE email=?', ('ana@example.test',)).fetchone()[0]
        connection.close()
        self.assertNotIn('ClaveSegura123!', stored_hash)

    def test_csrf_rejects_missing_token(self):
        result = self.client.post('/registro', data={'name': 'Ana', 'email': 'ana@example.test', 'password': 'ClaveSegura123!'})
        self.assertEqual(result.status_code, 400)

    def test_business_requires_review_before_search(self):
        self.register_and_login()
        result = self.post('/mi-negocio', {
            'name': 'Confecciones Andinas', 'category': 'Confección',
            'gallery': 'Galería Norte 12', 'description': 'Prendas de algodón y confección a pedido.',
        })
        self.assertIn('enviado a revisi'.encode(), result.data)
        self.assertNotIn(b'Confecciones Andinas', self.client.get('/negocios').data)
        self.make_admin()
        admin_client = self.app.test_client()
        self.post('/login', {'email': 'admin@example.test', 'password': 'ClaveAdmin123!'}, admin_client)
        dashboard = admin_client.get('/admin')
        self.assertIn(b'Confecciones Andinas', dashboard.data)
        self.post('/admin/negocios/1/publicar', {}, admin_client)
        self.assertIn(b'Confecciones Andinas', self.client.get('/negocios?rubro=Confecci%C3%B3n&q=Andinas').data)
        self.assertNotIn(b'Confecciones Andinas', self.client.get('/negocios?q=NoExiste').data)

    def test_owner_cannot_access_other_users_requests_or_admin(self):
        self.register_and_login()
        self.post('/orientacion', {'topic': 'Licencia municipal', 'details': 'Deseo conocer los pasos.'})
        self.assertIn(b'Deseo conocer los pasos.', self.client.get('/orientacion').data)
        self.assertEqual(self.client.get('/admin').status_code, 403)
        other = self.app.test_client()
        self.post('/registro', {'name': 'Beto', 'email': 'beto@example.test', 'password': 'ClaveSegura123!'}, other)
        self.post('/login', {'email': 'beto@example.test', 'password': 'ClaveSegura123!'}, other)
        self.assertNotIn(b'Deseo conocer los pasos.', other.get('/orientacion').data)

    def test_publication_rejects_non_admin_and_invalid_category(self):
        self.register_and_login()
        bad = self.post('/mi-negocio', {
            'name': 'Negocio', 'category': 'Inventado', 'gallery': 'Galería 3', 'description': 'Productos',
        })
        self.assertIn(b'Revisa los campos', bad.data)
        self.assertEqual(self.post('/admin/negocios/1/publicar', {}).status_code, 403)


if __name__ == '__main__':
    unittest.main()
