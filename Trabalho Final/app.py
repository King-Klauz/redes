import requests
from time import sleep
from threading import Thread
from tkinter import messagebox, Tk, Toplevel, Frame, Label, Button, StringVar, Entry, Canvas
from tkinter.ttk import Combobox
from plyer import notification
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from datetime import datetime, timedelta
from moedas import MOEDAS

API = 'https://economia.awesomeapi.com.br'

class App:
    def __init__(self) -> None:
        self.raiz = Tk()
        self.raiz.title('Consultor de Cotação')
        self.raiz.resizable(width=False, height=False)

        self.quadro = Frame(self.raiz)
        self.quadro.grid(row=1, column=1, padx=10, pady=10)

        self._ = Label(self.quadro, text='De:', font='arial 12', relief='groove', width=10)
        self._.grid(row=1, column=1, padx=2, pady=2)

        self._ = Label(self.quadro, text='Para:', font='arial 12', relief='groove', width=10)
        self._.grid(row=2, column=1, padx=2, pady=2)

        self.caixa1 = Combobox(self.quadro, values=[moeda for moeda in MOEDAS], width=25, state='readonly')
        self.caixa1.grid(row=1, column=2, padx=2, pady=2)

        self.caixa2 = Combobox(self.quadro, values=[moeda for moeda in MOEDAS], width=25, state='readonly')
        self.caixa2.grid(row=2, column=2, padx=2, pady=2)

        self._ = Button(self.quadro, font='arial 12', text='Consultar', command=self.consultar, width=10)
        self._.grid(row=3, column=1, columnspan=2, padx=2, pady=2)

        self.dados = {
            'Alta': StringVar(self.raiz),
            'Baixa': StringVar(self.raiz),
            'Variação': StringVar(self.raiz),
            'Data': StringVar(self.raiz)
        }

        for (linha, dado) in enumerate(self.dados, 4):
            self._ = Label(self.quadro, text=f'{dado}:', font='arial 12', relief='groove', width=10)
            self._.grid(row=linha, column=1, padx=2, pady=2)
            self._ = Label(self.quadro, textvariable=self.dados[dado], font='arial 12', relief='groove', width=19)
            self._.grid(row=linha, column=2, padx=2, pady=2)

        self.botao_monitorar = Button(self.quadro, font='arial 12', text='Monitorar', command=self.monitorar, width=10)
        self.botao_monitorar.grid(row=8, column=1, padx=2, pady=2)
        self.botao_monitorar.config(state='disabled')

        self.botao_historico = Button(self.quadro, font='arial 12', text='Gerar Histórico', command=self.gerar_historico, width=18)
        self.botao_historico.grid(row=8, column=2, padx=2, pady=2)
        self.botao_historico.config(state='disabled')

        self.pausado = True
        self.monitor = Thread(target=self.notificar)
        self.monitor.daemon = True
        self.monitor.start()

        # Inicializa as referências do gráfico como None
        self.fig_canvas = None
        self.toolbar = None

        self.raiz.mainloop()

    def consultar(self, flag=True) -> None:
        try:
            self.pausado = flag
            self.moeda1 = MOEDAS[self.caixa1.get()]
            self.moeda2 = MOEDAS[self.caixa2.get()]
        except:
            messagebox.showerror('Erro!', 'Selecione as moedas.')
        else:
            try:
                self.url = f'{API}/last/{self.moeda1}-{self.moeda2}'
                self.cotacao = requests.get(self.url).json()[f'{self.moeda1}{self.moeda2}']
            except:
                self.botao_monitorar.config(state='disabled')
                self.botao_historico.config(state='disabled')
                for dado in self.dados:
                    self.dados[dado].set('')
                messagebox.showerror('Erro!', 'Cotação ainda não disponível na API.')
            else:
                self.dados['Alta'].set(self.cotacao['high'])
                self.dados['Baixa'].set(self.cotacao['low'])
                self.dados['Variação'].set(self.cotacao['varBid'])
                self.dados['Data'].set(self.cotacao['create_date'])
                self.botao_monitorar.config(state='normal')
                self.botao_historico.config(state='normal')

    def monitorar(self) -> None:
        self.janela = Toplevel(self.raiz)
        self.janela.title('Monitor')
        self.janela.resizable(width=False, height=False)
        self._ = Label(self.janela, text='Limiar:', font='arial 12', relief='groove', width=10)
        self._.grid(row=1, column=1, padx=2, pady=2)
        self.entrada = Entry(self.janela, font='arial 12', width=15)
        self.entrada.grid(row=1, column=2, padx=2, pady=2)
        self._ = Button(self.janela, text='Definir', font='arial 12', command=self.definir, width=15)
        self._.grid(row=2, column=1, columnspan=2, padx=2, pady=2)

    def definir(self) -> None:
        try:
            self.limiar = float(self.entrada.get())
            if self.limiar <= 0:
                raise ValueError()
        except:
            messagebox.showerror('Erro', 'Valor Inválido.')
            self.janela.destroy()
        else:
            self.pausado = False
            self.janela.destroy()

    def notificar(self) -> None:
        while True:
            sleep(10)
            if not self.pausado:
                self.consultar(flag=False)
                valor = float(self.cotacao['high'])
                if self.limiar > 0 and valor > self.limiar:
                    notification.notify(
                        message='A cotação cruzou o limiar definido.',
                        title='Monitor',
                        timeout=3
                    )

    def gerar_historico(self) -> None:
        self.janela_historico = Toplevel(self.raiz)
        self.janela_historico.title('Gerar Histórico')
        self.janela_historico.resizable(width=False, height=False)

        self.frame_opcoes = Frame(self.janela_historico)
        self.frame_opcoes.grid(row=1, column=1, padx=10, pady=10)

        self._ = Button(self.frame_opcoes, text='15 Dias', font='arial 12', command=lambda: self.gerar_grafico(15), width=15)
        self._.grid(row=1, column=1, padx=2, pady=2)
        self._ = Button(self.frame_opcoes, text='1 Mês', font='arial 12', command=lambda: self.gerar_grafico(30), width=15)
        self._.grid(row=1, column=2, padx=2, pady=2)
        self._ = Button(self.frame_opcoes, text='3 Meses', font='arial 12', command=lambda: self.gerar_grafico(90), width=15)
        self._.grid(row=1, column=3, padx=2, pady=2)
        self._ = Button(self.frame_opcoes, text='6 Meses', font='arial 12', command=lambda: self.gerar_grafico(180), width=15)
        self._.grid(row=1, column=4, padx=2, pady=2)
        self._ = Button(self.frame_opcoes, text='12 Meses', font='arial 12', command=lambda: self.gerar_grafico(365), width=15)
        self._.grid(row=1, column=5, padx=2, pady=2)

        self.canvas_grafico = Canvas(self.janela_historico, width=800, height=400)
        self.canvas_grafico.grid(row=2, column=1, padx=10, pady=10)

    def gerar_grafico(self, dias: int) -> None:
        data_final = datetime.today()
        data_inicial = data_final - timedelta(days=dias)

        data_inicial_str = data_inicial.strftime('%Y-%m-%d')
        data_final_str = data_final.strftime('%Y-%m-%d')

        url_historico = f'{API}/json/daily/{self.moeda1}-{self.moeda2}/1000'
        response = requests.get(url_historico)

        if response.status_code != 200:
            messagebox.showerror('Erro', 'Não foi possível obter os dados históricos.')
            return

        historico = response.json()
        datas = []
        valores = []

        for dia in historico:
            data = datetime.fromtimestamp(int(dia['timestamp']))
            if data_inicial <= data <= data_final:
                datas.append(data)
                valores.append(float(dia['high']))

        if not datas:
            messagebox.showinfo('Informação', 'Nenhum dado encontrado para o período especificado.')
            return

        # Deleta o gráfico e a barra de ferramentas anteriores, se existirem
        if self.fig_canvas:
            self.fig_canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(datas, valores, marker='o')
        ax.set_xlabel('Data')
        ax.set_ylabel('Valor da Cotação')
        ax.set_title(f'Histórico de Cotações de {self.moeda1} para {self.moeda2}')
        ax.grid(True)

        self.fig_canvas = FigureCanvasTkAgg(fig, master=self.canvas_grafico)
        self.fig_canvas.draw()
        self.fig_canvas.get_tk_widget().pack()

        self.toolbar = NavigationToolbar2Tk(self.fig_canvas, self.canvas_grafico)
        self.toolbar.update()
        self.fig_canvas.get_tk_widget().pack()

if __name__ == '__main__':
    App()
