"""GC-10 / HU06: abrir la ficha de un negocio para consultar sus datos publicados."""
from base import HistoriaTestCase


class FichaDeNegocioTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.login()
        self.create_business()
        self.visitante = self.new_client()

    def test_ficha_de_perfil_aprobado_muestra_sus_datos_publicos(self):
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        respuesta = self.visitante.get('/negocios/1')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b'Confecciones Andinas', respuesta.data)
        self.assertIn('Galería Norte 12'.encode(), respuesta.data)

    def test_ficha_no_muestra_informacion_privada_de_la_cuenta(self):
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        contenido = self.visitante.get('/negocios/1').data
        self.assertNotIn(b'ana@example.test', contenido)
        self.assertNotIn(b'password', contenido.lower())

    def test_ficha_de_perfil_pendiente_o_inexistente_devuelve_404(self):
        self.assertEqual(self.visitante.get('/negocios/1').status_code, 404)
        self.assertEqual(self.visitante.get('/negocios/999').status_code, 404)

    def test_el_directorio_enlaza_a_la_ficha(self):
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        self.assertIn(b'href="/negocios/1"', self.visitante.get('/negocios').data)
