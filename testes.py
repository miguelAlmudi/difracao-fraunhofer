"""Testes independentes de física, PNG e exportação: python testes.py."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from fisica import calcular, exemplo, carregar_png, salvar_mascara
from graficos import desenhar, salvar


class Testes(unittest.TestCase):
    def test_fenda_primeiro_minimo_e_sinc(self):
        r = calcular(exemplo('simples'))
        x, i = r['x_m'], r['intensidade'][512]
        a = 0.125e-3
        previsto = 633e-9*5/a
        indice = np.argmin(abs(x-previsto))
        self.assertAlmostEqual(x[indice], previsto, places=10)
        self.assertLess(i[indice], 1e-20)
        teorico = np.sinc(a*x/(633e-9*5))**2
        regiao = abs(x) < 2*previsto
        self.assertLess(np.max(abs(teorico[regiao]-i[regiao])), 0.001)

    def test_dupla_fenda(self):
        r = calcular(exemplo('dupla'))
        x = r['x_m']
        teorico = np.sinc(0.0625e-3*x/(633e-9*5))**2 * np.cos(np.pi*0.25e-3*x/(633e-9*5))**2
        regiao = abs(x) < 0.03
        self.assertLess(np.max(abs(teorico[regiao]-r['intensidade'][512, regiao])), 0.002)

    def test_circulo_simetria_e_minimo(self):
        r = calcular(exemplo('circulo'), padding=4)
        i = r['intensidade']
        np.testing.assert_allclose(i, i.T, atol=1e-14)
        x = r['x_m']
        previsto = 1.22*633e-9*5/0.25e-3
        trecho = np.where((x > 0.8*previsto) & (x < 1.2*previsto))[0]
        observado = x[trecho[np.argmin(i[len(i)//2, trecho])]]
        self.assertLess(abs(observado/previsto-1), 0.06)

    def test_unidades_e_normalizacao(self):
        m = exemplo('dupla', 64)
        r = calcular(m)
        self.assertEqual(r['intensidade'].max(), 1)
        self.assertEqual(r['intensidade'][128,128], 1)
        for kw in ({'onda_nm':1266}, {'distancia_m':10}, {'largura_mm':0.5}):
            outro = calcular(m, **kw)
            np.testing.assert_allclose(outro['x_m'], 2*r['x_m'])
            np.testing.assert_allclose(outro['intensidade'], r['intensidade'])

    def test_entradas_invalidas(self):
        for valor in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                calcular(exemplo('simples', 32), largura_mm=valor)
        with self.assertRaises(ValueError):
            calcular(np.zeros((32,32)))

    def test_png_retangular_transparencia_e_inversao(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta)/'entrada.png'
            rgba = np.full((40,80,4), 255, dtype='uint8')
            rgba[:,:40,3] = 0
            Image.fromarray(rgba).save(p)
            m = carregar_png(p, 80)
            self.assertEqual(m.shape, (40,80))
            self.assertEqual(m[:,:40].sum(), 0)
            np.testing.assert_array_equal(carregar_png(p, 80, inverter=True), 1-m)
            self.assertEqual(calcular(m, largura_mm=2)['altura_mm'], 1)

    def test_exportacao_e_recarga(self):
        with tempfile.TemporaryDirectory() as pasta:
            p = Path(pasta)
            m = exemplo('simples', 64)
            salvar_mascara(m, p/'mascara.png')
            np.testing.assert_array_equal(carregar_png(p/'mascara.png',64), m)
            r = calcular(m)
            for escala in ('linear', 'log'):
                salvar(r, desenhar(r, escala), p/f'{escala}.png')
                with np.load(p/f'{escala}.npz') as dados:
                    np.testing.assert_allclose(dados['intensidade'], r['intensidade'])
                self.assertEqual(np.loadtxt(p/f'{escala}.csv',delimiter=',',skiprows=1).shape, (256,2))
                with Image.open(p/f'{escala}.png') as imagem:
                    self.assertGreater(imagem.width, 100)
                self.assertTrue((p/f'{escala}.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
