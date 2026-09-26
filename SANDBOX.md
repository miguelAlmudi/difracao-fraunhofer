# Sandbox óptico

Na tela principal, clique em **Abrir sandbox óptico…**. Também pode executar
`.venv\Scripts\python sandbox.py` diretamente.

## Experimentar

1. O exemplo inicial tem uma fonte, uma dupla fenda e um anteparo.
2. Clique e arraste o símbolo de um objeto. Horizontal = posição longitudinal z
   em metros; vertical = deslocamento y em milímetros. O cálculo atualiza ao soltar.
3. Use **＋ Fonte**, **＋ Abertura**, **＋ Anteparo**, **Duplicar** e **Remover**.
4. Selecione uma abertura e escolha fenda, dupla fenda, círculo ou retângulo.
   Edite as dimensões e clique em **Aplicar e simular**. Fenda e retângulo são
   ambos furos retangulares; a razão entre largura e altura define o aspecto.
5. Selecione uma fonte para alterar raio, potência relativa ou inclinação.
6. Clique num anteparo ou escolha seu número em **Ver anteparo**. O gráfico mostra
   a distribuição 2D e a potência relativa captada dentro de sua área quadrada.
7. **Salvar cena** grava posições e propriedades em JSON. **Abrir cena** recupera
   a montagem; existe um exemplo em `exemplos/sandbox.json`. **Salvar PNG** exporta
   o gráfico do anteparo escolhido.

Os campos do objeto só entram na cena após **Aplicar e simular**. Os parâmetros
globais de comprimento de onda e resolução são aplicados por **Simular**.
A cena do sandbox é independente dos parâmetros da janela de Fraunhofer.

## Modelo físico

Esta tela usa propagação escalar de Fresnel, paraxial, por FFT entre planos. Ela
permite calcular o campo próximo e a passagem por várias aberturas, ao contrário
de aplicar Fraunhofer separadamente a cada máscara.

O propagador é `H = exp(-i*pi*lambda*dz*(fx²+fy²))`. Em cada abertura, o campo é
multiplicado por sua máscara binária. Os objetos são ordenados pela posição z.
No mesmo z, entram primeiro as fontes, depois as aberturas e por fim os detectores.
Uma fonte não ilumina objetos que estão à sua esquerda. Não há reflexões.

Cada fonte é um feixe gaussiano com cintura no plano onde está colocada, com raio
de intensidade 1/e² dado pelo tamanho. A inclinação vertical varia de −2 a +2 mrad.
O comprimento de onda é compartilhado por todas as fontes. As fontes são
mutuamente incoerentes: propagam separadamente e suas intensidades se somam.
A difração de cada feixe em uma dupla fenda produz interferência normalmente.
Não há interferência entre duas fontes distintas nesta versão.

As aberturas são furos em placas opacas que cobrem o domínio. A dupla fenda usa
separação entre centros. Círculo usa o tamanho como diâmetro. Todos os objetos
ficam centrados em x=0; o arraste movimenta z e y. O editor lateral não é uma
representação em escala, e seus símbolos têm tamanho fixo para facilitar o arraste.

Os anteparos são **sensores virtuais não bloqueantes**, para comparar diversos
planos simultaneamente. Movê-los em y altera a região observada, não o campo
propagado. Uma parede opaca real impediria a luz de chegar aos planos seguintes.
Os traços pontilhados são eixos dos feixes sem obstáculos, não trajetórias calculadas.

## Limites numéricos

- Até 16 objetos, incluindo no máximo 4 fontes; bancada de 0 a 3 m.
- Janela útil de 4 mm e domínio de cálculo de 8 mm, com resolução de 128, 256 ou
  512 amostras por 4 mm. A extensão adicional reduz efeitos das bordas da FFT.
- A FFT impõe periodicidade. Um aviso aparece quando mais de 1% da energia em um
  plano avaliado está na faixa externa do domínio. Esse aviso não detecta todos
  os artefatos: luz que já voltou pela borda também pode contaminar a região central.
- Aberturas pequenas exigem mais resolução; distâncias longas ou grandes
  inclinações podem espalhar luz além da janela. Reduza distância/inclinação e
  compare resoluções para avaliar a estabilidade do resultado.
- Cores mostram intensidade normalizada pelo máximo de todo o plano do sensor;
  a área visível pode não incluir esse máximo. Use a potência relativa captada
  para comparar transmissão, pois a normalização esconde mudanças de brilho absoluto.
- A escala log realça intensidades fracas e também pode realçar artefatos numéricos.

É um simulador didático exploratório, sem polarização, lentes, espelhos, reflexão,
obstáculos volumétricos ou propagação em ângulos grandes.

Referência do método: [Numerical Beam Propagation, R. Paschotta](https://www.rp-photonics.com/numerical_beam_propagation.html).

## Testes

`python testes_sandbox.py` verifica expansão gaussiana contra solução analítica,
conservação de energia em espaço livre, soma de fontes, sequência de aberturas,
inclinação e sensores não bloqueantes. Os testes anteriores de Fraunhofer continuam
em `testes.py`.
