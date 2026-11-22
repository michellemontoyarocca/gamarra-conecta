"""GC-9 / HU05: filtrar negocios por rubro o nombre."""
from base import HistoriaTestCase


class FiltroDelDirectorioTests(HistoriaTestCase):
    def setUp(self):
        super().setUp()
        self.admin = self.make_admin()
        self.visitante = self.new_client()
        for indice, (nombre, rubro) in enumerate([('Confecciones Andinas', 'Confección'), ('Telas del Sur', 'Telas')], start=1):
            cliente = self.new_client()
            correo = f'dueno{indice}@example.test'
            self.register(correo, f'Dueño {indice}', cliente)
            self.login(correo, client=cliente)
            self.create_business(cliente, name=nombre, category=rubro)
            self.post(f'/admin/negocios/{indice}/publicar', {}, self.admin)

    def test_filtrar_por_rubro_muestra_solo_ese_rubro(self):
        datos = self.visitante.get('/negocios?rubro=Telas').data
        self.assertIn(b'Telas del Sur', datos)
        self.assertNotIn(b'Confecciones Andinas', datos)

    def test_filtrar_por_nombre_muestra_coincidencias_y_conserva_el_criterio(self):
        datos = self.visitante.get('/negocios?q=Andinas').data
        self.assertIn(b'Confecciones Andinas', datos)
        self.assertNotIn(b'Telas del Sur', datos)
        self.assertIn(b'value="Andinas"', datos)

    def test_sin_coincidencias_muestra_estado_vacio(self):
        datos = self.visitante.get('/negocios?q=NoExiste').data
        self.assertIn('Aún no hay negocios'.encode(), datos)

    def test_rubro_inventado_se_rechaza(self):
        self.assertEqual(self.visitante.get('/negocios?rubro=Inventado').status_code, 400)
