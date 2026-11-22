"""GC-8 / HU04: ver un directorio de negocios aprobados."""
from base import HistoriaTestCase


class DirectorioTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.login()
        self.create_business()

    def test_perfil_pendiente_no_aparece_en_el_directorio(self):
        respuesta = self.client.get('/negocios')
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(b'Confecciones Andinas', respuesta.data)

    def test_perfil_aprobado_aparece_en_el_directorio(self):
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        visitante = self.new_client()
        self.assertIn(b'Confecciones Andinas', visitante.get('/negocios').data)

    def test_la_portada_muestra_los_negocios_recientes_solo_si_estan_publicados(self):
        portada = self.new_client().get('/')
        self.assertNotIn(b'Confecciones Andinas', portada.data)
        self.assertIn('Aún no hay negocios publicados'.encode(), portada.data)
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        portada = self.new_client().get('/')
        self.assertIn(b'Confecciones Andinas', portada.data)
        self.assertIn(b'1</strong><span>negocio publicado', portada.data)

    def test_el_directorio_indica_cuantos_resultados_hay(self):
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        self.assertIn('1 resultado'.encode(), self.new_client().get('/negocios').data)

    def test_directorio_es_publico_y_no_expone_el_correo_del_titular(self):
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        contenido = self.new_client().get('/negocios').data
        self.assertNotIn(b'ana@example.test', contenido)
