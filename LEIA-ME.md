# Física 4 — Difração de Fraunhofer

Aplicativo simples em Python, NumPy, Pillow, Matplotlib e Tkinter. Branco deixa
a luz passar; preto bloqueia. Inclui fenda simples, dupla fenda e abertura circular.

## Executar no Windows

Instale Python 3.12 ou superior pelo python.org, incluindo Tcl/Tk e o launcher `py`.
Abra o terminal nesta pasta e execute, apenas na primeira vez:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Depois dê dois cliques em **iniciar.bat**, ou execute:

```powershell
.venv\Scripts\python app.py
```

Escolha um exemplo ou carregue um PNG, ajuste os parâmetros e clique em **Calcular**.
Escolha **Linear** ou **Logarítmica**. A barra abaixo dos gráficos permite zoom,
deslocamento e restauração da visualização. Valores decimais aceitam ponto ou vírgula.

Clique em **Ver montagem visual…** para abrir uma segunda janela com fonte à
esquerda, abertura no meio e o padrão na parede à direita. Ela acompanha os
cálculos e a escala linear/log da janela principal. O controle de largura da área
visível permite ampliar a região central do anteparo; **Salvar imagem…** exporta
a montagem. As dimensões do desenho e os feixes são ilustrativos, fora de escala;
somente o padrão na parede vem do cálculo físico. As cores indicam intensidade,
não a cor espectral real da luz. A área visível é mantida fixa ao mudar os parâmetros,
de modo que a expansão ou contração das franjas seja perceptível.

## Testar por partes

Há também uma bancada interativa em **Abrir sandbox óptico…**, com múltiplos objetos
arrastáveis e propagação de Fresnel. Consulte [SANDBOX.md](SANDBOX.md).

1. `python fisica.py`: recria os três PNGs na pasta `exemplos`.
2. `python testes.py`: verifica mínimos de difração, curvas analíticas de fendas,
   simetria circular, unidades, leitura de PNG, validações e exportação.
3. `python app.py`: abre a interface. Troque os três exemplos, carregue um PNG,
   altere a distância e salve. Use o Python da `.venv` nos comandos acima.

## O que significam os parâmetros

- **Largura total da imagem (mm)**: inclui as margens pretas; não é a largura da fenda.
  A proporção do PNG é preservada, com pixels quadrados e altura física automática.
- **Comprimento de onda (nm)**: comprimento de onda no meio de propagação.
- **Distância (m)**: da abertura até o anteparo.
- **Resolução**: número de amostras no maior lado (32 a 512). Comece com 256;
  50 também funciona, mas pode perder aberturas estreitas. Aumentar a resolução
  permite verificar convergência. Estruturas menores que um pixel podem desaparecer.
- **Limiar**: cinza a partir do qual um pixel passa a ser branco. Transparência é
  composta sobre preto antes da conversão. A inversão é aplicada depois do limiar.

Nos exemplos, com largura da imagem de 1 mm:

| Exemplo | Dimensões físicas |
|---|---|
| Fenda simples | largura 0,125 mm; altura 0,5 mm |
| Dupla fenda | cada largura 0,0625 mm; separação entre centros 0,25 mm; altura 0,5 mm |
| Círculo | diâmetro 0,25 mm |

Essas dimensões são exatas para as fendas na grade padrão de 256; o círculo tem
contorno discretizado. Outras resoluções podem arredondar as bordas.

## Modelo físico e limites

Iluminação plana, monocromática, coerente e uniforme; máscara binária de amplitude.
O campo é calculado por `fftshift(fft2(mascara))`, com zeros acrescentados para
amostrar melhor o padrão. A intensidade é `abs(campo)**2`, normalizada pelo máximo.
Os eixos são `x = lambda*z*fx` e `y = lambda*z*fy`, em aproximação paraxial.
Multiplicar lambda ou distância por dois duplica a escala espacial do padrão.

A tela mostra uma região central; os dados completos ficam no NPZ. O mapa log
mostra de −6 a 0 em `log10(I/Imax + 1e-12)`; valores mais baixos saturam na cor
escura. O corte usa intensidade normalizada em eixo logarítmico.

O indicador de Fresnel usa `F = a²/(lambda*z)`, sendo `a` a metade da diagonal
do retângulo que contém a abertura. `F < 0,1` é um critério aproximado conservador
para campo distante. Valores maiores geram aviso, mas o cálculo continua sendo
Fraunhofer. A aproximação dos eixos exige ângulos pequenos (`|x|, |y| << z`).
Não calcula propagação de Fresnel, potência absoluta ou o ponto de Poisson em campo
próximo. Uma máscara invertida representa um obstáculo dentro de uma janela
iluminada finita, cujas bordas também difratam.

Referência física: [Fraunhofer Diffraction — laboratório de Oxford](https://users.physics.ox.ac.uk/~lvovsky/471/labs/fraunhofer.pdf).

## Salvamento

**Salvar gráficos e dados** recalcula os parâmetros atuais e grava quatro arquivos:

- `.png`: os três gráficos na escala e visualização padrão selecionadas;
- `.csv`: corte horizontal, com x em mm e intensidade normalizada;
- `.npz`: matriz completa, máscara, eixos em metros e parâmetros (abrir com NumPy);
- `.json`: parâmetros e identificação da entrada.

O salvamento refaz a visualização padrão. Para salvar apenas um zoom personalizado,
use o botão de disquete da barra do Matplotlib.
Exemplos calculados estão em `resultados`.
