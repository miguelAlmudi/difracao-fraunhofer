"""Etapa 1: máscaras e difração. Todas as distâncias internas estão em metros."""
from pathlib import Path
import numpy as np
from PIL import Image


def exemplo(nome, n=256):
    """Geometrias em frações da largura/altura total da imagem."""
    y, x = np.mgrid[:n, :n]
    x = (x + 0.5) / n - 0.5
    y = (y + 0.5) / n - 0.5
    if nome == 'simples':
        m = (abs(x) < 0.0625) & (abs(y) < 0.25)
    elif nome == 'dupla':
        m = (abs(abs(x) - 0.125) < 0.03125) & (abs(y) < 0.25)
    elif nome == 'circulo':
        m = x*x + y*y < 0.125**2
    else:
        raise ValueError('Exemplo desconhecido.')
    return m.astype(float)


def carregar_png(caminho, n=256, limiar=128, inverter=False):
    if not 32 <= n <= 512:
        raise ValueError('A resolução deve ficar entre 32 e 512.')
    if not 1 <= limiar <= 255:
        raise ValueError('O limiar deve ficar entre 1 e 255.')
    with Image.open(caminho) as original:
        if original.format != 'PNG':
            raise ValueError('Selecione um arquivo PNG.')
        # Transparência é composta sobre preto: transparente bloqueia a luz.
        rgba = original.convert('RGBA')
        fundo = Image.new('RGBA', rgba.size, (0, 0, 0, 255))
        cinza = Image.alpha_composite(fundo, rgba).convert('L')
        # Preserva a proporção. A altura física é deduzida da largura.
        w, h = cinza.size
        tamanho = (max(1, round(n*w/max(w, h))), max(1, round(n*h/max(w, h))))
        cinza = cinza.resize(tamanho, Image.Resampling.LANCZOS)
        mascara = (np.asarray(cinza) >= limiar).astype(float)
    return 1 - mascara if inverter else mascara


def salvar_mascara(mascara, caminho):
    Image.fromarray((mascara*255).astype('uint8')).save(caminho)


def calcular(mascara, largura_mm=1.0, onda_nm=633.0, distancia_m=5.0, padding=4):
    valores = np.array([largura_mm, onda_nm, distancia_m], dtype=float)
    if not np.isfinite(valores).all() or (valores <= 0).any():
        raise ValueError('Largura, comprimento de onda e distância devem ser positivos e finitos.')
    m = np.asarray(mascara, dtype=float)
    if m.ndim != 2 or not m.size or not np.isfinite(m).all() or not np.isin(m, [0, 1]).all():
        raise ValueError('A máscara deve ser uma matriz binária 2D.')
    if not m.any():
        raise ValueError('A máscara está toda preta: não há passagem de luz.')
    if padding not in (1, 2, 4) or max(m.shape) > 512:
        raise ValueError('Use padding 1, 2 ou 4 e máscara de até 512 pixels por lado.')
    h, w = m.shape
    largura = largura_mm*1e-3
    onda = onda_nm*1e-9
    dx = largura/w
    altura = h*dx
    # Acrescentar zeros melhora a amostragem da figura, sem mudar a abertura.
    # PNG enumera linhas de cima para baixo; o eixo físico y cresce para cima.
    campo = np.fft.fftshift(np.fft.fft2(np.flipud(m), s=(h*padding, w*padding)))
    intensidade = abs(campo)**2
    intensidade /= intensidade.max()
    x = np.fft.fftshift(np.fft.fftfreq(w*padding, d=dx))*onda*distancia_m
    y = np.fft.fftshift(np.fft.fftfreq(h*padding, d=dx))*onda*distancia_m
    linhas, colunas = np.where(m > 0)
    # Raio conservador do retângulo que contém a abertura iluminada.
    raio = 0.5*np.hypot((colunas.max()-colunas.min()+1)*dx,
                        (linhas.max()-linhas.min()+1)*dx)
    fresnel = raio**2/(onda*distancia_m)
    return dict(mascara=m, intensidade=intensidade, x_m=x, y_m=y,
                largura_mm=largura_mm, altura_mm=altura*1e3, onda_nm=onda_nm,
                distancia_m=distancia_m, fresnel=fresnel, padding=padding)


if __name__ == '__main__':
    pasta = Path(__file__).parent/'exemplos'
    pasta.mkdir(exist_ok=True)
    for nome in ('simples', 'dupla', 'circulo'):
        salvar_mascara(exemplo(nome), pasta/f'{nome}.png')
    print('Três máscaras PNG geradas em', pasta)
