"""GC-5 / HU01: crear una cuenta para gestionar mi negocio en el portal."""
from base import HistoriaTestCase


class RegistroDeCuentaTests(HistoriaTestCase):
    def test_formulario_valido_crea_cuenta_y_permite_iniciar_sesion(self):
        resultado = self.register()
        self.assertIn('Cuenta creada'.encode(), resultado.data)
        self.assertEqual(self.query('SELECT COUNT(*) FROM users WHERE email=?', ('ana@example.test',))[0][0], 1)
        self.assertIn(b'Mi negocio', self.login().data)

    def test_correo_repetido_muestra_error_sin_duplicar_datos(self):
        self.register()
        repetido = self.register(name='Otra Ana')
        self.assertIn('Ese correo ya está registrado'.encode(), repetido.data)
        self.assertEqual(self.query('SELECT COUNT(*) FROM users')[0][0], 1)

    def test_contrasena_corta_se_rechaza(self):
        resultado = self.post('/registro', {'name': 'Ana', 'email': 'ana@example.test', 'password': 'corta'})
        self.assertIn(b'al menos 10 caracteres', resultado.data)
        self.assertEqual(self.query('SELECT COUNT(*) FROM users')[0][0], 0)
