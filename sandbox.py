"""Editor de bancada óptica com arraste, propriedades e detectores 2D."""
import copy
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sandbox_fisica import cena_inicial, objeto, validar, simular, FORMAS


class Sandbox:
    # A classe reúne o estado de uma janela independente da tela de Fraunhofer.
    def __init__(self, parent=None):
        self.janela = tk.Toplevel(parent) if parent else tk.Tk()
        self.janela.title('Sandbox óptico — arraste e experimente')
        self.janela.geometry('1280x820')
        self.janela.minsize(1100, 740)
        self.cena = cena_inicial()
        self.selecionado = 2
        self.resultado = None
        self.arrastando = False
        self.deslocamento = (0, 0)
        self.status = tk.StringVar()
        self.onda = tk.StringVar(value='633')
        self.resolucao = tk.StringVar(value='256')
        self.detector = tk.StringVar(value='3')
        self.log = tk.BooleanVar(value=True)
        topo = ttk.Frame(self.janela, padding=8)
        topo.pack(fill='x')
        for nome, tipo in [('＋ Fonte', 'fonte'), ('＋ Abertura', 'abertura'), ('＋ Anteparo', 'anteparo')]:
            ttk.Button(topo, text=nome, command=lambda t=tipo: self.adicionar(t)).pack(side='left', padx=3)
        ttk.Button(topo, text='Duplicar', command=self.duplicar).pack(side='left', padx=3)
        ttk.Button(topo, text='Remover', command=self.remover).pack(side='left', padx=3)
        ttk.Button(topo, text='Salvar cena', command=self.salvar_cena).pack(side='right', padx=3)
        ttk.Button(topo, text='Abrir cena', command=self.abrir_cena).pack(side='right', padx=3)
        ttk.Button(topo, text='Exemplo inicial', command=self.reiniciar).pack(side='right', padx=3)
        parametros = ttk.Frame(self.janela, padding=(10, 2))
        parametros.pack(fill='x')
        ttk.Label(parametros, text='Comprimento de onda (nm):').pack(side='left')
        ttk.Entry(parametros, textvariable=self.onda, width=7).pack(side='left', padx=5)
        ttk.Label(parametros, text='Resolução:').pack(side='left')
        ttk.Combobox(parametros, textvariable=self.resolucao, values=(128,256,512),
                     state='readonly', width=5).pack(side='left', padx=5)
        ttk.Button(parametros, text='Simular', command=self.executar).pack(side='left', padx=5)
        ttk.Label(parametros, text='Arraste objetos • horizontal: distância • vertical: altura',
                  foreground='#40566f').pack(side='right')
        corpo = ttk.Frame(self.janela, padding=8)
        corpo.pack(fill='both', expand=True)
        esquerdo = ttk.Frame(corpo)
        esquerdo.pack(side='left', fill='both', expand=True)
        direito = ttk.Frame(corpo, width=420)
        direito.pack(side='right', fill='both', padx=(10,0))
        direito.pack_propagate(False)
        self.canvas = tk.Canvas(esquerdo, bg='#101b2d', highlightthickness=0, height=380)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda event: self.desenhar())
        self.canvas.bind('<ButtonPress-1>', self.pressionar)
        self.canvas.bind('<B1-Motion>', self.mover)
        self.canvas.bind('<ButtonRelease-1>', self.soltar)
        ttk.Label(esquerdo, text='Vista lateral (z, y), fora de escala. Todos os objetos estão centrados em x = 0.\n'
                  'Amarelo: fonte →  •  Azul: abertura  •  Rosa: anteparo de observação',
                  padding=5).pack(anchor='w')
        editor = ttk.LabelFrame(esquerdo, text='Objeto selecionado', padding=8)
        editor.pack(fill='x', pady=5)
        self.titulo = tk.StringVar()
        ttk.Label(editor, textvariable=self.titulo, font=('',10,'bold')).grid(row=0,column=0,columnspan=4,sticky='w')
        self.campos = {}
        self.widgets = {}
        especificacoes = [('z','Posição z (m)'), ('y','Altura y (mm)'), ('tamanho','Tamanho (mm)'),
                         ('altura','Altura da abertura (mm)'), ('separacao','Separação das fendas (mm)'),
                         ('potencia','Potência relativa'), ('angulo','Inclinação da fonte (mrad)')]
        for i, (chave, rotulo) in enumerate(especificacoes):
            row, col = 1+i//2, 2*(i%2)
            ttk.Label(editor, text=rotulo).grid(row=row,column=col,sticky='w',padx=3,pady=4)
            var = tk.StringVar()
            widget = ttk.Entry(editor,textvariable=var,width=9)
            widget.grid(row=row,column=col+1,sticky='ew',padx=3)
            self.campos[chave] = var
            self.widgets[chave] = widget
        self.forma = tk.StringVar()
        ttk.Label(editor,text='Forma da abertura').grid(row=5,column=0,sticky='w')
        self.formas = ttk.Combobox(editor,textvariable=self.forma,values=FORMAS,state='readonly',width=12)
        self.formas.grid(row=5,column=1,sticky='ew')
        ttk.Button(editor,text='Aplicar e simular',command=self.aplicar).grid(row=5,column=2,columnspan=2,sticky='ew',padx=5)
        self.ajuda = tk.StringVar()
        ttk.Label(editor,textvariable=self.ajuda,wraplength=600).grid(row=6,column=0,columnspan=4,sticky='w',pady=6)
        editor.columnconfigure(1,weight=1)
        editor.columnconfigure(3,weight=1)
        linha = ttk.Frame(direito)
        linha.pack(fill='x')
        ttk.Label(linha,text='Ver anteparo:').pack(side='left')
        self.lista_detectores = ttk.Combobox(linha,textvariable=self.detector,state='readonly',width=5)
        self.lista_detectores.pack(side='left',padx=6)
        self.lista_detectores.bind('<<ComboboxSelected>>',lambda event:self.preview())
        ttk.Checkbutton(linha,text='Log',variable=self.log,command=self.preview).pack(side='left')
        ttk.Button(linha,text='Salvar PNG',command=self.salvar_png).pack(side='right')
        self.figura = Figure(figsize=(4,5), dpi=100)
        self.grafico = FigureCanvasTkAgg(self.figura,master=direito)
        self.grafico.get_tk_widget().pack(fill='both',expand=True)
        ttk.Label(direito,text='Fontes gaussianas independentes: intensidades se somam.\n'
                  'Aberturas são placas opacas com furos.\n'
                  'Anteparos são sensores virtuais e não bloqueiam a luz.\n'
                  'Sem reflexões; propagação sempre para a direita.',wraplength=400).pack(pady=5)
        ttk.Label(self.janela,textvariable=self.status,wraplength=1200,padding=8).pack(fill='x')
        self.preencher()
        self.executar()

    def atual(self):
        return next((o for o in self.cena['objetos'] if o['id']==self.selecionado),None)

    def preencher(self):
        o = self.atual()
        self.titulo.set(f"{o['tipo'].capitalize()} {o['id']}" if o else 'Clique em um objeto')
        for k,v in self.campos.items():
            v.set(f"{o[k]:g}" if o else '')
            ativo = o and (k in ('z','y','tamanho') or
                (o['tipo']=='fonte' and k in ('potencia','angulo')) or
                (o['tipo']=='abertura' and k in ('altura','separacao')))
            self.widgets[k].configure(state='normal' if ativo else 'disabled')
        self.forma.set(o['forma'] if o else 'dupla')
        self.formas.configure(state='readonly' if o and o['tipo']=='abertura' else 'disabled')
        explicacao = {'fonte':'Tamanho = raio do feixe (intensidade 1/e²). Arraste para mover a fonte.',
            'abertura':'Tamanho = largura (ou diâmetro do círculo). Dupla: largura de cada fenda; separação entre centros.',
            'anteparo':'Tamanho = lado da área quadrada observada. Arraste para medir em outra posição.'}
        self.ajuda.set(explicacao[o['tipo']] if o else '')

    def geometria(self):
        return max(self.canvas.winfo_width(),100),max(self.canvas.winfo_height(),100)

    def ponto(self,z,y):
        w,h=self.geometria()
        return 45+z/3*(w-75),30+(1.8-y)/3.6*(h-65)

    def coordenadas(self,x,y):
        w,h=self.geometria()
        return float(np.clip((x-45)/(w-75)*3,0,3)),float(np.clip(1.8-(y-30)/(h-65)*3.6,-1.5,1.5))

    def desenhar(self):
        c=self.canvas
        c.delete('all')
        w,h=self.geometria()
        for z in np.arange(0,3.01,0.5):
            x,_=self.ponto(z,0)
            c.create_line(x,25,x,h-30,fill='#26374e')
            c.create_text(x,h-15,text=f'{z:g} m',fill='#b8c7dc')
        for y in (-1.5,-1,0,1,1.5):
            _,py=self.ponto(0,y)
            c.create_line(40,py,w-20,py,fill='#26374e',dash=(3,5))
            c.create_text(22,py,text=f'{y:g}',fill='#b8c7dc')
        c.create_text(45,12,text='y (mm)',fill='#b8c7dc',anchor='w')
        cores={'fonte':'#ffd36b','abertura':'#7fc5ff','anteparo':'#ff91bc'}
        for o in self.cena['objetos']:
            x,y=self.ponto(o['z'],o['y'])
            cor=cores[o['tipo']]
            if o['tipo']=='fonte':
                # Eixo pontilhado ilustrativo, não uma solução de raios.
                fim=self.ponto(3,o['y']+o['angulo']*(3-o['z']))
                c.create_line(x,y,*fim,fill='#6b5e3d',dash=(4,5),arrow='last')
                c.create_oval(x-11,y-11,x+11,y+11,fill=cor,outline=cor)
            else:
                c.create_line(x,y-32,x,y+32,fill=cor,width=6)
                if o['tipo']=='abertura':
                    c.create_line(x,y-7,x,y+7,fill='#101b2d',width=6)
            if o['id']==self.selecionado:
                c.create_rectangle(x-17,y-38,x+17,y+38,outline='white',dash=(3,3))
            c.create_text(x,y-48,text=f"{o['tipo'].capitalize()} {o['id']}",fill=cor)
            if o['tipo']=='abertura':
                c.create_text(x,y+46,text=o['forma'],fill=cor)

    def pressionar(self,event):
        proximos=[]
        for o in self.cena['objetos']:
            x,y=self.ponto(o['z'],o['y'])
            if abs(event.x-x)<22 and abs(event.y-y)<40:
                proximos.append(((event.x-x)**2+(event.y-y)**2,o))
        if proximos:
            o=min(proximos,key=lambda par:par[0])[1]
            self.selecionado=o['id']
            z,y=self.coordenadas(event.x,event.y)
            self.deslocamento=(o['z']-z,o['y']-y)
            self.arrastando=True
            if o['tipo']=='anteparo':
                self.detector.set(str(o['id']))
                self.preview()
            self.preencher()
            self.desenhar()

    def mover(self,event):
        if self.arrastando and self.atual():
            z,y=self.coordenadas(event.x,event.y)
            self.atual().update(z=round(float(np.clip(z+self.deslocamento[0],0,3)),3),
                                y=round(float(np.clip(y+self.deslocamento[1],-1.5,1.5)),3))
            self.preencher()
            self.desenhar()
            self.status.set('Movendo… solte o mouse para recalcular. O gráfico ainda mostra o cálculo anterior.')

    def soltar(self,event):
        if self.arrastando:
            self.arrastando=False
            self.executar()

    def aplicar(self):
        if not self.atual(): return
        try:
            nova=copy.deepcopy(self.cena)
            o=next(o for o in nova['objetos'] if o['id']==self.selecionado)
            for k,v in self.campos.items(): o[k]=float(v.get().replace(',','.'))
            o['forma']=self.forma.get()
            self.cena=validar(nova)
            self.executar()
        except (ValueError,TypeError) as erro:
            messagebox.showerror('Propriedade inválida',str(erro),parent=self.janela)

    def adicionar(self,tipo):
        nova=copy.deepcopy(self.cena)
        ident=max([o['id'] for o in nova['objetos']]+[0])+1
        nova['objetos'].append(objeto(tipo,ident,{'fonte':0.2,'abertura':1.2,'anteparo':2.8}[tipo],0.3))
        self.trocar(nova,ident)

    def duplicar(self):
        if not self.atual(): return
        nova=copy.deepcopy(self.cena)
        o=copy.deepcopy(self.atual())
        o['id']=max(i['id'] for i in nova['objetos'])+1
        o['z']=min(3,o['z']+0.15)
        o['y']=min(1.5,o['y']+0.2)
        nova['objetos'].append(o)
        self.trocar(nova,o['id'])

    def trocar(self,nova,ident=None):
        try:
            self.cena=validar(nova)
        except (ValueError,TypeError) as erro:
            messagebox.showerror('Cena inválida',str(erro),parent=self.janela)
            return
        self.selecionado=ident
        self.onda.set(str(self.cena['onda_nm']))
        self.resolucao.set(str(self.cena['resolucao']))
        self.preencher()
        self.executar()

    def remover(self):
        self.cena['objetos']=[o for o in self.cena['objetos'] if o['id']!=self.selecionado]
        self.selecionado=None
        self.preencher()
        self.executar()

    def reiniciar(self):
        if messagebox.askyesno('Reiniciar cena','Substituir a cena atual pelo exemplo inicial?',parent=self.janela):
            self.trocar(cena_inicial(),2)

    def executar(self):
        try:
            nova=copy.deepcopy(self.cena)
            nova['onda_nm']=float(self.onda.get().replace(',','.'))
            nova['resolucao']=int(self.resolucao.get())
            self.cena=validar(nova)
            self.status.set('Calculando propagação…')
            self.janela.update_idletasks()
            self.resultado=simular(self.cena)
            ids=[str(o['id']) for o in self.cena['objetos'] if o['tipo']=='anteparo']
            self.lista_detectores.configure(values=ids)
            if self.detector.get() not in ids: self.detector.set(ids[0] if ids else '')
            self.desenhar()
            self.preview()
            aviso=' '.join(self.resultado['avisos'])
            self.status.set(aviso or 'Pronto. Arraste um objeto ou edite suas propriedades. Fontes → aberturas → anteparos; a ordem segue a posição z.')
            return True
        except (ValueError,TypeError,MemoryError) as erro:
            self.resultado=None
            self.preview()
            self.status.set('Corrija os valores e clique em Simular.')
            messagebox.showerror('Não foi possível simular',str(erro),parent=self.janela)
            return False

    def preview(self):
        self.figura.clear()
        ax=self.figura.add_subplot(111)
        ident=int(self.detector.get()) if self.detector.get() else None
        o=next((o for o in self.cena['objetos'] if o['id']==ident and o['tipo']=='anteparo'),None)
        if self.resultado is None or o is None or ident not in self.resultado['detectores']:
            ax.text(0.5,0.5,'Adicione um anteparo e simule.',ha='center',va='center',transform=ax.transAxes)
            ax.axis('off')
        else:
            eixo=self.resultado['eixo_mm']
            dados=self.resultado['detectores'][ident]
            pico=dados.max()
            norm=dados/pico if pico>0 else np.zeros_like(dados)
            imagem=np.log10(norm+1e-8) if self.log.get() else norm
            dx=self.resultado['dx_m']*1e3
            img=ax.imshow(imagem,origin='lower',extent=(eixo[0]-dx/2,eixo[-1]+dx/2,eixo[0]-dx/2,eixo[-1]+dx/2),
                          cmap='inferno',vmin=-5 if self.log.get() else 0,vmax=0 if self.log.get() else 1)
            metade=o['tamanho']/2
            ax.set(xlim=(-metade,metade),ylim=(o['y']-metade,o['y']+metade),xlabel='x (mm)',ylabel='y (mm)',
                   title=f"Anteparo {ident} • z = {o['z']:g} m")
            self.figura.colorbar(img,ax=ax,shrink=0.65,label='log10(I/Imax)' if self.log.get() else 'I/Imax')
            area=(abs(eixo[None,:])<=metade)&(abs(eixo[:,None]-o['y'])<=metade)
            potencia=float(dados[area].sum()*self.resultado['dx_m']**2)
            self.figura.text(0.5,0.05,f'Potência captada (relativa): {potencia:.4g}\n'+
                ('Sem luz neste anteparo.' if pico==0 else 'Brilho normalizado pelo pico de todo este plano.'),ha='center',fontsize=9)
        self.figura.tight_layout(rect=(0,0.12,1,0.98))
        self.grafico.draw()

    def salvar_cena(self):
        if not self.executar(): return
        nome=filedialog.asksaveasfilename(parent=self.janela,defaultextension='.json',initialfile='cena_optica.json',filetypes=[('Cena JSON','*.json')])
        if nome:
            try: Path(nome).write_text(json.dumps(self.cena,ensure_ascii=False,indent=2),encoding='utf-8')
            except OSError as erro: messagebox.showerror('Erro ao salvar',str(erro),parent=self.janela)

    def abrir_cena(self):
        nome=filedialog.askopenfilename(parent=self.janela,filetypes=[('Cena JSON','*.json')])
        if nome:
            try:
                nova=json.loads(Path(nome).read_text(encoding='utf-8'))
                self.trocar(nova)
            except (OSError,ValueError,TypeError) as erro:
                messagebox.showerror('Não foi possível abrir',str(erro),parent=self.janela)

    def salvar_png(self):
        if self.resultado is None: return
        nome=filedialog.asksaveasfilename(parent=self.janela,defaultextension='.png',initialfile='anteparo_sandbox.png',filetypes=[('Imagem PNG','*.png')])
        if nome:
            try: self.figura.savefig(nome,dpi=160)
            except OSError as erro: messagebox.showerror('Erro ao salvar',str(erro),parent=self.janela)


if __name__=='__main__':
    Sandbox().janela.mainloop()
