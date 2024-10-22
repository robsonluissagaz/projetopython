from tkinter import *
from tkinter import ttk
import sqlite3
import os
from tkinter import messagebox

#criando o arquivo do banco de dados
pasta_banco = os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI")
if not os.path.exists(pasta_banco):
    os.makedirs(pasta_banco)
caminho_do_banco = os.path.join(pasta_banco, "estoque.db")
conn = sqlite3.connect(caminho_do_banco)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS equipamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL,
    setor TEXT NOT NULL,
    usuario TEXT NOT NULL,
    componentes TEXT,
    observacao TEXT
)
''')
conn.commit()
conn.close()

#configuração da tela principal
root = Tk()
largura_tela = root.winfo_screenwidth()
altura_tela = root.winfo_screenheight()
tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')


class Application():
    #tela do menú inicial
    def __init__(self):
        self.root = root
        self.tela()
        self.frame_de_tela()
        self.widgets_frame1()
        self.lista_frame2()
        root.mainloop()


    def tela_cadastro(self):
        #criação da janela cadastro
        self.janela_cadastro = Toplevel(self.root)
        self.framecadastro = Frame(self.janela_cadastro, bd=4, bg='white', 
                             highlightbackground='#107db2',
                             highlightthickness=2)
        self.framecadastro.place(relx= 0.001, rely= 0.001, relwidth= 1, relheight= 1)
        self.janela_cadastro.title("CADASTRO DE EQUIPAMENTOS")
        self.janela_cadastro.configure(background='white')
        self.janela_cadastro.geometry('400x400')
        self.janela_cadastro.resizable(False, False)
        #tornando outras janelas não interativas
        self.janela_cadastro.grab_set()
        #criação do conteudo da janela:
        #criando o campo nome
        self.lb_nome = Label(self.janela_cadastro, text='NOME',fg='black',font=("Arial", 10))#,borderwidth=5,bg='#458B74')
        self.lb_nome.place(relx=0.01, rely=0.01)
        self.nome_entry = Entry(self.janela_cadastro)
        self.nome_entry.place(relx=0.30, rely=0.01, width=250)
        #criando o campo setor
        self.lb_setor = Label(self.janela_cadastro, text='SETOR',fg='black',font=("Arial", 10))
        self.lb_setor.place(relx=0.01, rely=0.1)
        self.setor_entry = Entry(self.janela_cadastro)
        self.setor_entry.place(relx=0.30, rely=0.1, width=250)
        #criando o campo usuário:
        self.lb_usuario = Label(self.janela_cadastro, text='USUÁRIO',fg='black',font=("Arial", 10))
        self.lb_usuario.place(relx=0.01, rely=0.2)
        self.usuario_entry = Entry(self.janela_cadastro)
        self.usuario_entry.place(relx=0.30, rely=0.2, width=250)
        #criando o campo componentes
        self.lb_componente = Label(self.janela_cadastro, text='COMPONENTES',fg='black',font=("Arial", 10))
        self.lb_componente.place(relx=0.01, rely=0.3)
        self.componente_entry = Entry(self.janela_cadastro)
        self.componente_entry.place(relx=0.30, rely=0.3, width=250)
        #criando o campo categoria
        self.lb_categoria = Label(self.janela_cadastro, text='CATEGORIA',fg='black',font=("Arial", 10))
        self.lb_categoria.place(relx=0.01, rely=0.4)
        self.categoria_entry = Entry(self.janela_cadastro)
        self.categoria_entry.place(relx=0.30, rely=0.4, width=250)
        #criando o campo observações
        self.lb_obs = Label(self.janela_cadastro, text='OBSERVAÇÃO',fg='black',font=("Arial", 10))
        self.lb_obs.place(relx=0.01, rely=0.5)
        self.obs_entry = Entry(self.janela_cadastro)
        self.obs_entry.place(relx=0.30, rely=0.5, width=250)
        #criando o botão de cadastrar
        self.bt_cadastrar = Button(self.janela_cadastro, text='CADASTRAR', command=self.cadastrar, borderwidth=5, bg='#107db2', fg='white',font=("Arial", 10))
        self.bt_cadastrar.place(relx= 0.7, rely= 0.9)
        #Botão para fechar a janela:
        self.bt_fechar = Button(self.janela_cadastro, text='CANCELAR',borderwidth=5,bg='#107db2',fg='white',font=("Arial", 10), command=self.janela_cadastro.destroy)
        self.bt_fechar.place(relx= 0.1, rely= 0.9)


    #características da tela menú inicial
    def tela(self):
        self.root.title("Sagaz TEC")
        self.root.configure(background='#107db2')
        self.root.geometry(tamanho_tela_str)
        self.root.resizable(True, True)
        root.state('zoomed')
        self.root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
        self.root.minsize(width=largura_tela, height=altura_tela)


    def salvar_alteracoes(self, equipamento_id):
        nome = self.nome_editar_entry.get().upper()
        setor = self.setor_editar_entry.get().upper()
        usuario = self.usuario_editar_entry.get().upper()
        componentes = self.componentes_editar_entry.get().upper()
        categoria = self.categoria_editar_entry.get().upper()
        observacao = self.observacao_editar_entry.get().upper()
        # Atualizar no banco de dados
        try:
            conn = sqlite3.connect(caminho_do_banco)
            cursor = conn.cursor()
            cursor.execute('''UPDATE equipamentos 
                            SET nome=?, setor=?, usuario=?, componentes=?, categoria=?, observacao=?
                            WHERE id=?''', (nome,setor, usuario, 
                                            componentes, categoria, 
                                            observacao, equipamento_id))
            conn.commit()
            messagebox.showinfo("Sucesso", "Alterações salvas com sucesso!")
        except sqlite3.Error as erro:
            messagebox.showerror("Erro", f"Erro ao salvar alterações: {erro}")
        finally:
            conn.close()


    def carregar_dados(self):
        # Limpa os dados existentes na lista
        for item in self.listaequip.get_children():
            self.listaequip.delete(item)
        # Conectando ao banco de dados e buscando os dados
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, categoria, setor FROM equipamentos")
        registros = cursor.fetchall()
        # Inserindo os dados na Treeview
        for registro in registros:
            self.listaequip.insert("", "end", values=registro)
        conn.close()

    #função para alterar na tela de cadastrar
    def alterar(self):
        #Função que abre uma janela para listar e alterar os equipamentos cadastrados.
        # Criação da nova janela
        self.janela_alterar = Toplevel(self.root)
        self.janela_alterar.title("ALTERAR EQUIPAMENTO")
        self.janela_alterar.configure(background='white')
        self.janela_alterar.geometry('500x400')
        self.janela_alterar.resizable(False, False)
        # Tornar outras janelas não interativas
        self.janela_alterar.grab_set()
        # Criar uma Treeview para exibir os equipamentos
        self.lista_alterar = ttk.Treeview(self.janela_alterar, height=10, columns=('col0','col1', 'col2', 'col3', 'col4'))
        self.lista_alterar.heading('#0', text='')
        self.lista_alterar.heading('#1', text='ID')
        self.lista_alterar.heading('#2', text='Nome')
        self.lista_alterar.heading('#3', text='Categoria')
        self.lista_alterar.heading('#4', text='Setor')
        # Posicionar as colunas
        self.lista_alterar.column('#0', width=1)
        self.lista_alterar.column('#1', width=50)
        self.lista_alterar.column('#2', width=200)
        self.lista_alterar.column('#3', width=150)
        self.lista_alterar.column('#4', width=100)
        self.lista_alterar.pack(pady=20)
        # Adicionar barra de rolagem
        scroll_alterar = Scrollbar(self.janela_alterar, orient='vertical')
        self.lista_alterar.configure(yscroll=scroll_alterar.set)
        scroll_alterar.pack(side=RIGHT, fill=Y)
        # Carregar dados na Treeview
        self.carregar_dados_alteracao()
        # Botão para abrir a janela de edição
        bt_editar = Button(self.janela_alterar, text="EDITAR SELECIONADO", bg='#107db2', fg='white', command=self.editar_equipamento)
        bt_editar.pack(pady=10)


    def carregar_dados_alteracao(self):
        """Carrega os dados dos equipamentos para a janela de alteração."""
        # Limpar o Treeview
        for item in self.lista_alterar.get_children():
            self.lista_alterar.delete(item)
        # Conectar ao banco de dados e buscar os dados
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, setor,usuario, componentes, categoria, observacao  FROM equipamentos")
        registros = cursor.fetchall()
        # Inserir os dados na Treeview
        for registro in registros:
            self.lista_alterar.insert("", "end", values=registro)
        conn.close()


    def editar_equipamento(self):
        """Função que abre uma janela de edição para o equipamento selecionado."""
        # Verificar se algum item foi selecionado
        selecionado = self.lista_alterar.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um equipamento para editar!")
            return
        # Obter os valores do item selecionado
        item = self.lista_alterar.item(selecionado)
        equipamento_id = item['values'][0]
        nome = item['values'][1]
        setor = item['values'][2]
        usuario = item['values'][3]
        componentes = item['values'][4]
        categoria = item['values'][5]
        observacao = item['values'][6]
        # Criar a janela de edição
        self.janela_editar = Toplevel(self.janela_alterar)
        self.janela_editar.title("EDITAR EQUIPAMENTO")
        self.janela_editar.configure(background='white')
        self.janela_editar.geometry('400x400')
        self.janela_editar.resizable(False, False)
        self.janela_editar.grab_set()
        # Criar campos para edição (usando valores atuais)
        #nome
        Label(self.janela_editar, text='Nome', bg='#458B74', fg='white').place(relx=0.1, rely=0.1)
        self.nome_editar_entry = Entry(self.janela_editar)
        self.nome_editar_entry.place(relx=0.4, rely=0.1)
        self.nome_editar_entry.insert(0, nome)
        #setor
        Label(self.janela_editar, text='Setor', bg='#458B74', fg='white').place(relx=0.1, rely=0.2)
        self.setor_editar_entry = Entry(self.janela_editar)
        self.setor_editar_entry.place(relx=0.4, rely=0.2)
        self.setor_editar_entry.insert(0, setor)
        #Usuário
        Label(self.janela_editar, text='Usuário', bg='#458B74', fg='white').place(relx=0.1, rely=0.3)
        self.usuario_editar_entry = Entry(self.janela_editar)
        self.usuario_editar_entry.place(relx=0.4, rely=0.3)
        self.usuario_editar_entry.insert(0, usuario)
        #Componentes
        Label(self.janela_editar, text='Componentes', bg='#458B74', fg='white').place(relx=0.1, rely=0.4)
        self.componentes_editar_entry = Entry(self.janela_editar)
        self.componentes_editar_entry.place(relx=0.4, rely=0.4)
        self.componentes_editar_entry.insert(0, componentes)
        #Categoria
        Label(self.janela_editar, text='Categoria', bg='#458B74', fg='white').place(relx=0.1, rely=0.5)
        self.categoria_editar_entry = Entry(self.janela_editar)
        self.categoria_editar_entry.place(relx=0.4, rely=0.5)
        self.categoria_editar_entry.insert(0, categoria)
        #Observação
        Label(self.janela_editar, text='Observação', bg='#458B74', fg='white').place(relx=0.1, rely=0.6)
        self.observacao_editar_entry = Entry(self.janela_editar)
        self.observacao_editar_entry.place(relx=0.4, rely=0.6)
        self.observacao_editar_entry.insert(0, observacao)
        # Botão para salvar as alterações
        bt_salvar = Button(self.janela_editar, text="SALVAR ALTERAÇÕES", bg='#107db2', fg='white', 
                        command=lambda: self.salvar_alteracoes(equipamento_id))
        bt_salvar.place(relx=0.7, rely=0.9)


    #função para cadastrar na tela de cadastrar
    def cadastrar(self):
        # Captura as informações dos campos
        nome = self.nome_entry.get().upper()
        categoria = self.categoria_entry.get().upper()
        setor = self.setor_entry.get().upper()
        usuario = self.usuario_entry.get().upper()
        componentes = self.componente_entry.get().upper()
        observacao = self.obs_entry.get().upper()
        if not nome or not categoria or not setor or not usuario:
            messagebox.showwarning("Atenção", "Por favor, preencha todos os campos obrigatórios!")
            return
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM equipamentos WHERE nome = ?", (nome,))
        existe = cursor.fetchone()[0]
        if existe > 0:
            messagebox.showwarning("Atenção", "Este equipamento já está cadastrado!")
            conn.close()
            return
        cursor.execute('''
        INSERT INTO equipamentos (nome, categoria, setor, usuario, componentes, observacao)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, categoria, setor, usuario, componentes, observacao))
        conn.commit()
        conn.close()
        self.limpar_campos()
        messagebox.showinfo("Sucesso", "Equipamento cadastrado com sucesso!")
        self.carregar_dados()


    #definindo a função para limpar os campos da janela cadastrar
    def limpar_campos(self):
        self.nome_entry.delete(0, END)
        self.categoria_entry.delete(0, END)
        self.setor_entry.delete(0, END)
        self.usuario_entry.delete(0, END)
        self.componente_entry.delete(0, END)
        self.obs_entry.delete(0, END)


    #criando a função para visualização dos dados no frame2
    def frame_de_tela(self):
        #Abaixo a criação do primeiro frame:
        self.frame1 = Frame(self.root, bd=4, bg='white', 
                             highlightbackground='#98F5FF',
                             highlightthickness=2)
        self.frame1.place(relx= 0.02, rely= 0.02, relwidth= 0.96, relheight=0.46)
        #Abaixo a criação do segundo frame:
        self.frame2 = Frame(self.root, bd=4, bg='white', 
                             highlightbackground='#98F5FF',
                             highlightthickness=2)
        self.frame2.place(relx= 0.02, rely= 0.5, relwidth= 0.96, relheight=0.46)


    def widgets_frame1(self):
        #criando o botão cadastrar:
        self.bt_cadastrar = Button(self.frame1, text='CADASTRAR EQUIPAMENTO',bg='#107db2',fg='white',font=("Arial", 10), command=self.tela_cadastro,borderwidth=5)
        self.bt_cadastrar.place(relx=0.01, rely=0.01, relwidth=0.15, relheight=0.10)
        #criando o botão alterar:
        self.bt_alterar = Button(self.frame1, text='ALTERAR EQUIPAMENTO',borderwidth=5,bg='#107db2',fg='white',font=("Arial", 10),command=self.alterar)
        self.bt_alterar.place(relx=0.01, rely=0.15, relwidth=0.15, relheight=0.10)
        #criando o botão excluir:
        self.bt_excluir = Button(self.frame1, text='EXCLUIR EQUIPAMENTO',borderwidth=5,bg='#107db2',fg='white',font=("Arial", 10))
        self.bt_excluir.place(relx=0.01, rely=0.30, relwidth=0.15, relheight=0.10)
        #criando o botão de vincular nota fiscal:
        self.bt_fiscal = Button(self.frame1, text='VINCULAR NOTA FISCAL',borderwidth=5,bg='#107db2',fg='white',font=("Arial", 10))
        self.bt_fiscal.place(relx=0.01, rely=0.45, relwidth=0.15, relheight=0.10)
        #criando o botão para fechar o programa:
        self.bt_fechar = Button(self.frame1, text='FECHAR PROGRAMA',borderwidth=5,bg='#107db2',fg='white',font=("Arial", 10), command=self.root.destroy)
        self.bt_fechar.place(relx=0.01, rely=0.90, relwidth=0.15, relheight=0.10)


    def lista_frame2(self):
        #criando as colunas da lista do frame2
        self.listaequip = ttk.Treeview(self.frame2, height=3, columns=('col1', 'col2', 'col3', 'col4'))
        self.carregar_dados()
        self.listaequip.heading('#0', text='')
        self.listaequip.heading('#1', text='ID')
        self.listaequip.heading('#2', text='Nome')
        self.listaequip.heading('#3', text='Categoria')
        self.listaequip.heading('#4', text='Setor')
        #posicionando e dimensionando as colunas
        self.listaequip.column('#0', width=1)
        self.listaequip.column('#1', width=50)
        self.listaequip.column('#2', width=200)
        self.listaequip.column('#3', width=200)
        self.listaequip.column('#4', width=200)
        self.listaequip.place(relx=0.01, rely=0.1, relwidth=0.95, relheight=0.85)
        #criando a barra de rolagem
        self.scroll_lista = Scrollbar(self.frame2, orient='vertical')
        self.listaequip.configure(yscroll=self.scroll_lista.set)
        self.scroll_lista.place(relx=0.96, rely=0.1, relwidth=0.02, relheight=0.85)


Application()