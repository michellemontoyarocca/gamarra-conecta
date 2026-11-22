"""GC-11 / HU07: consultar una guía de formalización con pasos y enlaces oficiales."""
from base import HistoriaTestCase


class GuiaDeFormalizacionTests(HistoriaTestCase):
    def test_la_guia_es_publica_y_muestra_los_pasos(self):
        respuesta = self.client.get('/guia')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(b'RUC', respuesta.data)
        self.assertIn('licencia de funcionamiento'.encode(), respuesta.data)

    def test_la_guia_enlaza_a_fuentes_oficiales(self):
        contenido = self.client.get('/guia').data
        self.assertIn(b'https://www.sunat.gob.pe/', contenido)
        self.assertIn(b'https://www.gob.pe/', contenido)

    def test_la_guia_se_identifica_como_informacion_general(self):
        contenido = self.client.get('/guia').data
        self.assertIn('no verifica la situación'.encode(), contenido)

    def test_los_enlaces_externos_no_filtran_el_origen(self):
        self.assertIn(b'rel="noopener noreferrer"', self.client.get('/guia').data)
