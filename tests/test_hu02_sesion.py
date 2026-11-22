"""GC-6 / HU02: iniciar y cerrar sesión para proteger el acceso a mis datos."""
from base import HistoriaTestCase


class SesionTests(HistoriaTestCase):
    def test_credenciales_validas_llevan_al_panel(self):
        self.register()
        self.assertIn(b'Mi negocio', self.login().data)

    def test_credenciales_invalidas_no_dan_acceso(self):
        self.register()
        resultado = self.login(password='ClaveIncorrecta1!')
        self.assertIn(b'Credenciales incorrectas', resultado.data)
        self.assertEqual(self.client.get('/mi-negocio').status_code, 302)

    def test_cerrar_sesion_vuelve_a_proteger_el_panel(self):
        self.register()
        self.login()
        self.assertEqual(self.client.get('/mi-negocio').status_code, 200)
        self.post('/logout', {})
        self.assertEqual(self.client.get('/mi-negocio').status_code, 302)
