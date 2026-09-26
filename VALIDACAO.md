# Validação realizada

Sandbox: oito testes físicos adicionais passaram (expansão gaussiana analítica,
energia, fontes independentes, bloqueio por aberturas, inclinação e sensores).
O teste de integração exercitou seleção/arraste, quatro formas, inclusão,
duplicação, remoção, alternância linear/log, salvar/abrir JSON e reabertura da
janela. As mesmas rotinas dos eventos de mouse foram chamadas com coordenadas
de teste; os diálogos de arquivo receberam respostas automáticas. Os sete testes
anteriores de Fraunhofer também passaram.

Atualização da montagem visual: testadas as três aberturas, escalas linear/log,
atualização da distância, área visível da parede, abertura sem duplicar janelas,
fechamento e reabertura. A imagem exportada foi inspecionada visualmente.

Ambiente: Windows, Python 3.12, NumPy 2.5.3, Pillow 12.3.0, Matplotlib 3.11.2 e Tk 8.6.

As etapas foram implementadas e verificadas separadamente:

1. Máscaras PNG e núcleo físico: fenda simples comparada com sinc²; dupla fenda
   comparada com sinc² vezes cos²; abertura circular verificada por simetria e
   primeiro mínimo próximo de 1,22 λz/D. Escalas físicas e normalização verificadas.
2. Gráficos e arquivos: escalas linear/log, exportação PNG/CSV/NPZ/JSON e recarga
   dos dados verificados. Gráfico exportado inspecionado visualmente.
3. Interface Tkinter executada: exemplos, mudança de escala, carregamento PNG,
   inversão, vírgula decimal, rejeição de comprimento de onda zero e exportação
   exercitados por chamadas aos mesmos comandos usados pelos botões.

Resultado: os 7 testes em `testes.py` passaram, assim como o teste de integração
da GUI. Os diálogos de escolher/salvar arquivo e erro foram substituídos por
respostas automáticas no teste; a janela Tkinter e os gráficos foram executados
de verdade. Isso não substitui testar manualmente a aparência em outros monitores.

O Python disponível no ambiente de execução exigiu instalação local de Matplotlib
e execução fora do isolamento para acessar Tk/Tcl. Nenhuma configuração específica
desse ambiente é exigida pelo projeto portátil; em uma instalação normal do Python
para Windows, siga `LEIA-ME.md`.
