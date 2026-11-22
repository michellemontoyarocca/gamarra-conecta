"""GC-15 / HU11: proteger formularios y datos para evitar cambios no autorizados."""
from base import HistoriaTestCase


class ProteccionDeFormulariosTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.login()
        self.create_business()

    def test_post_sin_token_csrf_se_rechaza_y_no_cambia_los_datos(self):
        respuesta = self.client.post('/mi-negocio', data={
            'name': 'Nombre alterado', 'category': 'Telas', 'gallery': 'Galería 1', 'description': 'Texto',
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(self.query('SELECT name FROM businesses')[0][0], 'Confecciones Andinas')

    def test_post_con_token_invalido_se_rechaza(self):
        self.client.get('/')
        respuesta = self.client.post('/orientacion', data={'_csrf': 'falso', 'topic': 'Licencia municipal', 'details': 'x'})
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(self.query('SELECT COUNT(*) FROM guidance_requests')[0][0], 0)

    def test_cambios_sin_sesion_se_redirigen_al_login(self):
        anonimo = self.new_client()
        self.assertEqual(anonimo.get('/mi-negocio').status_code, 302)
        self.assertEqual(anonimo.get('/orientacion').status_code, 302)

    def test_la_cookie_de_sesion_es_httponly_y_samesite(self):
        cabeceras = self.client.get('/login').headers.getlist('Set-Cookie')
        self.assertTrue(any('HttpOnly' in c and 'SameSite=Lax' in c for c in cabeceras) or self.app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertTrue(self.app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(self.app.config['SESSION_COOKIE_SAMESITE'], 'Lax')

    def test_las_entradas_se_escapan_en_pantalla(self):
        self.post('/mi-negocio', {
            'name': '<script>alert(1)</script>', 'category': 'Otros', 'gallery': 'Galería 2', 'description': 'Descripción',
        })
        admin = self.make_admin()
        self.assertNotIn(b'<script>alert(1)</script>', admin.get('/admin').data)
