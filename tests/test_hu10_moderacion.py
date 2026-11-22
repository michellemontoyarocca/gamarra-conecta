"""GC-14 / HU10: aprobar o rechazar perfiles para controlar qué negocios aparecen en el directorio."""
from base import HistoriaTestCase


class ModeracionDePerfilesTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.login()
        self.create_business()
        self.admin = self.make_admin()
        self.visitante = self.new_client()

    def estado(self):
        return self.query('SELECT status FROM businesses')[0][0]

    def test_el_administrador_ve_el_perfil_pendiente(self):
        self.assertIn(b'Confecciones Andinas', self.admin.get('/admin').data)

    def test_aprobar_publica_el_perfil_en_el_directorio(self):
        self.post('/admin/negocios/1/publicar', {}, self.admin)
        self.assertEqual(self.estado(), 'publicado')
        self.assertIn(b'Confecciones Andinas', self.visitante.get('/negocios').data)

    def test_rechazar_mantiene_el_perfil_fuera_del_directorio(self):
        self.post('/admin/negocios/1/rechazar', {}, self.admin)
        self.assertEqual(self.estado(), 'rechazado')
        self.assertNotIn(b'Confecciones Andinas', self.visitante.get('/negocios').data)
        self.assertEqual(self.visitante.get('/negocios/1').status_code, 404)

    def test_el_titular_puede_corregir_un_perfil_rechazado_y_reenviarlo(self):
        self.post('/admin/negocios/1/rechazar', {}, self.admin)
        self.create_business(name='Confecciones Andinas Norte')
        self.assertEqual(self.estado(), 'pendiente')

    def test_un_usuario_comun_no_puede_moderar(self):
        self.assertEqual(self.post('/admin/negocios/1/publicar', {}).status_code, 403)
        self.assertEqual(self.post('/admin/negocios/1/rechazar', {}).status_code, 403)
        self.assertEqual(self.estado(), 'pendiente')
