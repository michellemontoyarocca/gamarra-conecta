"""GC-12 / HU08: solicitar orientación para recibir seguimiento de la consulta."""
from base import HistoriaTestCase


class SolicitudDeOrientacionTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.login()

    def test_solicitud_valida_queda_pendiente_y_visible_en_el_panel(self):
        resultado = self.post('/orientacion', {'topic': 'Licencia municipal', 'details': 'Deseo conocer los pasos.'})
        self.assertIn(b'Solicitud registrada', resultado.data)
        self.assertEqual(self.query('SELECT status FROM guidance_requests')[0][0], 'pendiente')
        self.assertIn(b'Deseo conocer los pasos.', self.client.get('/orientacion').data)

    def test_solicitud_vacia_se_rechaza(self):
        resultado = self.post('/orientacion', {'topic': 'Licencia municipal', 'details': '   '})
        self.assertIn(b'Elige un tema', resultado.data)
        self.assertEqual(self.query('SELECT COUNT(*) FROM guidance_requests')[0][0], 0)

    def test_tema_inventado_o_texto_demasiado_largo_se_rechazan(self):
        self.post('/orientacion', {'topic': 'Tema falso', 'details': 'Consulta'})
        self.post('/orientacion', {'topic': 'Licencia municipal', 'details': 'x' * 1001})
        self.assertEqual(self.query('SELECT COUNT(*) FROM guidance_requests')[0][0], 0)

    def test_requiere_sesion_para_solicitar(self):
        anonimo = self.new_client()
        self.assertEqual(anonimo.get('/orientacion').status_code, 302)
