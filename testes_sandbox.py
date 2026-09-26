"""Validação física independente para o sandbox: python testes_sandbox.py."""
import copy
import unittest
import numpy as np
from sandbox_fisica import cena_inicial, objeto, simular, validar, propagar


class TestesSandbox(unittest.TestCase):
    def cena(self):
        c=cena_inicial()
        c['resolucao']=128
        return c

    def test_propagacao_gaussiana_analitica(self):
        n=256
        dx=8e-3/n
        e=(np.arange(n)-n/2)*dx
        x,y=np.meshgrid(e,e)
        w=0.3e-3
        onda=633e-9
        z=0.5
        u=np.exp(-(x*x+y*y)/w**2)
        f=np.fft.fftfreq(n,dx)
        v=propagar(u,z,onda,f[:,None]**2+f[None,:]**2)
        intensidade=abs(v)**2
        raio_observado=2*np.sqrt((intensidade*x*x).sum()/intensidade.sum())
        raio_teorico=w*np.sqrt(1+(z/(np.pi*w*w/onda))**2)
        self.assertAlmostEqual(raio_observado/raio_teorico,1,places=5)
        self.assertAlmostEqual(float(intensidade.sum()/np.sum(abs(u)**2)),1,places=10)

    def test_fontes_incoerentes_somam(self):
        c=self.cena()
        r=simular(c)['detectores'][3]
        segunda=copy.deepcopy(c['objetos'][0])
        segunda['id']=4
        c['objetos'].append(segunda)
        np.testing.assert_allclose(simular(c)['detectores'][3],2*r,rtol=1e-10)

    def test_sensor_nao_bloqueia(self):
        c=self.cena()
        original=simular(c)['detectores'][3]
        c['objetos'].append(objeto('anteparo',4,0.5))
        np.testing.assert_allclose(simular(c)['detectores'][3],original,atol=1e-7)

    def test_fonte_a_direita_nao_ilumina(self):
        c=self.cena()
        c['objetos'][0]['z']=3
        self.assertEqual(simular(c)['detectores'][3].max(),0)

    def test_duas_aberturas_bloqueiam(self):
        c=self.cena()
        a=c['objetos'][1]
        a.update(forma='circulo',tamanho=0.2,y=-0.7)
        b=copy.deepcopy(a)
        b.update(id=4,y=0.7)
        c['objetos'].append(b)
        self.assertEqual(simular(c)['detectores'][3].max(),0)

    def test_abertura_reduz_potencia(self):
        c=self.cena()
        r=simular(c)
        transmitida=r['detectores'][3].sum()*r['dx_m']**2
        self.assertGreater(transmitida,0)
        self.assertLess(transmitida,1)

    def test_inclinacao_desloca_feixe(self):
        c=self.cena()
        c['objetos']=[objeto('fonte',1,0),objeto('anteparo',2,1)]
        c['objetos'][0]['angulo']=0.5
        r=simular(c)
        i=r['detectores'][2]
        centro=(i*r['eixo_mm'][:,None]).sum()/i.sum()
        self.assertAlmostEqual(float(centro),0.5,places=3)

    def test_cenas_invalidas_e_vazias(self):
        for chave,valor in [('onda_nm',float('nan')),('resolucao',2048),('objetos',None)]:
            c=self.cena()
            c[chave]=valor
            with self.assertRaises(ValueError): validar(c)
        c=self.cena()
        c['objetos'][1]['tamanho']=2
        with self.assertRaises(ValueError): validar(c)
        c=self.cena()
        c['objetos']=[]
        self.assertEqual(len(simular(c)['avisos']),2)


if __name__=='__main__':
    unittest.main(verbosity=2)
