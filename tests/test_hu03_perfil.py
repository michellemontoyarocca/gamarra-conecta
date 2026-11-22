"""GC-7 / HU03: registrar y editar el perfil de mi negocio."""
from base import HistoriaTestCase


class PerfilDeNegocioTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.login()

    def test_perfil_valido_queda_pendiente_de_revision(self):
        resultado = self.create_business()
        self.assertIn('enviado a revisi'.encode(), resultado.data)
        self.assertEqual(self.query('SELECT status FROM businesses')[0][0], 'pendiente')

    def test_editar_un_perfil_publicado_lo_devuelve_a_pendiente(self):
        self.create_business()
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        self.assertEqual(self.query('SELECT status FROM businesses')[0][0], 'publicado')
        self.create_business(name='Confecciones Andinas Norte')
        estado, nombre = self.query('SELECT status, name FROM businesses')[0]
        self.assertEqual((estado, nombre), ('pendiente', 'Confecciones Andinas Norte'))

    def test_no_se_puede_editar_el_perfil_de_otra_cuenta(self):
        self.create_business()
        otra = self.new_client()
        self.register('beto@example.test', 'Beto', otra)
        self.login('beto@example.test', client=otra)
        self.create_business(otra, name='Telas Beto', category='Telas')
        nombres = sorted(fila[0] for fila in self.query('SELECT name FROM businesses'))
        self.assertEqual(nombres, ['Confecciones Andinas', 'Telas Beto'])

    def test_el_titular_ve_el_estado_de_su_perfil_en_mi_negocio(self):
        self.create_business()
        self.assertIn(b'Tu perfil est\xc3\xa1 en revisi\xc3\xb3n', self.client.get('/mi-negocio').data)
        admin = self.make_admin()
        self.post('/admin/negocios/1/publicar', {}, admin)
        self.assertIn(b'Tu perfil est\xc3\xa1 publicado', self.client.get('/mi-negocio').data)

    def test_el_titular_ve_que_su_perfil_fue_rechazado_y_puede_corregirlo(self):
        self.create_business()
        admin = self.make_admin()
        self.post('/admin/negocios/1/rechazar', {}, admin)
        self.assertIn(b'Tu perfil fue rechazado', self.client.get('/mi-negocio').data)

    def test_categoria_invalida_se_rechaza(self):
        resultado = self.create_business(category='Inventado')
        self.assertIn(b'Revisa los campos', resultado.data)
        self.assertEqual(self.query('SELECT COUNT(*) FROM businesses')[0][0], 0)
