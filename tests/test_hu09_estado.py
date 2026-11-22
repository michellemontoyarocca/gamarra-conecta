"""GC-13 / HU09: consultar el estado de mis solicitudes."""
from base import HistoriaTestCase


class EstadoDeSolicitudesTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.login()
        self.post('/orientacion', {'topic': 'Licencia municipal', 'details': 'Consulta de licencia.'})

    def test_la_solicitud_nueva_muestra_estado_pendiente(self):
        self.assertIn(b'pendiente', self.client.get('/orientacion').data)

    def test_al_revisarla_el_administrador_el_estado_se_actualiza(self):
        admin = self.make_admin()
        self.post('/admin/solicitudes/1/revisar', {}, admin)
        pagina = self.client.get('/orientacion').data
        self.assertIn(b'revisada', pagina)
        self.assertNotIn(b'>pendiente<', pagina)

    def test_solo_veo_mis_solicitudes(self):
        otra = self.new_client()
        self.register('beto@example.test', 'Beto', otra)
        self.login('beto@example.test', client=otra)
        self.assertNotIn(b'Consulta de licencia.', otra.get('/orientacion').data)

    def test_un_usuario_comun_no_puede_marcar_solicitudes_como_revisadas(self):
        self.assertEqual(self.post('/admin/solicitudes/1/revisar', {}).status_code, 403)
        self.assertEqual(self.query('SELECT status FROM guidance_requests')[0][0], 'pendiente')
