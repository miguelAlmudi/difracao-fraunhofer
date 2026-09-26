"""Etapa 2: figuras e salvamento, também utilizáveis sem interface."""
import json
from pathlib import Path
import numpy as np
from matplotlib.figure import Figure


def desenhar(resultado, escala='log', figura=None):
    fig = figura if figura is not None else Figure(figsize=(10, 7), dpi=100)
    fig.clear()
    r = resultado
    ax_m, ax_i, ax_c = fig.subplots(1, 3)
    m, intensidade = r['mascara'], r['intensidade']
    ax_m.imshow(m, cmap='gray', vmin=0, vmax=1,
                extent=[-r['largura_mm']/2, r['largura_mm']/2,
                        -r['altura_mm']/2, r['altura_mm']/2])
    ax_m.set(title='Abertura (branco = luz)', xlabel='x (mm)', ylabel='y (mm)')
    x, y = r['x_m']*1e3, r['y_m']*1e3
    dx, dy = x[1]-x[0], y[1]-y[0]
    dados = np.log10(intensidade+1e-12) if escala == 'log' else intensidade
    img = ax_i.imshow(dados, origin='lower', cmap='inferno',
                      extent=[x[0]-dx/2, x[-1]+dx/2, y[0]-dy/2, y[-1]+dy/2],
                      vmin=-6 if escala == 'log' else 0, vmax=0 if escala == 'log' else 1)
    # Região central legível; a barra de ferramentas permite ampliar/mover.
    limite = min(max(abs(x)), max(abs(y)), 12*r['onda_nm']*1e-6*r['distancia_m']/(r['largura_mm']*1e-3))
    ax_i.set(xlim=(-limite, limite), ylim=(-limite, limite),
             title='Difração no anteparo', xlabel='x (mm)', ylabel='y (mm)')
    fig.colorbar(img, ax=ax_i, shrink=0.65, label='log10(I/Imax)' if escala == 'log' else 'I/Imax')
    corte = intensidade[len(y)//2]
    if escala == 'log':
        ax_c.semilogy(x, np.maximum(corte, 1e-12))
        ax_c.set_ylim(1e-6, 1.1)
    else:
        ax_c.plot(x, corte)
        ax_c.set_ylim(0, 1.05)
    ax_c.set(xlim=(-limite, limite), title='Corte horizontal (y = 0)', xlabel='x (mm)', ylabel='I/Imax')
    ax_c.grid(alpha=0.25)
    ax_c.set_box_aspect(1)
    fig.suptitle(f"Fraunhofer • λ = {r['onda_nm']:g} nm • z = {r['distancia_m']:g} m")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


def salvar(resultado, figura, destino):
    """PNG dos gráficos + NPZ completo + CSV do corte + parâmetros JSON."""
    base = Path(destino).with_suffix('')
    figura.savefig(base.with_suffix('.png'), dpi=160)
    r = resultado
    np.savez_compressed(base.with_suffix('.npz'), **r)
    corte = r['intensidade'][len(r['y_m'])//2]
    np.savetxt(base.with_suffix('.csv'), np.column_stack((r['x_m']*1e3, corte)),
               delimiter=',', header='x_mm,intensidade_normalizada', comments='')
    parametros = {k: v for k, v in r.items() if not isinstance(v, np.ndarray)}
    parametros['convencao'] = 'Branco=passagem; largura da imagem inteira; pixels quadrados.'
    base.with_suffix('.json').write_text(json.dumps(parametros, ensure_ascii=False, indent=2), encoding='utf-8')
