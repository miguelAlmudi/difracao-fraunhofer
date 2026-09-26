# Difração de Fraunhofer — Física 4

Simulador acadêmico em Python com interface Tkinter, cálculo NumPy e gráficos
Matplotlib. Carrega máscaras PNG e inclui fenda simples, dupla fenda e círculo.

- Parâmetros físicos: largura da imagem, comprimento de onda e distância.
- Intensidade linear/logarítmica e corte horizontal.
- Montagem visual com fonte, abertura e anteparo.
- Sandbox óptico: arraste múltiplas fontes, aberturas e anteparos; salve cenas.
- Exportação de gráficos e dados em PNG, CSV, NPZ e JSON.

## Executar no Windows

Instale Python com Tcl/Tk e execute nesta pasta:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Depois da instalação, também pode abrir pelo `iniciar.bat`.

## Testes

```powershell
.venv\Scripts\python testes.py
.venv\Scripts\python testes_sandbox.py
```

Veja [instruções e modelo físico](LEIA-ME.md) e [validação realizada](VALIDACAO.md).
A largura informada corresponde à imagem inteira, incluindo margens pretas.
A montagem visual é ilustrativa e fora de escala; o padrão no anteparo é calculado.

Para abrir diretamente a bancada interativa: `python sandbox.py`.
Consulte [o guia do sandbox](SANDBOX.md) para os controles e limites físicos.
