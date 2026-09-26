"""Etapa 3: interface básica Tkinter. Execute: python app.py."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from fisica import exemplo, carregar_png, calcular
from graficos import desenhar, salvar
from montagem import desenhar_montagem
from sandbox import Sandbox


def criar_app():
    janela = tk.Tk()
    janela.title('Física 4 — Difração de Fraunhofer')
    janela.geometry('1200x760')
    janela.minsize(1000, 660)
    painel = ttk.Frame(janela, padding=12)
    painel.pack(side='left', fill='y')
    area = ttk.Frame(janela)
    area.pack(side='right', fill='both', expand=True)
    estado = {'arquivo': None, 'resultado': None}
    montagem = {'janela': None}
    bancada = {'app': None}

    def abrir_sandbox():
        if bancada['app'] is None or not bancada['app'].janela.winfo_exists():
            bancada['app'] = Sandbox(janela)
        else:
            bancada['app'].janela.lift()
    campos = {}
    ttk.Label(painel, text='Difração de Fraunhofer', font=('', 13, 'bold')).pack(anchor='w', pady=(0, 12))
    fonte = tk.StringVar(value='simples')
    ttk.Label(painel, text='Abertura de exemplo').pack(anchor='w')
    escolha = ttk.Combobox(painel, textvariable=fonte, state='readonly',
                           values=('simples', 'dupla', 'circulo'))
    escolha.pack(fill='x')
    nome = tk.StringVar(value='Exemplo: simples')
    ttk.Label(painel, textvariable=nome, wraplength=230).pack(anchor='w', pady=6)

    def carregar():
        caminho = filedialog.askopenfilename(title='Escolher máscara PNG', filetypes=[('Imagem PNG', '*.png')])
        if caminho:
            estado['arquivo'] = caminho
            nome.set(Path(caminho).name)
            atualizar()

    ttk.Button(painel, text='Carregar PNG…', command=carregar).pack(fill='x', pady=(0, 10))
    for chave, rotulo, padrao in (
        ('largura', 'Largura total da imagem (mm)', '1'),
        ('onda', 'Comprimento de onda (nm)', '633'),
        ('distancia', 'Distância ao anteparo (m)', '5'),
        ('n', 'Resolução: maior lado (32–512)', '256'),
        ('limiar', 'Limiar do PNG (1–255)', '128')):
        ttk.Label(painel, text=rotulo).pack(anchor='w', pady=(5, 0))
        campos[chave] = tk.StringVar(value=padrao)
        ttk.Entry(painel, textvariable=campos[chave]).pack(fill='x')
    inverter = tk.BooleanVar(value=False)
    ttk.Checkbutton(painel, text='Inverter preto/branco', variable=inverter).pack(anchor='w', pady=8)
    escala = tk.StringVar(value='log')
    linha = ttk.Frame(painel)
    linha.pack(fill='x')
    for texto, valor in [('Linear', 'linear'), ('Logarítmica', 'log')]:
        ttk.Radiobutton(linha, text=texto, variable=escala, value=valor,
                        command=lambda: redesenhar()).pack(side='left')
    figura = Figure(figsize=(10, 6), dpi=100)
    canvas = FigureCanvasTkAgg(figura, master=area)
    canvas.get_tk_widget().pack(fill='both', expand=True)
    NavigationToolbar2Tk(canvas, area)
    status = tk.StringVar()

    def redesenhar():
        if estado['resultado'] is not None:
            desenhar(estado['resultado'], escala.get(), figura)
            canvas.draw()
            atualizar_montagem()

    def atualizar_montagem():
        if montagem['janela'] is not None and montagem['janela'].winfo_exists():
            if estado['resultado'] is not None:
                desenhar_montagem(estado['resultado'], escala.get(),
                                  montagem['largura'].get(), montagem['figura'])
                montagem['canvas'].draw()

    def abrir_montagem():
        if not atualizar():
            return
        if montagem['janela'] is not None and montagem['janela'].winfo_exists():
            montagem['janela'].lift()
            return
        tela = tk.Toplevel(janela)
        tela.title('Montagem visual — fonte, abertura e anteparo')
        tela.geometry('1200x700')
        tela.minsize(900, 560)
        barra = ttk.Frame(tela, padding=8)
        barra.pack(fill='x')
        ttk.Label(barra, text='Largura da área visível no anteparo (mm):').pack(side='left')
        largura = tk.DoubleVar(value=80)
        seletor = ttk.Combobox(barra, textvariable=largura, state='readonly',
                               values=(10, 20, 40, 80, 160, 320), width=6)
        seletor.pack(side='left', padx=8)
        fig = Figure(figsize=(12, 6), dpi=100)
        cv = FigureCanvasTkAgg(fig, master=tela)
        cv.get_tk_widget().pack(fill='both', expand=True)
        montagem.update(janela=tela, figura=fig, canvas=cv, largura=largura)
        seletor.bind('<<ComboboxSelected>>', lambda event: atualizar_montagem())

        def salvar_cena():
            destino = filedialog.asksaveasfilename(parent=tela, title='Salvar montagem',
                defaultextension='.png', initialfile='montagem.png', filetypes=[('Imagem PNG', '*.png')])
            if destino:
                try:
                    fig.savefig(destino, dpi=160, facecolor=fig.get_facecolor())
                except OSError as erro:
                    messagebox.showerror('Erro ao salvar', str(erro), parent=tela)

        ttk.Button(barra, text='Salvar imagem…', command=salvar_cena).pack(side='right')
        atualizar_montagem()

    def atualizar():
        try:
            n = int(campos['n'].get())
            limiar = int(campos['limiar'].get())
            if not 32 <= n <= 512 or not 1 <= limiar <= 255:
                raise ValueError('Resolução: 32 a 512. Limiar: 1 a 255.')
            if estado['arquivo']:
                m = carregar_png(estado['arquivo'], n, limiar, inverter.get())
            else:
                m = exemplo(fonte.get(), n)
                if inverter.get():
                    m = 1-m
            numeros = [float(campos[c].get().replace(',', '.')) for c in ('largura', 'onda', 'distancia')]
            r = calcular(m, *numeros)
            r['origem'] = Path(estado['arquivo']).name if estado['arquivo'] else fonte.get()
            r['limiar'] = limiar
            r['invertida'] = inverter.get()
            estado['resultado'] = r
            redesenhar()
            aviso = 'Campo distante adequado (critério aproximado).' if r['fresnel'] < 0.1 else 'Atenção: campo distante pode não valer. Aumente a distância.'
            status.set(f"Altura da imagem: {r['altura_mm']:.4g} mm\nNúmero de Fresnel: {r['fresnel']:.3g}\n{aviso}")
            botao_salvar.state(['!disabled'])
            return True
        except (ValueError, OSError, MemoryError) as erro:
            estado['resultado'] = None
            botao_salvar.state(['disabled'])
            status.set('Corrija os dados e clique em Calcular.')
            messagebox.showerror('Não foi possível calcular', str(erro), parent=janela)
            return False

    def usar_exemplo(event=None):
        estado['arquivo'] = None
        nome.set('Exemplo: '+fonte.get())
        atualizar()

    def exportar():
        # Recalcula para não salvar um gráfico com parâmetros antigos.
        if not atualizar():
            return
        destino = filedialog.asksaveasfilename(title='Salvar gráficos e dados (4 arquivos)',
            defaultextension='.png', initialfile='difracao.png', filetypes=[('Gráfico PNG', '*.png')])
        if destino:
            base = Path(destino).with_suffix('')
            extras = [base.with_suffix(ext) for ext in ('.csv', '.npz', '.json')]
            if any(p.exists() for p in extras) and not messagebox.askyesno('Substituir dados?',
                    'Já existem dados com este nome. Substituir CSV, NPZ e JSON?', parent=janela):
                return
            try:
                salvar(estado['resultado'], figura, destino)
                status.set('Salvos: PNG, CSV, NPZ e JSON.\n'+str(base.parent))
            except OSError as erro:
                messagebox.showerror('Erro ao salvar', str(erro), parent=janela)

    escolha.bind('<<ComboboxSelected>>', usar_exemplo)
    ttk.Button(painel, text='Calcular', command=atualizar).pack(fill='x', pady=(10, 5))
    botao_salvar = ttk.Button(painel, text='Salvar gráficos e dados…', command=exportar)
    botao_salvar.pack(fill='x')
    ttk.Button(painel, text='Ver montagem visual…', command=abrir_montagem).pack(fill='x', pady=(6, 0))
    ttk.Button(painel, text='Abrir sandbox óptico…', command=abrir_sandbox).pack(fill='x', pady=(6, 0))
    ttk.Label(painel, textvariable=status, wraplength=230).pack(anchor='w', pady=12)
    ttk.Label(painel, text='Branco = luz; preto = bloqueio.\nA largura é da imagem inteira.\nAltura automática; pixels quadrados.\nApós editar, clique em Calcular.',
              wraplength=230, foreground='#555555').pack(anchor='w')
    atualizar()
    # Referências simples permitem verificar as ações reais da GUI nos testes.
    return janela, dict(campos=campos, fonte=fonte, escala=escala, inverter=inverter,
                        estado=estado, atualizar=atualizar, usar_exemplo=usar_exemplo,
                        redesenhar=redesenhar, exportar=exportar, carregar=carregar, figura=figura,
                        abrir_montagem=abrir_montagem, montagem=montagem,
                        abrir_sandbox=abrir_sandbox, bancada=bancada)


if __name__ == '__main__':
    janela, _ = criar_app()
    janela.mainloop()
