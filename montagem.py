"""Vista didática da montagem. A parede usa a intensidade calculada por FFT."""
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle, Circle
from matplotlib.transforms import Affine2D


def desenhar_montagem(r, escala='log', largura_parede_mm=80, figura=None):
    fig = figura if figura is not None else Figure(figsize=(12, 6), dpi=100)
    fig.clear()
    fig.set_facecolor('#101827')
    ax = fig.add_axes((0.02, 0.08, 0.96, 0.82))
    ax.set(xlim=(0, 12), ylim=(0, 6.5), aspect='equal')
    ax.axis('off')
    cor = '#ffe090'
    texto = '#e5edf8'
    # Os feixes são apenas uma indicação do caminho da luz, não raios calculados.
    ax.add_patch(Polygon([(1.7, 2.3), (4, 1.5), (4, 4.5), (1.7, 3.7)],
                         color=cor, alpha=0.10))
    ax.add_patch(Polygon([(4.65, 2.7), (9, 1), (11.2, 1.7), (11.2, 5.7),
                         (9, 5), (4.65, 3.7)], color=cor, alpha=0.09))
    for yy in (2.3, 2.8, 3.3, 3.8):
        ax.annotate('', xy=(3.9, yy), xytext=(2.1, yy),
                    arrowprops=dict(arrowstyle='->', color=cor, alpha=0.55, lw=1.2))
    ax.add_patch(Rectangle((0.35, 2.45), 1.3, 1.1, facecolor='#425776', edgecolor='#91a9c8'))
    ax.add_patch(Circle((1.65, 3), 0.24, color=cor))
    ax.text(0.95, 4.4, 'FONTE DE LUZ', color=texto, ha='center', weight='bold')
    ax.text(0.95, 2.05, f"λ = {r['onda_nm']:g} nm", color=cor, ha='center')
    ax.text(2.8, 4.45, 'Iluminação\nplana e uniforme', color=texto, ha='center', fontsize=9)

    abertura = Affine2D.from_values(1.3, 0.45, 0, 3, 4, 1.5)
    ax.imshow(r['mascara'], origin='upper', extent=(0, 1, 0, 1), cmap='gray',
              vmin=0, vmax=1, interpolation='nearest', transform=abertura+ax.transData, zorder=4)
    ax.add_patch(Polygon(abertura.transform([(0,0),(1,0),(1,1),(0,1)]),
                         fill=False, edgecolor='#94a3b8', linewidth=2, zorder=5))
    ax.text(4.65, 5.4, 'ABERTURA', color=texto, ha='center', weight='bold')
    ax.text(4.65, 1.1, f"Imagem: {r['largura_mm']:g} × {r['altura_mm']:g} mm",
            color=texto, ha='center', fontsize=9)
    ax.annotate('', xy=(9, 0.6), xytext=(5.3, 0.6),
                arrowprops=dict(arrowstyle='<->', color='#94a3b8'))
    ax.text(7.15, 0.8, f"Distância: {r['distancia_m']:g} m", ha='center', color=texto)
    ax.text(7.1, 4.5, 'Luz difratada', ha='center', color=cor)

    # Amostra uma área física fixa: mudar λ ou z altera o tamanho das franjas.
    limite = largura_parede_mm/2
    coordenadas = np.linspace(-limite, limite, 400)*1e-3
    x, y = r['x_m'], r['y_m']
    ix = np.clip(np.searchsorted(x, coordenadas), 0, len(x)-1)
    iy = np.clip(np.searchsorted(y, coordenadas), 0, len(y)-1)
    dados = r['intensidade'][np.ix_(iy, ix)].copy()
    validos = ((coordenadas >= y[0]) & (coordenadas <= y[-1]))[:, None] & (
        (coordenadas >= x[0]) & (coordenadas <= x[-1]))[None, :]
    dados[~validos] = np.nan
    if escala == 'log':
        dados = np.clip((np.log10(dados+1e-12)+6)/6, 0, 1)
    parede = Affine2D.from_values(2.2, 0.7, 0, 4, 9, 1)
    ax.imshow(dados, origin='lower', extent=(0, 1, 0, 1), cmap='inferno',
              vmin=0, vmax=1, interpolation='bilinear', transform=parede+ax.transData, zorder=4)
    ax.add_patch(Polygon(parede.transform([(0,0),(1,0),(1,1),(0,1)]),
                         fill=False, edgecolor='#c5d3e7', linewidth=2, zorder=5))
    ax.text(10.1, 6.05, 'ANTEPARO', color=texto, ha='center', weight='bold')
    ax.text(10.1, 0.55, f"Área: {largura_parede_mm:g} × {largura_parede_mm:g} mm",
            color=texto, ha='center', fontsize=9)
    fig.suptitle('Da fonte ao padrão de difração', color='white', fontsize=17, y=0.96)
    nota = 'Montagem e feixes ilustrativos, fora de escala. Parede: intensidade calculada; cores representam brilho.'
    nota += '\nEscala '+('logarítmica (realça franjas fracas).' if escala == 'log' else 'linear.')
    if not validos.all():
        nota += ' Parte da parede está fora da região calculada.'
    if r['fresnel'] >= 0.1:
        nota += ' Atenção: condição de campo distante não satisfeita pelo critério adotado.'
    fig.text(0.5, 0.025, nota, ha='center', color='#bac8dc', fontsize=9)
    return fig
