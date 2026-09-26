"""Propagação escalar paraxial entre planos; fontes mutuamente incoerentes."""
import copy
import numpy as np

FORMAS = ('fenda', 'dupla', 'circulo', 'retangulo')


def objeto(tipo, identificador, z=0.4, y=0.0):
    return dict(id=identificador, tipo=tipo, z=z, y=y, forma='dupla',
                tamanho=0.2 if tipo == 'abertura' else (0.6 if tipo == 'fonte' else 3.0),
                altura=1.0, separacao=0.6, potencia=1.0, angulo=0.0)


def cena_inicial():
    return dict(versao=1, onda_nm=633.0, resolucao=256, objetos=[
        objeto('fonte', 1, 0.1), objeto('abertura', 2, 0.3), objeto('anteparo', 3, 0.8)])


def validar(cena):
    if not isinstance(cena, dict) or cena.get('versao') != 1:
        raise ValueError('Arquivo de cena inválido (versão 1 esperada).')
    def numero(v, minimo, maximo, nome):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) or not minimo <= v <= maximo:
            raise ValueError(f'{nome}: use um número entre {minimo} e {maximo}.')
    numero(cena.get('onda_nm'), 380, 780, 'Comprimento de onda (nm)')
    if cena.get('resolucao') not in (128, 256, 512):
        raise ValueError('Resolução: 128, 256 ou 512.')
    itens = cena.get('objetos')
    if not isinstance(itens, list) or len(itens) > 16:
        raise ValueError('Use no máximo 16 objetos.')
    ids = set()
    for o in itens:
        if not isinstance(o, dict) or o.get('tipo') not in ('fonte', 'abertura', 'anteparo'):
            raise ValueError('Objeto desconhecido.')
        ident = o.get('id')
        if not isinstance(ident, int) or isinstance(ident, bool) or ident in ids or ident < 1:
            raise ValueError('Identificadores de objetos inválidos.')
        ids.add(ident)
        for chave, minimo, maximo in [('z', 0, 3), ('y', -1.5, 1.5),
            ('tamanho', 0.08, 3), ('altura', 0.08, 3), ('separacao', 0.08, 3),
            ('potencia', 0.01, 10), ('angulo', -2, 2)]:
            numero(o.get(chave), minimo, maximo, chave)
        if o.get('forma') not in FORMAS:
            raise ValueError('Forma inválida.')
        if o['tipo'] == 'abertura' and o['forma'] == 'dupla' and o['separacao'] <= o['tamanho']:
            raise ValueError('Na dupla fenda, a separação deve superar a largura de cada fenda.')
    if sum(o['tipo'] == 'fonte' for o in itens) > 4:
        raise ValueError('Use no máximo quatro fontes.')
    return copy.deepcopy(cena)


def propagar(campo, distancia, onda, f2):
    """H(fx,fy)=exp(-i*pi*lambda*z*(fx²+fy²)); fase global omitida."""
    if distancia == 0:
        return campo.copy()
    return np.fft.ifft2(np.fft.fft2(campo)*np.exp(-1j*np.pi*onda*distancia*f2))


def mascara(o, x, y):
    xx = x*1e3
    yy = y*1e3-o['y']
    a = o['tamanho']
    if o['forma'] == 'circulo':
        return xx**2+yy**2 <= (a/2)**2
    horizontal = abs(xx) <= a/2
    if o['forma'] == 'dupla':
        horizontal = abs(abs(xx)-o['separacao']/2) <= a/2
    return horizontal & (abs(yy) <= o['altura']/2)


def simular(cena):
    cena = validar(cena)
    n = cena['resolucao']
    # Janela útil de 4 mm; domínio de 8 mm para reduzir retorno periódico da FFT.
    dx = 4e-3/n
    eixo = (np.arange(2*n)-n)*dx
    x, y = np.meshgrid(eixo, eixo)
    freq = np.fft.fftfreq(2*n, dx)
    f2 = freq[:, None]**2+freq[None, :]**2
    onda = cena['onda_nm']*1e-9
    prioridade = {'fonte': 0, 'abertura': 1, 'anteparo': 2}
    itens = sorted(cena['objetos'], key=lambda o: (o['z'], prioridade[o['tipo']], o['id']))
    detectores = {o['id']: np.zeros((2*n, 2*n)) for o in itens if o['tipo'] == 'anteparo'}
    avisos = []
    fontes = [o for o in itens if o['tipo'] == 'fonte']
    if not fontes:
        avisos.append('Adicione uma fonte de luz.')
    if not detectores:
        avisos.append('Adicione um anteparo para observar o resultado.')
    borda = (abs(x) > 3.4e-3) | (abs(y) > 3.4e-3)
    for fonte in fontes:
        raio = fonte['tamanho']*1e-3
        campo = np.exp(-(x*x+(y-fonte['y']*1e-3)**2)/raio**2).astype(complex)
        campo *= np.sqrt(fonte['potencia']/(np.sum(abs(campo)**2)*dx**2))
        campo *= np.exp(2j*np.pi/onda*np.sin(fonte['angulo']*1e-3)*y)
        z = fonte['z']
        for o in itens:
            if o['tipo'] == 'fonte' or o['z'] < fonte['z']:
                continue
            campo = propagar(campo, o['z']-z, onda, f2)
            z = o['z']
            intensidade = abs(campo)**2
            total = intensidade.sum()
            if total > 0 and intensidade[borda].sum()/total > 0.01:
                avisos.append('Luz próxima à borda do domínio: resultado pode ter artefatos periódicos.')
            if o['tipo'] == 'abertura':
                campo *= mascara(o, x, y)
                if o['tamanho']*1e-3 < 4*dx:
                    avisos.append('Abertura pouco amostrada: aumente a resolução.')
            else:
                detectores[o['id']] += intensidade
    return dict(eixo_mm=eixo*1e3, detectores=detectores,
                avisos=list(dict.fromkeys(avisos)), dx_m=dx)
