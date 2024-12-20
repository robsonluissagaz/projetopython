from imapclient import IMAPClient
import pyzmail
from tkinter import *
import tkinter as tk
from tkinter import ttk
import sqlite3
import os
from tkinter import filedialog, messagebox
import shutil
from PIL import Image, ImageTk
import win32evtlog
import threading
import json

pasta_banco = os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI")
caminho_do_banco = os.path.join(pasta_banco, "estoque.db")
caminho_notas_fiscais = os.path.join(pasta_banco, "notas_fiscais.db")
if not os.path.exists(pasta_banco):
    os.makedirs(pasta_banco)
root = Tk()
with open('credenciais.json', 'r') as file:
    credenciais = json.load(file)
EMAIL = credenciais.get('email')
PASSWORD = credenciais.get('senha')
SERVER = "imap.gmail.com"


#criando o arquivo do banco de dados
def banco_equipamentos():
    conn = sqlite3.connect(caminho_do_banco)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS equipamentos (id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                categoria TEXT DEFAULT 'NENHUM REGISTRO',
                setor TEXT  DEFAULT 'NENHUM INSERIDO',
                usuario TEXT DEFAULT 'NENHUM REGISTRADO',
                componentes TEXT DEFAULT 'NENHUM COMPONENTE',
                key TEXT DEFAULT 'KEY NAO INSERIDA', 
                observacao TEXT DEFAULT 'NENHUMA OBSERVAÇÃO')''')
    conn.commit()
    conn.close()


#Criando o banco de dados para as notas fiscais
def banco_notas():
    #Criando o banco de dados para as notas fiscais
    conn = sqlite3.connect(caminho_notas_fiscais)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS notas(id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipamento_id INTEGER NOT NULL,
                caminho TEXT NOT NULL,
                FOREIGN KEY (equipamento_id) REFERENCES equipamentos (id))''')
    conn.commit()
    conn.close()


class Application():
    def __init__(self):
        self.root = root
        self.imagem = Image.open("sagaztec.png")
        self.imagem_tk = ImageTk.PhotoImage(self.imagem)
        self.conexao_imap = None
        self.mensagens_dict = {}
        self.tela()
        self.frame_de_tela()
        self.widgets_frame1()
        self.lista_frame2()
        self.conectar_imap()
        root.mainloop()


    def conectar_imap(self):
        try:
            self.conexao_imap = IMAPClient(SERVER, ssl=True)
            self.conexao_imap.login(EMAIL, PASSWORD)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao conectar ao servidor IMAP.\n{str(e)}")


    def reconectar_imap(self):
            if not self.conexao_imap or not self.conexao_imap.has_capability("IMAP4rev1"):
                self.conectar_imap()


    def desconectar_imap(self):
        if self.conexao_imap:
            self.conexao_imap.logout()


    def marcar_como_lixo(self):
        try:
            item_selecionado = self.tree.focus()
            if not item_selecionado:
                messagebox.showwarning("Atenção", "Selecione um e-mail para marcar como Lixo.")
                return
            uid = int(item_selecionado)
            self.conexao_imap.select_folder("Resolvidos")
            self.conexao_.move([uid], "Lixeira")
            self.tree.delete(item_selecionado)
            del self.mensagens_dict[str(uid)]
            self.texto_conteudo.configure(state=tk.NORMAL)
            self.texto_conteudo.delete("1.0", tk.END)
            self.texto_conteudo.configure(state=tk.DISABLED)
            messagebox.showinfo("Sucesso", "O e-mail foi movido para 'Lixeira'.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível mover o e-mail para 'Lixeira'.\n{str(e)}")


    def exibir_conteudo(self, event):
        try:
            selecionado = self.tree.selection()
            if selecionado:
                uid = selecionado[0]
                if uid in self.mensagens_dict:
                    conteudo_email = self.mensagens_dict[uid]["conteudo"]
                    self.texto_conteudo.config(state=tk.NORMAL)
                    self.texto_conteudo.delete(1.0, tk.END)
                    self.texto_conteudo.insert(tk.END, conteudo_email)
                    self.texto_conteudo.config(state=tk.DISABLED)
                else:
                    messagebox.showerror("Erro", "Conteúdo do e-mail não encontrado.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir o conteúdo do e-mail:\n{e}")


    def carregar_chamados(self):
        try:
            self.conexao_imap.select_folder("Chamados", readonly=True)
            mensagens = self.conexao_imap.search(["ALL"])
            for item in self.tree.get_children():
                self.tree.delete(item)
            for uid in mensagens:
                mensagem_raw = self.conexao_imap.fetch([uid], ["BODY[]", "FLAGS"])
                mensagem = pyzmail.PyzMessage.factory(mensagem_raw[uid][b"BODY[]"])
                remetente = mensagem.get_address("from")[1]
                assunto = mensagem.get_subject() or "Sem Assunto"
                data = mensagem.get_decoded_header("date")
                conteudo = mensagem.text_part.get_payload().decode(mensagem.text_part.charset) if mensagem.text_part else "Sem conteúdo disponível"
                self.mensagens_dict[f"{uid}"] = {
                    "remetente": remetente,
                    "assunto": assunto,
                    "conteudo": conteudo,
                    "data": data,}
                self.tree.insert("", "end", iid=uid, values=(remetente, assunto, data))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar os chamados.\n{str(e)}")


    def marcar_como_resolvido(self):
        try:
            item_selecionado = self.tree.focus()
            if not item_selecionado:
                messagebox.showwarning("Atenção", "Selecione um e-mail para marcar como resolvido.")
                return
            uid = int(item_selecionado)
            self.reconectar_imap()
            self.conexao_imap.select_folder("Chamados")
            self.conexao_imap.move([uid], "Resolvidos")
            self.tree.delete(item_selecionado)
            del self.mensagens_dict[str(uid)]
            self.texto_conteudo.configure(state=tk.NORMAL)
            self.texto_conteudo.delete("1.0", tk.END)
            self.texto_conteudo.configure(state=tk.DISABLED)
            messagebox.showinfo("Sucesso", "O e-mail foi movido para 'Resolvidos'.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível mover o e-mail para 'Resolvidos'.\n{str(e)}")


    def carregar_chamados_resolvidos(self):
        try:
            self.conexao_imap.select_folder("Resolvidos", readonly=True)
            mensagens = self.conexao_imap.search(["ALL"])
            for item in self.tree.get_children():
                self.tree.delete(item)
            for uid in mensagens:
                mensagem_raw = self.conexao_imap.fetch([uid], ["BODY[]", "FLAGS"])
                mensagem = pyzmail.PyzMessage.factory(mensagem_raw[uid][b"BODY[]"])
                remetente = mensagem.get_address("from")[1]
                assunto = mensagem.get_subject() or "Sem Assunto"
                data = mensagem.get_decoded_header("date")
                conteudo = "Sem conteúdo disponível"
                if mensagem.text_part:
                    try:
                        conteudo = mensagem.text_part.get_payload().decode(mensagem.text_part.charset)
                    except Exception:
                        conteudo = "Erro ao decodificar o conteúdo."
                self.mensagens_dict[f"{uid}"] = {
                    "remetente": remetente,
                    "assunto": assunto,
                    "conteudo": conteudo,
                    "data": data,}
                self.tree.insert("", "end", iid=uid, values=(remetente, assunto, data))
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar os chamados.\n{str(e)}")


    def carregar_chamados_em_thread(self):
        threading.Thread(target=self.carregar_chamados, daemon=True).start()


    def carregar_resolvidos_em_thread(self):
        threading.Thread(target=self.carregar_chamados_resolvidos, daemon=True).start()


    def carregar_logs_eventos(self):
        item_selecionado = self.lista_excluir_nota.selection()
        item_valores = self.lista_excluir_nota.item(item_selecionado[0], "values")
        server = item_valores[3]
        log_type = 'Segurança'#,'Application', 'Security'
        log_handle = win32evtlog.OpenEventLog(server, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        event_type_map = {1: "Erro", 2: "Aviso", 4: "Nível"}
        events = win32evtlog.ReadEventLog(log_handle, flags, 0)
        for event in events:
            event_id = event.EventID & 0xFFFF  # Máscara para obter o ID correto
            event_type = event.EventType
            event_type_str = event_type_map.get(event_type, "Desconhecido")
            description = str(event.StringInserts) if event.StringInserts else "Sem descrição"
            self.tree.insert("", "end", values=(event_id, event_type_str, description))
        win32evtlog.CloseEventLog(log_handle)


    def ver_eventos(self):
        selected_item = self.lista_excluir_nota.selection()
        if not selected_item:
            messagebox.showwarning("Atenção", "Selecione um usuário.")
            return
        item_values = self.lista_excluir_nota.item(selected_item[0], "values")
        nome_usuario = item_values[3]
        caminho_log = os.path.join(f"\\\\{nome_usuario}", "C$", "Windows", "System32", "winevt", "Logs")
        try:
            if os.path.exists(caminho_log):
                os.startfile(caminho_log)
            else:
                messagebox.showerror("Erro", f"O caminho do log não foi encontrado para o usuário {nome_usuario}.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível acessar os eventos do usuário {nome_usuario}.\nErro: {e}")


    def cancelar(self, janela_atual, janela_destino):
        janela_atual.destroy()
        janela_destino.lift()
        janela_destino.grab_set()


    def abrir_nota(self):
        nota_selecionada = self.lista_cad_nota.selection()
        if not nota_selecionada:
            messagebox.showwarning("Atenção", "Selecione uma nota para visualizar.")
            return
        nota_id = self.lista_cad_nota.item(nota_selecionada, "values")[0]
        conn = sqlite3.connect(caminho_notas_fiscais)
        cursor = conn.cursor()
        cursor.execute("SELECT caminho FROM notas WHERE id = ?", (nota_id,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado:
            caminho_nota = resultado[0]
            if os.path.exists(caminho_nota):
                os.startfile(caminho_nota)
            else:
                messagebox.showerror("Erro", "Arquivo não encontrado. Verifique se o caminho está correto.")
        else:
            messagebox.showerror("Erro", "Caminho da nota fiscal não encontrado no banco de dados.")


    def excluir_nota(self):
        nota_selecionada = self.lista_cad_nota.selection()
        if not nota_selecionada:
            messagebox.showwarning("Atenção", "Selecione uma nota para visualizar.")
            return
        nota_id = self.lista_cad_nota.item(nota_selecionada, "values")[0]
        conn = sqlite3.connect(caminho_notas_fiscais)
        cursor = conn.cursor()
        cursor.execute("SELECT caminho FROM notas WHERE id = ?", (nota_id,))
        resultado = cursor.fetchone()
        caminho_nota = resultado[0] if resultado else None
        resposta = messagebox.askyesno("Confirmação", "Tem certeza de que deseja excluir esta nota?")
        if not resposta:
            conn.close()
            return
        cursor.execute("DELETE FROM notas WHERE id = ?", (nota_id,))
        conn.commit()
        conn.close()
        if caminho_nota and os.path.exists(caminho_nota):
            try:
                os.remove(caminho_nota)
            except Exception as e:
                messagebox.showwarning("Aviso", f"Não foi possível excluir o arquivo físico: {e}")
        self.lista_cad_nota.delete(nota_selecionada)
        messagebox.showinfo("Sucesso", "Nota fiscal excluída com sucesso.")


    def carregar_dados_tela_remover_nota_2(self):
        selected_item = self.lista_excluir_nota.selection()
        if not selected_item:
            messagebox.showwarning("Atenção", "Selecione um equipamento para visualizar suas notas fiscais.")
            return
        equipamento_id = self.lista_excluir_nota.item(selected_item, "values")[0]
        conn = sqlite3.connect(caminho_notas_fiscais)
        cursor = conn.cursor()
        cursor.execute("SELECT id, caminho FROM notas WHERE equipamento_id = ?", (equipamento_id,))
        notas = cursor.fetchall()
        conn.close()
        if not notas:
            messagebox.showinfo("Informação", "Não há notas fiscais vinculadas a este equipamento.")
            self.janela_fiscal_remover_2.destroy()
            self.janela_fiscal_remover.lift()
            self.janela_fiscal_remover.grab_set()
        for nota in notas:
            nota_id = nota[0]
            caminho_completo = nota[1]
            if caminho_completo:
                nome_arquivo = os.path.basename(caminho_completo)
                self.lista_cad_nota.insert("", "end", values=(nota_id, nome_arquivo))


    def treeview_tela_eventos_1(self):
        for item in self.lista_excluir_nota.get_children():
            self.lista_excluir_nota.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, setor, usuario FROM equipamentos")
        registros = cursor.fetchall()
        for registro in registros:
            self.lista_excluir_nota.insert("", "end", values=registro)
        conn.close()


    def tela_nota_fiscal(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        if not hasattr(self, 'janela_fiscal') or not self.janela_fiscal.winfo_exists():
            #criação da janela fiscal
            self.janela_fiscal = Toplevel(self.root)
            self.janela_fiscal.title("Sagaz TEC // NOTA FISCAL")
            self.janela_fiscal.configure(background='#107db2')
            self.janela_fiscal.geometry(tamanho_tela_str)
            self.janela_fiscal.state('zoomed')
            self.janela_fiscal.maxsize(width=largura_tela, height=altura_tela)
            self.janela_fiscal.minsize(width=largura_tela, height=altura_tela)
            self.janela_fiscal.resizable(True, True)
            #tornando outras janelas não interativas
            self.janela_fiscal.grab_set()
            #Frame da imagem
            self.frame_imagem = Frame(self.janela_fiscal, bg='#107db2')
            self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
            #imagem
            rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
            rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
            #Frame botoes
            self.frame_botoes = Frame(self.janela_fiscal, bg='lightblue')
            self.frame_botoes.place(relx= 0.30, rely= 0.15, relwidth= 0.30, relheight=0.70)
            #Botões
            #Cadastrar
            self.bt_fiscal_cadastrar = Button(self.frame_botoes, text='CADASTRAR NOVA NOTA', borderwidth=5,
                                            bg='#107db2',fg='white',font=("Arial", 10),
                                            command=self.tela_cadastrar_nota)
            self.bt_fiscal_cadastrar.pack(padx=40, pady=40)
            #Visualizar
            self.bt_fiscal_visualizar_nota = Button(self.frame_botoes, text='VISUALIZAR NOTAS', borderwidth=5,
                                            bg='#107db2',fg='white',font=("Arial", 10),
                                            command=self.tela_visualizar_nota)
            self.bt_fiscal_visualizar_nota.pack(padx=40, pady=40)
            #Excluir
            self.bt_fiscal_excluir = Button(self.frame_botoes, text='EXCLUIR NOTA', borderwidth=5, bg='#107db2',
                                    fg='white',font=("Arial", 10), command=self.tela_remover_nota)
            self.bt_fiscal_excluir.pack(padx=40, pady=40)
            #cancelar
            self.bt_fiscal_cancelar = Button(self.frame_botoes, text='CANCELAR', borderwidth=5, bg='red',
                                    fg='white',font=("Arial", 10),
                                    command=lambda:self.cancelar(self.janela_fiscal, self.root))
            self.bt_fiscal_cancelar.pack(padx=40, pady=40)
        else:
            self.janela_fiscal.lift()


    def tela_cadastrar_nota(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        #criação da janela cadastrar nota
        self.janela_fiscal_cadastrar = Toplevel(self.root)
        self.janela_fiscal_cadastrar.title("Sagaz TEC // CADASTRO DE NOTA")
        self.janela_fiscal_cadastrar.configure(background='#107db2')
        self.janela_fiscal_cadastrar.geometry(tamanho_tela_str)
        self.janela_fiscal_cadastrar.state('zoomed')
        self.janela_fiscal_cadastrar.maxsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_cadastrar.minsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_cadastrar.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_fiscal_cadastrar.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_fiscal_cadastrar, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_fiscal_cadastrar, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.30, relheight=0.70)
        # Treeview
        self.lista_excluir_nota = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2'))
        self.lista_excluir_nota.pack(side='bottom', fill='both', expand=True)
        self.lista_excluir_nota.heading('#0', text='')
        self.lista_excluir_nota.heading('#1', text='ID')
        self.lista_excluir_nota.heading('#2', text='Nome Equipamento')
        self.lista_excluir_nota.column('#0', width=1)
        self.lista_excluir_nota.column('#1', width=30)
        self.lista_excluir_nota.column('#2', width=300)
        self.lista_excluir_nota.pack(pady=20)
        #scrollbar da treeview
        scroll_excluir_nota = Scrollbar(self.lista_excluir_nota, orient='vertical', command=self.lista_excluir_nota.yview)
        self.lista_excluir_nota.configure(yscrollcommand=scroll_excluir_nota.set)
        scroll_excluir_nota.pack(side='right', fill='y')
        #Frame pesquisa
        self.frame_pesquisa = Frame(self.janela_fiscal_cadastrar, bg='lightblue')
        self.frame_pesquisa.place(relx= 0.05, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #label pesquisa id
        self.lb_alterar_id = Label(self.frame_pesquisa, text='PESQUISA ID',font=("Arial", 10))
        self.lb_alterar_id.pack(padx=10,pady=10)
        #campo pesquisa id
        self.excluir_id_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3, width=20)
        self.excluir_id_entry.pack(padx=10, pady=10)
        #botão pesquisa id
        bt_pesquisa = Button(self.frame_pesquisa, text="PESQUISAR ID", 
                             bg='#107db2',borderwidth=5, fg='white', font=('Arial',10), command=self.pesquisa_id_excluir_notas)
        bt_pesquisa.pack(padx=10,pady=10)
        #label pesquisa nome
        self.lb_alterar_nome = Label(self.frame_pesquisa, text='PESQUISA NOME',font=("Arial", 10))
        self.lb_alterar_nome.pack(padx=10, pady=10)
        #campo pesquisa nome
        self.excluir_nome_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF',
                                           highlightcolor='#98F5FF', highlightthickness=3, width=30)
        self.excluir_nome_entry.pack(padx=10,pady=10)
        #botão pesquisa nome
        bt_pesquisa_alterar_nome = Button(self.frame_pesquisa,text="PESQUISAR NOME",
                                  bg='#107db2',fg='white',borderwidth=5, font=('Arial',10), command=self.pesquisa_nome_excluir_notas)
        bt_pesquisa_alterar_nome.pack(padx=10,pady=10)
        #Botão para resetar a treeview
        bt_reseta_treeview = Button(self.frame_pesquisa,text="RESETAR PESQUISA",
                                  bg='red',fg='white',borderwidth=5, font=('Arial',10), command=self.carregar_dados_fiscal)
        bt_reseta_treeview.pack(padx=40,pady=40)
        #botão Cadastrar nota selecionado
        bt_nota_selecionado = Button(self.janela_fiscal_cadastrar, text="CADASTRAR NOTA",
                                        borderwidth=5,bg='#107db2',fg='white',font=("Arial", 10),
                                        command=self.cadastrar_nota)
        bt_nota_selecionado.place(relx=0.53, rely=0.90)
        #Botão concelar
        bt_cancelar = Button(self.janela_fiscal_cadastrar, text="CANCELAR",borderwidth=5,
                             bg='red',fg='white', font=("Arial", 10),
                             command=lambda:self.cancelar(self.janela_fiscal_cadastrar, self.janela_fiscal))
        bt_cancelar.place(relx=0.42, rely=0.90)
        self.carregar_dados_fiscal()


    def tela_notas_cadastradas(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        self.janela_fiscal_cad = Toplevel(self.root)
        self.janela_fiscal_cad.title("Sagaz TEC // NOTAS CADASTRADAS")
        self.janela_fiscal_cad.configure(background='#107db2')
        self.janela_fiscal_cad.geometry(tamanho_tela_str)
        self.janela_fiscal_cad.state('zoomed')
        self.janela_fiscal_cad.maxsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_cad.minsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_cad.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_fiscal_cad.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_fiscal_cad, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_fiscal_cad, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #treeview
        self.lista_cad_nota = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2'))
        self.lista_cad_nota.pack(side='bottom', fill='both', expand=True)
        self.lista_cad_nota.heading('#0', text='')
        self.lista_cad_nota.heading('#1', text='ID')
        self.lista_cad_nota.heading('#2', text='Nota')
        self.lista_cad_nota.column('#0', width=1)
        self.lista_cad_nota.column('#1', width=30)
        self.lista_cad_nota.column('#2', width=400)
        self.lista_cad_nota.pack(pady=20)
        #scrollbar da treeview
        scroll_cad_nota = Scrollbar(self.lista_cad_nota, orient='vertical', command=self.lista_cad_nota.yview)
        self.lista_cad_nota.configure(yscrollcommand=scroll_cad_nota.set)
        scroll_cad_nota.pack(side='right', fill='y')
        #frame botoes baixo
        self.frame_botoes = Frame(self.janela_fiscal_cad, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #botoes
        #Abrir Notas
        self.bt_abrir_nota = Button(self.frame_botoes, text='ABRIR NOTA',borderwidth=5,
                                bg='#107db2',fg='white', font=("Arial", 10), command=self.abrir_nota)
        self.bt_abrir_nota.place(relx=0.42, rely=0.30)
        #Cancelar
        self.bt_cancelar = Button(self.frame_botoes, text='CANCELAR',borderwidth=5,
                                bg='red',fg='white',font=("Arial", 10),
                                command=lambda:self.cancelar(self.janela_fiscal_cad,self.janela_fiscal_visualizar))
        self.bt_cancelar.place(relx=0.10, rely=0.30)
        self.carregar_dados_notas()


    def tela_visualizar_nota(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        self.janela_fiscal_visualizar = Toplevel(self.root)
        self.janela_fiscal_visualizar.title("Sagaz TEC // VISUALIZAÇÃO DE NOTAS")
        self.janela_fiscal_visualizar.configure(background='#107db2')
        self.janela_fiscal_visualizar.geometry(tamanho_tela_str)
        self.janela_fiscal_visualizar.state('zoomed')
        self.janela_fiscal_visualizar.maxsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_visualizar.minsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_visualizar.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_fiscal_visualizar.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_fiscal_visualizar, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_fiscal_visualizar, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #treeview
        self.lista_excluir_nota = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2'))
        self.lista_excluir_nota.pack(side='bottom', fill='both', expand=True)
        self.lista_excluir_nota.heading('#0', text='')
        self.lista_excluir_nota.heading('#1', text='ID')
        self.lista_excluir_nota.heading('#2', text='Nome Equipamento')
        self.lista_excluir_nota.column('#0', width=1)
        self.lista_excluir_nota.column('#1', width=30)
        self.lista_excluir_nota.column('#2', width=300)
        self.lista_excluir_nota.pack(pady=20)
        #scrollbar da treeview
        scroll_excluir_nota = Scrollbar(self.lista_excluir_nota, orient='vertical', command=self.lista_excluir_nota.yview)
        self.lista_excluir_nota.configure(yscrollcommand=scroll_excluir_nota.set)
        scroll_excluir_nota.pack(side='right', fill='y')
        #Frame pesquisa
        self.frame_pesquisa = Frame(self.janela_fiscal_visualizar, bg='lightblue')
        self.frame_pesquisa.place(relx= 0.05, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #label pesquisa id
        self.lb_excluir_id = Label(self.frame_pesquisa, text='PESQUISA ID',font=("Arial", 10))
        self.lb_excluir_id.pack(padx=10,pady=10)
        #campo pesquisa id
        self.excluir_id_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3)
        self.excluir_id_entry.pack(padx=10,pady=10)
        #botão pesquisa id
        bt_pesquisa_id = Button(self.frame_pesquisa, text="PESQUISAR ID",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.pesquisa_id_excluir_notas)
        bt_pesquisa_id.pack(padx=10,pady=10)
        #label pesquisa nome
        self.lb_excluir_nome = Label(self.frame_pesquisa, text='PESQUISA NOME',font=("Arial", 10))
        self.lb_excluir_nome.pack(padx=10,pady=10)
        #campo pesquisa nome
        self.excluir_nome_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3)
        self.excluir_nome_entry.pack(padx=10,pady=10)
        #botão pesquisa nome
        bt_pesquisa_nome = Button(self.frame_pesquisa,text="PESQUISAR NOME",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10),command=self.pesquisa_nome_excluir_notas)
        bt_pesquisa_nome.pack(padx=10,pady=10)
        #Botão resetar treeview
        bt_reseta_treeview_excluir = Button(self.frame_pesquisa, text="RESETAR PESQUISA",
                                  bg='red', fg='white', borderwidth=5, font=("Arial", 10), command=self.carregar_dados_fiscal)
        bt_reseta_treeview_excluir.pack(padx=40,pady=40)
        #frame botoes baixo
        self.frame_botoes = Frame(self.janela_fiscal_visualizar, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #botão excluir selecionado
        bt_excluir_selecionado = Button(self.frame_botoes, text="SELECIONAR",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.tela_notas_cadastradas)
        bt_excluir_selecionado.place(relx=0.42, rely=0.30)
        #botão cancelar
        bt_cancelar = Button(self.frame_botoes, text="CANCELAR",borderwidth=5, bg='red',fg='white',
                                 font=("Arial", 10), command=lambda:self.cancelar(self.janela_fiscal_visualizar, self.janela_fiscal))
        bt_cancelar.place(relx=0.10, rely=0.30)
        self.carregar_dados_fiscal()


    def carregar_dados_notas(self):
        selected_item = self.lista_excluir_nota.selection()
        if not selected_item:
            messagebox.showwarning("Atenção", "Selecione um equipamento para visualizar suas notas fiscais.")
            return
        equipamento_id = self.lista_excluir_nota.item(selected_item, "values")[0]
        conn = sqlite3.connect(caminho_notas_fiscais)
        cursor = conn.cursor()
        cursor.execute("SELECT id, caminho FROM notas WHERE equipamento_id = ?", (equipamento_id,))
        notas = cursor.fetchall()
        conn.close()
        if not notas:
            messagebox.showinfo("Informação", "Não há notas fiscais vinculadas a este equipamento.")
            self.janela_fiscal_cad.destroy()
            self.janela_fiscal_visualizar.lift()
            self.janela_fiscal_visualizar.grab_set()
        for nota in notas:
            nota_id = nota[0]
            caminho_completo = nota[1]
            if caminho_completo:
                nome_arquivo = os.path.basename(caminho_completo)
                self.lista_cad_nota.insert("", "end", values=(nota_id, nome_arquivo))


    def tela_remover_nota(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        #criação da janela cadastrar nota
        self.janela_fiscal_remover = Toplevel(self.root)
        self.janela_fiscal_remover.title("Sagaz TEC // REMOVER NOTA")
        self.janela_fiscal_remover.configure(background='#107db2')
        self.janela_fiscal_remover.geometry(tamanho_tela_str)
        self.janela_fiscal_remover.state('zoomed')
        self.janela_fiscal_remover.maxsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_remover.minsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_remover.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_fiscal_remover.grab_set()
        #imagem
        rotulo_imagem_alterar = tk.Label(self.janela_fiscal_remover, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.82, rely=0.04)
         #frame_treeview
        self.frame_treeview = Frame(self.janela_fiscal_remover, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #treeview
        self.lista_excluir_nota = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2'))
        self.lista_excluir_nota.pack(side='bottom', fill='both', expand=True)
        self.lista_excluir_nota.heading('#0', text='')
        self.lista_excluir_nota.heading('#1', text='ID')
        self.lista_excluir_nota.heading('#2', text='Nome Equipamento')
        self.lista_excluir_nota.column('#0', width=1)
        self.lista_excluir_nota.column('#1', width=30)
        self.lista_excluir_nota.column('#2', width=300)
        self.lista_excluir_nota.pack(pady=20)
        #scrollbar da treeview
        scroll_excluir_nota = Scrollbar(self.lista_excluir_nota, orient='vertical', command=self.lista_excluir_nota.yview)
        self.lista_excluir_nota.configure(yscrollcommand=scroll_excluir_nota.set)
        scroll_excluir_nota.pack(side='right', fill='y')
        #Frame pesquisa
        self.frame_pesquisa = Frame(self.janela_fiscal_remover, bg='lightblue')
        self.frame_pesquisa.place(relx= 0.05, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #label pesquisa id
        self.lb_excluir_id = Label(self.frame_pesquisa, text='PESQUISA ID',font=("Arial", 10))
        self.lb_excluir_id.pack(padx=10,pady=10)
        #campo pesquisa id
        self.excluir_id_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3)
        self.excluir_id_entry.pack(padx=10,pady=10)
        #botão pesquisa id
        bt_pesquisa_id = Button(self.frame_pesquisa, text="PESQUISAR ID",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.pesquisa_id_excluir_notas)
        bt_pesquisa_id.pack(padx=10,pady=10)
        #label pesquisa nome
        self.lb_excluir_nome = Label(self.frame_pesquisa, text='PESQUISA NOME',font=("Arial", 10))
        self.lb_excluir_nome.pack(padx=10,pady=10)
        #campo pesquisa nome
        self.excluir_nome_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3)
        self.excluir_nome_entry.pack(padx=10,pady=10)
        #botão pesquisa nome
        bt_pesquisa_nome = Button(self.frame_pesquisa,text="PESQUISAR NOME",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10),command=self.pesquisa_nome_excluir_notas)
        bt_pesquisa_nome.pack(padx=10,pady=10)
        #Botão resetar treeview
        bt_reseta_treeview_excluir = Button(self.frame_pesquisa, text="RESETAR PESQUISA",
                                  bg='red', fg='white', borderwidth=5, font=("Arial", 10), command=self.carregar_dados_fiscal)
        bt_reseta_treeview_excluir.pack(padx=40,pady=40)
        #frame botoes baixo
        self.frame_botoes = Frame(self.janela_fiscal_remover, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #botão excluir selecionado
        bt_excluir_selecionado = Button(self.frame_botoes, text="SELECIONAR",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.tela_remover_nota_2)
        bt_excluir_selecionado.place(relx=0.42, rely=0.30)
        #botão cancelar
        bt_cancelar = Button(self.frame_botoes, text="CANCELAR",borderwidth=5, bg='red',fg='white',
                                 font=("Arial", 10), command=lambda:self.cancelar(self.janela_fiscal_remover, self.janela_fiscal))
        bt_cancelar.place(relx=0.10, rely=0.30)
        self.carregar_dados_fiscal()


    def tela_remover_nota_2(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        self.janela_fiscal_remover_2 = Toplevel(self.root)
        self.janela_fiscal_remover_2.title("Sagaz TEC // EXCLUIR NOTAS")
        self.janela_fiscal_remover_2.configure(background='#107db2')
        self.janela_fiscal_remover_2.geometry(tamanho_tela_str)
        self.janela_fiscal_remover_2.state('zoomed')
        self.janela_fiscal_remover_2.maxsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_remover_2.minsize(width=largura_tela, height=altura_tela)
        self.janela_fiscal_remover_2.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_fiscal_remover_2.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_fiscal_remover_2, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_fiscal_remover_2, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #treeview
        self.lista_cad_nota = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2'))
        self.lista_cad_nota.pack(side='bottom', fill='both', expand=True)
        self.lista_cad_nota.heading('#0', text='')
        self.lista_cad_nota.heading('#1', text='ID')
        self.lista_cad_nota.heading('#2', text='Nota')
        self.lista_cad_nota.column('#0', width=1)
        self.lista_cad_nota.column('#1', width=30)
        self.lista_cad_nota.column('#2', width=400)
        self.lista_cad_nota.pack(pady=20)
        #scrollbar da treeview
        scroll_cad_nota = Scrollbar(self.lista_cad_nota, orient='vertical', command=self.lista_cad_nota.yview)
        self.lista_cad_nota.configure(yscrollcommand=scroll_cad_nota.set)
        scroll_cad_nota.pack(side='right', fill='y')
        #frame botoes baixo
        self.frame_botoes = Frame(self.janela_fiscal_remover_2, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #botoes
        #Abrir Notas
        self.bt_abrir_nota = Button(self.frame_botoes, text='EXCLUIR NOTA',borderwidth=5,
                                bg='#107db2',fg='white', font=("Arial", 10), command=self.excluir_nota)
        self.bt_abrir_nota.place(relx=0.42, rely=0.30)
        #Cancelar
        self.bt_cancelar = Button(self.frame_botoes, text='CANCELAR',borderwidth=5,
                                bg='red',fg='white',font=("Arial", 10),
                                command=lambda:self.cancelar(self.janela_fiscal_remover_2,self.janela_fiscal_remover))
        self.bt_cancelar.place(relx=0.10, rely=0.30)
        self.carregar_dados_tela_remover_nota_2()
        

    def pesquisa_id_excluir_notas(self):
            id_equipamento = self.excluir_id_entry.get()
            if not id_equipamento or id_equipamento.isalpha():
                messagebox.showwarning("Atenção", "EQUIPAMENTO NÃO ENCONTRADO")
                return
            for item in self.lista_excluir_nota.get_children():
                self.lista_excluir_nota.delete(item)
            conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
            cursor = conn.cursor()
            cursor.execute('SELECT id, nome FROM equipamentos WHERE id = ?', (id_equipamento,))
            registros = cursor.fetchall()
            for registro in registros:
                self.lista_excluir_nota.insert("", "end", values=registro)
            conn.close()


    def pesquisa_nome_excluir_notas(self):
            id_equipamento = self.excluir_nome_entry.get().upper()
            if not id_equipamento or id_equipamento.isnumeric():
                messagebox.showwarning("Atenção", "EQUIPAMENTO NÃO ENCONTRADO")
                return
            for item in self.lista_excluir_nota.get_children():
                self.lista_excluir_nota.delete(item)
            conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM equipamentos WHERE nome LIKE ?", ('%' + id_equipamento + '%',))
            registros = cursor.fetchall()
            for registro in registros:
                self.lista_excluir_nota.insert("", "end", values=registro)
            conn.close()


    def carregar_dados_fiscal(self):
        for item in self.lista_excluir_nota.get_children():
            self.lista_excluir_nota.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, categoria, setor FROM equipamentos")
        registros = cursor.fetchall()
        for registro in registros:
            self.lista_excluir_nota.insert("", "end", values=registro)
        self.excluir_id_entry.delete(0, END)
        self.excluir_nome_entry.delete(0, END)
        conn.close()


    def cadastrar_nota(self):
        item_selecionado = self.lista_excluir_nota.focus()
        if not item_selecionado:
            messagebox.showwarning("Atenção", "Selecione um equipamento na lista para cadastrar a nota fiscal.")
            return
        equipamento_id = self.lista_excluir_nota.item(item_selecionado, 'values')[0]
        arquivo_origem = filedialog.askopenfilename(title="Selecione uma nota fiscal (PDF)", filetypes=[("PDF files", "*.pdf")])
        if not arquivo_origem:
            return
        pasta_destino = pasta_banco
        arquivo_destino = os.path.join(pasta_destino, os.path.basename(arquivo_origem))
        try:
            shutil.move(arquivo_origem, arquivo_destino)
            conn = sqlite3.connect(caminho_notas_fiscais)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notas (equipamento_id, caminho) 
                VALUES (?, ?)
            ''', (equipamento_id, arquivo_destino))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Nota fiscal cadastrada com sucesso!")
            self.janela_fiscal_cadastrar.destroy()
            self.tela_nota_fiscal()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao cadastrar a nota fiscal: {e}")


    def tela_cadastro(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{int(largura_tela)}x{int(altura_tela)}"
        #criação da janela cadastro
        self.janela_cadastro = Toplevel(self.root)
        self.janela_cadastro.title("Sagaz TEC // CADASTRO DE EQUIPAMENTOS")
        self.janela_cadastro.configure(background='#107db2')
        self.janela_cadastro.geometry(tamanho_tela_str)
        self.janela_cadastro.state('zoomed')
        self.janela_cadastro.maxsize(width=largura_tela, height=altura_tela)
        self.janela_cadastro.minsize(width=largura_tela, height=altura_tela)
        #self.janela_cadastro.resizable(True, True)
        #Frame
        self.framecadastro = Frame(self.janela_cadastro, bd=4, bg='white', highlightbackground='#98F5FF',highlightthickness=2)
        self.framecadastro.place(relx= 0.15, rely= 0.13, relwidth= 0.58, relheight=0.75)
        #tornando outras janelas não interativas
        self.janela_cadastro.grab_set()
        #imagem
        rotulo_imagem_alterar = tk.Label(self.janela_cadastro, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.82, rely=0.04)
        #entry info
        self.lb_info = Label(self.framecadastro, text='** DADOS OBRIGATÓRIOS',fg='black',font=("Arial", 10))
        self.lb_info.place(relx=0.50, rely=0.05)
        #criando o campo nome
        self.lb_nome = Label(self.framecadastro, text='**NOME',fg='black',font=("Arial", 10))
        self.lb_nome.place(relx=0.15, rely=0.15)
        self.nome_entry = Entry(self.framecadastro, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.nome_entry.place(relx=0.30, rely=0.15, width=500)
        #criando o campo setor
        self.lb_setor = Label(self.framecadastro, text='SETOR',fg='black',font=("Arial", 10))
        self.lb_setor.place(relx=0.15, rely=0.25)
        self.setor_entry = Entry(self.framecadastro, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.setor_entry.place(relx=0.30, rely=0.25, width=500)
        #criando o campo usuário:
        self.lb_usuario = Label(self.framecadastro, text='USUÁRIO',fg='black',font=("Arial", 10))
        self.lb_usuario.place(relx=0.15, rely=0.35)
        self.usuario_entry = Entry(self.framecadastro, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.usuario_entry.place(relx=0.30, rely=0.35, width=500)
        #criando o campo componentes
        self.lb_componente = Label(self.framecadastro, text='COMPONENTES',fg='black',font=("Arial", 10))
        self.lb_componente.place(relx=0.15, rely=0.45)
        self.componente_entry = Entry(self.framecadastro, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.componente_entry.place(relx=0.30, rely=0.45, width=500)
        #criando o campo categoria
        self.lb_categoria = Label(self.framecadastro, text='**CATEGORIA',fg='black',font=("Arial", 10))
        self.lb_categoria.place(relx=0.15, rely=0.55)
        self.categoria_entry = Entry(self.framecadastro, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.categoria_entry.place(relx=0.30, rely=0.55, width=500)
        #criando o campo KEY
        self.lb_key = Label(self.framecadastro, text='SERIAL KEY',fg='black',font=("Arial", 10))
        self.lb_key.place(relx=0.15, rely=0.65)
        self.key_entry = Entry(self.framecadastro, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.key_entry.place(relx=0.30, rely=0.65, width=500)
        #criando o campo observações
        self.lb_obs = Label(self.framecadastro, text='OBSERVAÇÃO',fg='black',font=("Arial", 10))
        self.lb_obs.place(relx=0.15, rely=0.75)
        self.obs_entry = Entry(self.framecadastro, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.obs_entry.place(relx=0.30, rely=0.75, width=500)
        #criando o botão de cadastrar
        self.bt_cadastrar = Button(self.framecadastro, text='CADASTRAR',
                                   borderwidth=5, bg='#107db2', fg='white',
                                   font=("Arial", 10), command=self.cadastrar)
        self.bt_cadastrar.place(relx= 0.57, rely= 0.82)
        #Botão para fechar a janela:
        self.bt_fechar = Button(self.framecadastro, text='CANCELAR', borderwidth=5, bg='red',
                                fg='white',font=("Arial", 10), command=lambda:self.cancelar(self.janela_cadastro,self.root))
        self.bt_fechar.place(relx= 0.32, rely= 0.82)


    def tela_eventos_1(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        #criação da janela cadastrar nota
        self.janela_eventos_1 = Toplevel(self.root)
        self.janela_eventos_1.title("Sagaz TEC // EVENTOS")
        self.janela_eventos_1.configure(background='#107db2')
        self.janela_eventos_1.geometry(tamanho_tela_str)
        self.janela_eventos_1.state('zoomed')
        self.janela_eventos_1.maxsize(width=largura_tela, height=altura_tela)
        self.janela_eventos_1.minsize(width=largura_tela, height=altura_tela)
        self.janela_eventos_1.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_eventos_1.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_eventos_1, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_eventos_1, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.40, relheight=0.70)
        # Treeview
        self.lista_excluir_nota = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2', 'col3', 'col4'))
        self.lista_excluir_nota.pack(side='bottom', fill='both', expand=True)
        self.lista_excluir_nota.heading('#0', text='')
        self.lista_excluir_nota.heading('#1', text='ID')
        self.lista_excluir_nota.heading('#2', text='Nome Equipamento')
        self.lista_excluir_nota.heading('#3', text='Setor Equipamento')
        self.lista_excluir_nota.heading('#4', text='Usuário')
        self.lista_excluir_nota.column('#0', width=1)
        self.lista_excluir_nota.column('#1', width=30)
        self.lista_excluir_nota.column('#2', width=100)
        self.lista_excluir_nota.column('#3', width=100)
        self.lista_excluir_nota.column('#4', width=100)
        self.lista_excluir_nota.pack(pady=20)
        #scrollbar da treeview
        scroll_excluir_nota = Scrollbar(self.lista_excluir_nota, orient='vertical', command=self.lista_excluir_nota.yview)
        self.lista_excluir_nota.configure(yscrollcommand=scroll_excluir_nota.set)
        scroll_excluir_nota.pack(side='right', fill='y')
        #Frame pesquisa
        self.frame_pesquisa = Frame(self.janela_eventos_1, bg='lightblue')
        self.frame_pesquisa.place(relx= 0.05, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #label pesquisa id
        self.lb_alterar_id = Label(self.frame_pesquisa, text='PESQUISA ID',font=("Arial", 10))
        self.lb_alterar_id.pack(padx=10,pady=10)
        #campo pesquisa id
        self.excluir_id_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3, width=20)
        self.excluir_id_entry.pack(padx=10, pady=10)
        #frame botoes baixo
        self.frame_botoes = Frame(self.janela_eventos_1, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #Botoes
        #botão pesquisa id
        bt_pesquisa = Button(self.frame_pesquisa, text="PESQUISAR ID", 
                             bg='#107db2',borderwidth=5, fg='white', font=('Arial',10), command=self.pesquisa_id_excluir_notas)
        bt_pesquisa.pack(padx=10,pady=10)
        #label pesquisa nome
        self.lb_alterar_nome = Label(self.frame_pesquisa, text='PESQUISA NOME',font=("Arial", 10))
        self.lb_alterar_nome.pack(padx=10, pady=10)
        #campo pesquisa nome
        self.excluir_nome_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF',
                                           highlightcolor='#98F5FF', highlightthickness=3, width=30)
        self.excluir_nome_entry.pack(padx=10,pady=10)
        #botão pesquisa nome
        bt_pesquisa_alterar_nome = Button(self.frame_pesquisa,text="PESQUISAR NOME",
                                  bg='#107db2',fg='white',borderwidth=5, font=('Arial',10), command=self.pesquisa_nome_excluir_notas)
        bt_pesquisa_alterar_nome.pack(padx=10,pady=10)
        #Botão para resetar a treeview
        bt_reseta_treeview = Button(self.frame_pesquisa,text="RESETAR PESQUISA",
                                  bg='red',fg='white',borderwidth=5, font=('Arial',10), command=self.carregar_dados_fiscal)
        bt_reseta_treeview.pack(padx=40,pady=40)
        #botão Cadastrar nota selecionado
        bt_nota_selecionado = Button(self.frame_botoes, text="VISUALIZAR EVENTOS",
                                        borderwidth=5,bg='#107db2',fg='white',font=("Arial", 10), command=self.ver_eventos)
        bt_nota_selecionado.place(relx=0.53, rely=0.30)
        #Botão cancelar
        bt_cancelar = Button(self.frame_botoes, text="CANCELAR",borderwidth=5, bg='red',fg='white',
                                 font=("Arial", 10), command=lambda:self.cancelar(self.janela_eventos_1, self.root))
        bt_cancelar.place(relx=0.10, rely=0.30)
        self.treeview_tela_eventos_1()


    def tela_eventos_2(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        #criação da janela cadastrar nota
        self.janela_eventos_2 = Toplevel(self.root)
        self.janela_eventos_2.title("Sagaz TEC // VISUALIZAÇÃO DE EVENTOS")
        self.janela_eventos_2.configure(background='#107db2')
        self.janela_eventos_2.geometry(tamanho_tela_str)
        self.janela_eventos_2.state('zoomed')
        self.janela_eventos_2.maxsize(width=largura_tela, height=altura_tela)
        self.janela_eventos_2.minsize(width=largura_tela, height=altura_tela)
        self.janela_eventos_2.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_eventos_2.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_eventos_2, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_eventos_2, bg='#107db2')
        self.frame_treeview.place(relx= 0.10, rely= 0.10, relwidth= 0.70, relheight=0.70)
        #Treeview
        self.tree = ttk.Treeview(self.frame_treeview, columns=("ID", "Tipo", "Descrição"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Descrição", text="Descrição")
        self.tree.column("ID", width=10)
        self.tree.column("Tipo", width=30)
        self.tree.column("Descrição", width=800)
        self.tree.pack(fill="both", expand=True)
        #scrollbar da treeview
        scroll_excluir = Scrollbar(self.frame_treeview, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=scroll_excluir.set)
        scroll_excluir.pack(side='bottom', fill='x')
        self.carregar_logs_eventos()


    def tela_chamado(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        #criação da janela cadastrar nota
        self.janela_chamado = Toplevel(self.root)
        self.janela_chamado.title("Sagaz TEC // CHAMADOS")
        self.janela_chamado.configure(background='#107db2')
        self.janela_chamado.geometry(tamanho_tela_str)
        self.janela_chamado.state('zoomed')
        self.janela_chamado.maxsize(width=largura_tela, height=altura_tela)
        self.janela_chamado.minsize(width=largura_tela, height=altura_tela)
        self.janela_chamado.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_chamado.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_chamado, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #Frame botoes
        self.frame_botoes = Frame(self.janela_chamado, bg='lightblue')
        self.frame_botoes.place(relx= 0.30, rely= 0.15, relwidth= 0.30, relheight=0.70)
        #Botões
        #Cadastrar
        self.bt_fiscal_cadastrar = Button(self.frame_botoes, text='CHAMADOS PENDENTES', borderwidth=5,
                                        bg='#107db2',fg='white',font=("Arial", 10),
                                        command=self.tela_chamado_1)
        self.bt_fiscal_cadastrar.pack(padx=50, pady=50)
        #Visualizar
        self.bt_fiscal_visualizar_nota = Button(self.frame_botoes, text='CHAMADOS RESOLVIDOS', borderwidth=5,
                                        bg='#107db2',fg='white',font=("Arial", 10),
                                        command=self.tela_chamado_2)
        self.bt_fiscal_visualizar_nota.pack(padx=50, pady=50)
        #cancelar
        self.bt_fiscal_cancelar = Button(self.frame_botoes, text='CANCELAR', borderwidth=5, bg='red',
                                fg='white',font=("Arial", 10),
                                command=lambda:self.cancelar(self.janela_chamado, self.root))
        self.bt_fiscal_cancelar.pack(padx=50, pady=50)


    def tela_chamado_1(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        #criação da janela cadastrar nota
        self.janela_chamado_1 = Toplevel(self.root)
        self.janela_chamado_1.title("Sagaz TEC // CHAMADOS PENDENTES")
        self.janela_chamado_1.configure(background='#107db2')
        self.janela_chamado_1.geometry(tamanho_tela_str)
        self.janela_chamado_1.state('zoomed')
        self.janela_chamado_1.maxsize(width=largura_tela, height=altura_tela)
        self.janela_chamado_1.minsize(width=largura_tela, height=altura_tela)
        self.janela_chamado_1.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_chamado_1.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_chamado_1, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        # Frame da Treeview
        self.frame_treeview = Frame(self.janela_chamado_1, bg='#107db2')
        self.frame_treeview.place(relx=0.01, rely=0.10, relwidth=0.50, relheight=0.70)
        # Scrollbar da Treeview
        self.scrollbar = ttk.Scrollbar(self.frame_treeview, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        # Treeview
        self.tree = ttk.Treeview(self.frame_treeview,columns=("Remetente", 
                                                              "Assunto", "Data"),show="headings",yscrollcommand=self.scrollbar.set)
        # Configuração das colunas
        self.tree.heading("Remetente", text="Remetente")
        self.tree.heading("Assunto", text="Assunto")
        self.tree.heading("Data", text="Data")
        self.tree.column("Remetente", width=100, anchor="w")
        self.tree.column("Assunto", width=200, anchor="w")
        self.tree.column("Data", width=100, anchor="w")
        # Posicionamento da Treeview
        self.tree.pack(side="left", fill="both", expand=True)
        # Vincula a Scrollbar à Treeview
        self.scrollbar.config(command=self.tree.yview)
        # Evento para exibir conteúdo
        self.tree.bind("<<TreeviewSelect>>", self.exibir_conteudo)
        #frame conteudo
        self.frame_mensagens = Frame(self.janela_chamado_1, bg='#107db2')
        self.frame_mensagens.place(relx=0.52,rely=0.10, relwidth= 0.30, relheight=0.70)
        #Scroll bar das mensagens
        self.scrollbar_msg = ttk.Scrollbar(self.frame_mensagens, orient='vertical')
        #treeview das mensagens
        self.texto_conteudo = tk.Text(self.frame_mensagens, wrap=tk.WORD, state=tk.DISABLED, yscrollcommand=self.scrollbar_msg.set)
        self.scrollbar_msg.pack(side="right", fill="y")
        self.texto_conteudo.pack(fill="both", expand=True)
        self.scrollbar_msg.config(command=self.texto_conteudo.yview)
        #frame botoes baixo
        self.frame_botoes = Frame(self.janela_chamado_1, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #botoes
        #Resolvido
        bt_resolvido = Button(self.frame_botoes, text="RESOLVIDO",borderwidth=5, bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.marcar_como_resolvido)
        bt_resolvido.place(relx=0.45, rely=0.30)
        #Cancelar
        bt_cancelar = Button(self.frame_botoes, text="CANCELAR",borderwidth=5, bg='red',fg='white',
                                 font=("Arial", 10), command=lambda:self.cancelar(self.janela_chamado_1, self.janela_chamado))
        bt_cancelar.place(relx=0.10, rely=0.30)
        self.carregar_chamados()
    

    def tela_chamado_2(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        #criação da janela
        self.janela_chamado_2 = Toplevel(self.root)
        self.janela_chamado_2.title("Sagaz TEC // CHAMADOS RESOLVIDOS")
        self.janela_chamado_2.configure(background='#107db2')
        self.janela_chamado_2.geometry(tamanho_tela_str)
        self.janela_chamado_2.state('zoomed')
        self.janela_chamado_2.maxsize(width=largura_tela, height=altura_tela)
        self.janela_chamado_2.minsize(width=largura_tela, height=altura_tela)
        self.janela_chamado_2.resizable(True, True)
        #tornando outras janelas não interativas
        self.janela_chamado_2.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_chamado_2, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_chamado_2, bg='#107db2')
        self.frame_treeview.place(relx= 0.01, rely= 0.10, relwidth= 0.50, relheight=0.70)
        #scrollbar da treeview
        self.scrollbar = tk.Scrollbar(self.frame_treeview, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")
        #Treeview
        self.tree = ttk.Treeview(self.frame_treeview, columns=("Remetente", 
                                                               "Assunto", 
                                                               "Data"), show="headings", yscrollcommand=self.scrollbar.set)
        self.tree.heading("Remetente", text="Remetente")
        self.tree.heading("Assunto", text="Assunto")
        self.tree.heading("Data", text="Data")
        self.tree.column("Remetente", width=100)
        self.tree.column("Assunto", width=50)
        self.tree.column("Data", width=50)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.exibir_conteudo)
        self.scrollbar.config(command=self.tree.yview)
        #frame conteudo
        self.frame_mensagens = Frame(self.janela_chamado_2, bg='#107db2')
        self.frame_mensagens.place(relx=0.52,rely=0.10, relwidth= 0.30, relheight=0.70)
        #treeview das mensagens
        self.texto_conteudo = tk.Text(self.frame_mensagens, wrap=tk.WORD, state=tk.DISABLED)
        self.texto_conteudo.pack(fill="both", expand=True)
        #Scroll bar do frame conteudo
        self.scroll_conteudo = tk.Scrollbar(self.texto_conteudo, orient="vertical", command=self.texto_conteudo.yview)
        self.scroll_conteudo.pack(side="right", fill="y")
        self.texto_conteudo.configure(yscrollcommand=self.scroll_conteudo.set)
        #frame botoes baixo
        self.frame_botoes = Frame(self.janela_chamado_2, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #botoes
        #Excluir
        bt_excluir = Button(self.frame_botoes, text="MOVER PARA LIXEIRA",borderwidth=5, bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.marcar_como_lixo)
        bt_excluir.place(relx=0.45, rely=0.30)
        #Cancelar
        bt_cancelar = Button(self.frame_botoes, text="CANCELAR",borderwidth=5, bg='red',fg='white',
                                 font=("Arial", 10), command=lambda:self.cancelar(self.janela_chamado_2, self.janela_chamado))
        bt_cancelar.place(relx=0.10, rely=0.30)
        self.carregar_chamados_resolvidos()


    #características da tela menú inicial
    def tela(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        self.root.title("Sagaz TEC")
        self.root.configure(background='#107db2')
        self.root.geometry(tamanho_tela_str)
        self.root.resizable(True, True)
        root.state('zoomed')
        self.root.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
        self.root.minsize(width=largura_tela, height=altura_tela)
        

    def salvar_alteracoes(self, equipamento_id):
        nome = self.nome_editar_entry.get().upper()
        setor = self.setor_editar_entry.get().upper() or 'SEM REGISTRO'
        usuario = self.usuario_editar_entry.get() or 'SEM REGISTRO'
        componentes = self.componentes_editar_entry.get().upper() or 'SEM REGISTRO'
        categoria = self.categoria_editar_entry.get().upper()
        key = self.key_editar_entry.get().upper() or 'SEM REGISTRO'
        observacao = self.observacao_editar_entry.get().upper() or 'SEM REGISTRO'
        try:
            conn = sqlite3.connect(caminho_do_banco)
            cursor = conn.cursor()
            cursor.execute('''UPDATE equipamentos 
                            SET nome=?, setor=?, usuario=?, componentes=?, categoria=?, key=?, observacao=?
                            WHERE id=?''', (nome,setor, usuario, 
                                            componentes, categoria, key, 
                                            observacao, equipamento_id))
            conn.commit()
            messagebox.showinfo("Sucesso", "Alterações salvas com sucesso!")
        except sqlite3.Error as erro:
            messagebox.showerror("Erro", f"Erro ao salvar alterações: {erro}")
        finally:
            conn.close()
        self.janela_editar.destroy()
        self.janela_alterar.destroy()
        self.carregar_dados()


    def carregar_dados(self):
        for item in self.listaequip.get_children():
            self.listaequip.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, categoria, setor, usuario FROM equipamentos")
        registros = cursor.fetchall()
        for registro in registros:
            self.listaequip.insert("", "end", values=registro)
        conn.close()


    def tela_excluir(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        self.janela_excluir = Toplevel(self.root)
        self.janela_excluir.title('Sagaz TEC // EXLCUIR EQUIPAMENTO')
        self.janela_excluir.configure(background='#107db2')
        self.janela_excluir.geometry(tamanho_tela_str)
        self.janela_excluir.state('zoomed')
        self.janela_excluir.maxsize(root.winfo_screenwidth(), root.winfo_screenheight())
        self.janela_excluir.minsize(width=largura_tela, height=altura_tela)
        self.janela_excluir.resizable(TRUE, TRUE)
        self.janela_excluir.grab_set()
        #imagem
        rotulo_imagem_alterar = tk.Label(self.janela_excluir, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.82, rely=0.04)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_excluir, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.30, relheight=0.70)
        # Treeview
        self.lista_excluir = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2'))
        self.lista_excluir.pack(side='bottom', fill='both', expand=True)
        self.lista_excluir.heading('#0', text='')
        self.lista_excluir.heading('#1', text='ID')
        self.lista_excluir.heading('#2', text='Nome Equipamento')
        self.lista_excluir.column('#0', width=1)
        self.lista_excluir.column('#1', width=30)
        self.lista_excluir.column('#2', width=300)
        self.lista_excluir.pack(pady=20)
        #scrollbar da treeview
        scroll_excluir = Scrollbar(self.lista_excluir, orient='vertical', command=self.lista_excluir.yview)
        self.lista_excluir.configure(yscrollcommand=scroll_excluir.set)
        scroll_excluir.pack(side='right', fill='y')
        #Frame das pesquisas
        self.frame_pesquisa = Frame(self.janela_excluir, bg='lightblue')
        self.frame_pesquisa.place(relx= 0.05, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #label pesquisa id
        self.lb_excluir_id = Label(self.frame_pesquisa, text='PESQUISA ID',font=("Arial", 10))
        self.lb_excluir_id.pack(padx=10,pady=10)
        #campo pesquisa id
        self.excluir_id_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3)
        self.excluir_id_entry.pack(padx=10,pady=10)
        #botão pesquisa id
        bt_pesquisa_id = Button(self.frame_pesquisa, text="PESQUISAR ID",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.pesquisa_id_excluir)
        bt_pesquisa_id.pack(padx=10,pady=10)
        #label pesquisa nome
        self.lb_excluir_nome = Label(self.frame_pesquisa, text='PESQUISA NOME',font=("Arial", 10))
        self.lb_excluir_nome.pack(padx=10,pady=10)
        #campo pesquisa nome
        self.excluir_nome_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3)
        self.excluir_nome_entry.pack(padx=10,pady=10)
        #botão pesquisa nome
        bt_pesquisa_nome = Button(self.frame_pesquisa,text="PESQUISAR NOME",borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10),command=self.pesquisa_nome_excluir)
        bt_pesquisa_nome.pack(padx=10,pady=10)
        #Botão resetar treeview
        bt_reseta_treeview_excluir = Button(self.frame_pesquisa, text="RESETAR PESQUISA",
                                  bg='red', fg='white', borderwidth=5, font=("Arial", 10), command=self.carregar_dados_exclusao)
        bt_reseta_treeview_excluir.pack(padx=40,pady=40)
        #frame_botoes1
        self.frame_botoes = Frame(self.janela_excluir, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        #botão excluir selecionado
        bt_excluir_selecionado = Button(self.frame_botoes, text="EXCLUIR SELECIONADO",borderwidth=5,bg='#107db2',
                                        fg='white',font=("Arial", 10), command=self.excluir)
        bt_excluir_selecionado.place(relx=0.42, rely=0.30)
        #botão cancelar
        bt_cancelar = Button(self.frame_botoes, text="CANCELAR",borderwidth=5, bg='red',fg='white',
                                 font=("Arial", 10), 
                                 command=lambda:self.cancelar(self.janela_excluir, self.root))
        bt_cancelar.place(relx=0.10, rely=0.30)
        self.carregar_dados_exclusao()


    def excluir(self):
        selecionado = self.lista_excluir.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um equipamento para excluir!")
            return
        valores_item = self.lista_excluir.item(selecionado, 'values')
        id_equipamento = valores_item[0]
        nome_equipamento = valores_item[1]
        confirmar = messagebox.askyesno("Confirmação", "Tem certeza que deseja excluir este equipamento?")
        if confirmar:
            try:
                conn = sqlite3.connect(caminho_do_banco)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM equipamentos WHERE id = ?", (id_equipamento,))
                conn.commit()
                conn.close()
                self.lista_excluir.delete(selecionado)
                for item in self.listaequip.get_children():
                    if self.listaequip.item(item, 'values')[0] == id_equipamento:
                        self.listaequip.delete(item)
                        break
                messagebox.showinfo('Sucesso', f"Equipamento {nome_equipamento} excluído.")
            except sqlite3.Error as e:
                print(f"Erro ao excluir equipamento: {e}")
        else:
            print("Nenhum equipamento selecionado.")


    #função para alterar na tela de cadastrar
    def alterar(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{largura_tela}x{altura_tela}".replace(' ', '')
        # Criação da nova janela
        self.janela_alterar = Toplevel(self.root)
        self.janela_alterar.title("Sagaz TEC // ALTERAR EQUIPAMENTO")
        self.janela_alterar.configure(background='#107db2')
        self.janela_alterar.geometry(tamanho_tela_str)
        self.janela_alterar.state('zoomed')
        self.janela_alterar.maxsize(width=largura_tela, height=altura_tela)
        self.janela_alterar.minsize(width=largura_tela, height=altura_tela)
        self.janela_alterar.resizable(True, True)
        # Tornar outras janelas não interativas
        self.janela_alterar.grab_set()
        #Frame da imagem
        self.frame_imagem = Frame(self.janela_alterar, bg='#107db2')
        self.frame_imagem.place(relx= 0.82, rely= 0.04, relwidth= 0.17, relheight=0.34)
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame_imagem, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.02, rely=0.04)
        #Frame pesquisa
        self.frame_pesquisa = Frame(self.janela_alterar, bg='lightblue')
        self.frame_pesquisa.place(relx= 0.05, rely= 0.10, relwidth= 0.30, relheight=0.70)
        #label pesquisa id
        self.lb_alterar_id = Label(self.frame_pesquisa, text='PESQUISA ID',font=("Arial", 10))
        self.lb_alterar_id.pack(padx=10,pady=10)
        #campo pesquisa id
        self.lb_alterar_id_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF', 
                                                highlightcolor='#98F5FF', highlightthickness=3, width=20)
        self.lb_alterar_id_entry.pack(padx=10, pady=10)
        #botão pesquisa id
        bt_pesquisa = Button(self.frame_pesquisa, text="PESQUISAR ID", 
                             bg='#107db2',borderwidth=5, fg='white', font=('Arial',10), command=self.pesquisa_id_alterar)
        bt_pesquisa.pack(padx=10,pady=10)
        #label pesquisa nome
        self.lb_alterar_nome = Label(self.frame_pesquisa, text='PESQUISA NOME',font=("Arial", 10))
        self.lb_alterar_nome.pack(padx=10, pady=10)
        #campo pesquisa nome
        self.lb_alterar_nome_entry = Entry(self.frame_pesquisa, bd=4, highlightbackground='#98F5FF',
                                           highlightcolor='#98F5FF', highlightthickness=3, width=30)
        self.lb_alterar_nome_entry.pack(padx=10,pady=10)
        #botão pesquisa nome
        bt_pesquisa_alterar_nome = Button(self.frame_pesquisa,text="PESQUISAR NOME",
                                  bg='#107db2',fg='white',borderwidth=5, font=('Arial',10), command=self.pesquisa_nome_alterar)
        bt_pesquisa_alterar_nome.pack(padx=10,pady=10)
        #Botão para resetar a treeview
        bt_reseta_treeview = Button(self.frame_pesquisa,text="RESETAR PESQUISA",
                                  bg='red',fg='white',borderwidth=5, font=('Arial',10), command=self.carregar_dados_alteracao)
        bt_reseta_treeview.pack(padx=40,pady=40)
        #frame_treeview
        self.frame_treeview = Frame(self.janela_alterar, bg='#107db2')
        self.frame_treeview.place(relx= 0.40, rely= 0.10, relwidth= 0.30, relheight=0.70)
        # Criar uma Treeview para exibir os equipamentos
        self.lista_alterar = ttk.Treeview(self.frame_treeview, height=25, columns=('col1', 'col2'))
        self.lista_alterar.pack(side='bottom', fill='both', expand=True)
        self.lista_alterar.heading('#0', text='')
        self.lista_alterar.heading('#1', text='ID')
        self.lista_alterar.heading('#2', text='Nome')
        # Posicionar as colunas
        self.lista_alterar.column('#0', width=10)
        self.lista_alterar.column('#1', width=40)
        self.lista_alterar.column('#2', width=250)
        self.lista_alterar.pack(pady=20)
        # Adicionar barra de rolagem
        scroll_vertical = Scrollbar(self.lista_alterar, orient='vertical', command=self.lista_alterar.yview)
        scroll_vertical.pack(side='right', fill='y')
        self.lista_alterar.configure(yscrollcommand=scroll_vertical.set)
        # Carregar dados na Treeview
        self.carregar_dados_alteracao()
        #frame_botoes1
        self.frame_botoes = Frame(self.janela_alterar, bd=4, bg='#107db2', highlightbackground='#107db2',highlightthickness=2)
        self.frame_botoes.place(relx= 0.40, rely= 0.80, relwidth= 0.30, relheight=0.10)
        # Botão para abrir a janela de edição
        bt_editar = Button(self.frame_botoes, text="EDITAR SELECIONADO", bg='#107db2', fg='white',
                           borderwidth=5, font=('Arial',10), command=self.editar_equipamento)
        bt_editar.place(relx=0.42, rely=0.30)
        bt_cancelar = Button(self.frame_botoes, text="CANCELAR", bg='red', fg='white',
                             borderwidth=5, font=('Arial',10), command=lambda:self.cancelar(self.janela_alterar,self.root))
        bt_cancelar.place(relx=0.10, rely=0.30)


    def carregar_dados_alteracao(self):
        """Carrega os dados dos equipamentos para a janela de alteração."""
        for item in self.lista_alterar.get_children():
            self.lista_alterar.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, setor,usuario, componentes, categoria, key, observacao  FROM equipamentos")
        registros = cursor.fetchall()
        for registro in registros:
            self.lista_alterar.insert("", "end", values=registro)
        conn.close()
        self.lb_alterar_id_entry.delete(0, END)
        self.lb_alterar_nome_entry.delete(0, END)


    def carregar_dados_exclusao(self):
            """Carrega os dados dos equipamentos para a janela de alteração."""
            for item in self.lista_excluir.get_children():
                self.lista_excluir.delete(item)
            conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id, nome FROM equipamentos")
            registros = cursor.fetchall()
            for registro in registros:
                self.lista_excluir.insert("", "end", values=registro)
            conn.close()
            self.excluir_id_entry.delete(0, END)
            self.excluir_nome_entry.delete(0, END)


    def pesquisa_id_excluir(self):
        id_equipamento = self.excluir_id_entry.get()
        if not id_equipamento or id_equipamento.isalpha():
            messagebox.showwarning("Atenção", "EQUIPAMENTO NÃO ENCONTRADO")
            return
        for item in self.lista_excluir.get_children():
            self.lista_excluir.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome FROM equipamentos WHERE id = ?', (id_equipamento,))
        registros = cursor.fetchall()
        for registro in registros:
            self.lista_excluir.insert("", "end", values=registro)
        conn.close()

    
    def pesquisa_nome_excluir(self):
        id_equipamento = self.excluir_nome_entry.get().upper()
        if not id_equipamento or id_equipamento.isnumeric():
            messagebox.showwarning("Atenção", "EQUIPAMENTO NÃO ENCONTRADO")
            return
        for item in self.lista_excluir.get_children():
            self.lista_excluir.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipamentos WHERE nome LIKE ?", ('%' + id_equipamento + '%',))
        registros = cursor.fetchall()
        for registro in registros:
            self.lista_excluir.insert("", "end", values=registro)
        conn.close()

    #Função para o filtro de pesquisa por ID
    def pesquisa_id_alterar(self):
        id_equipamento = self.lb_alterar_id_entry.get()
        if not id_equipamento or id_equipamento.isalpha():
            messagebox.showwarning("Atenção", "EQUIPAMENTO NÃO ENCONTRADO")
            return
        for item in self.lista_alterar.get_children():
            self.lista_alterar.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome FROM equipamentos WHERE id = ?', (id_equipamento,))
        registros = cursor.fetchall()
        for registro in registros:
            self.lista_alterar.insert("", "end", values=registro)
        conn.close()

    #Função para o filtro de pesquisa por nome
    def pesquisa_nome_alterar(self):
        id_equipamento = self.lb_alterar_nome_entry.get()
        if not id_equipamento or id_equipamento.isnumeric():
            messagebox.showwarning("Atenção", "EQUIPAMENTO NÃO ENCONTRADO")
            return
        for item in self.lista_alterar.get_children():
            self.lista_alterar.delete(item)
        conn = sqlite3.connect(os.path.join(os.path.expanduser("~"), "Documents", "Estoque_TI", "estoque.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM equipamentos WHERE nome LIKE ?", ('%' + id_equipamento + '%',))
        registros = cursor.fetchall()
        for registro in registros:
            self.lista_alterar.insert("", "end", values=registro)
        conn.close()

    #Tela de editar equipamento
    def editar_equipamento(self):
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        tamanho_tela_str = f"{int(largura_tela)}x{int(altura_tela)}"
        """Função que abre uma janela de edição para o equipamento selecionado."""
        selecionado = self.lista_alterar.selection()
        if not selecionado:
            messagebox.showwarning("Atenção", "Selecione um equipamento para editar!")
            return
        item = self.lista_alterar.item(selecionado)
        equipamento_id = item['values'][0]
        nome = item['values'][1]
        setor = item['values'][2]
        usuario = item['values'][3]
        componentes = item['values'][4]
        categoria = item['values'][5]
        key = item['values'][6]
        observacao = item['values'][7]
        # Criar a janela de edição
        self.janela_editar = Toplevel(self.janela_alterar)
        self.janela_editar.title("Sagaz TEC // EDITAR EQUIPAMENTO")
        self.janela_editar.configure(background='#107db2')
        self.janela_editar.geometry(tamanho_tela_str)
        self.janela_editar.state('zoomed')
        #self.janela_editar.resizable(False, False)
        self.janela_editar.maxsize(width=largura_tela, height=altura_tela)
        self.janela_editar.minsize(width=largura_tela, height=altura_tela)
        self.janela_editar.grab_set()
        #imagem
        rotulo_imagem_alterar = tk.Label(self.janela_editar, image=self.imagem_tk, bg='#107db2')
        rotulo_imagem_alterar.place(relx=0.82, rely=0.04)
        #frame
        self.frame_editar = Frame(self.janela_editar, bd=4, bg='white', 
                                  highlightbackground='#98F5FF',highlightthickness=2)
        self.frame_editar.place(relx= 0.28, rely= 0.02, relwidth= 0.50, relheight=0.80)
        # Criar campos para edição (usando valores atuais)
        #INFO LABEL
        Label(self.janela_editar, text='** DADOS OBRIGATÓRIOS').place(relx=0.50, rely=0.03)
        self.nome_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        #nome
        Label(self.janela_editar, text='**NOME').place(relx=0.30, rely=0.07)
        self.nome_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.nome_editar_entry.place(relx=0.38, rely=0.07, width=500)
        self.nome_editar_entry.insert(0, nome)
        #setor
        Label(self.janela_editar, text='SETOR').place(relx=0.30, rely=0.17)
        self.setor_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.setor_editar_entry.place(relx=0.38, rely=0.17, width=500)
        self.setor_editar_entry.insert(0, setor)
        #Usuário
        Label(self.janela_editar, text='USUÁRIO').place(relx=0.30, rely=0.27)
        self.usuario_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.usuario_editar_entry.place(relx=0.38, rely=0.27, width=500)
        self.usuario_editar_entry.insert(0, usuario)
        #Componentes
        Label(self.janela_editar, text='COMPONENTES').place(relx=0.30, rely=0.37)
        self.componentes_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.componentes_editar_entry.place(relx=0.38, rely=0.37, width=500)
        self.componentes_editar_entry.insert(0, componentes)
        #Categoria
        Label(self.janela_editar, text='**CATEGORIA').place(relx=0.30, rely=0.47)
        self.categoria_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.categoria_editar_entry.place(relx=0.38, rely=0.47, width=500)
        self.categoria_editar_entry.insert(0, categoria)
        #Key
        Label(self.janela_editar, text='KEY').place(relx=0.30, rely=0.57)
        self.key_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.key_editar_entry.place(relx=0.38, rely=0.57, width=500)
        self.key_editar_entry.insert(0, key)
        #Observação
        Label(self.janela_editar, text='OBSERVAÇÃO').place(relx=0.30, rely=0.67)
        self.observacao_editar_entry = Entry(self.janela_editar, highlightbackground='#107db2', 
                                                highlightcolor='#107db2', highlightthickness=2)
        self.observacao_editar_entry.place(relx=0.38, rely=0.67, width=500)
        self.observacao_editar_entry.insert(0, observacao)
        # Botão para salvar as alterações
        bt_salvar = Button(self.janela_editar, text="SALVAR ALTERAÇÕES", borderwidth=5, bg='#107db2', fg='white',font=("Arial", 10), 
                            command=lambda: messagebox.showwarning('Atenção','Insira Todos os dados')if not self.nome_editar_entry.get() or not self.categoria_editar_entry.get() else self.salvar_alteracoes(equipamento_id))
        bt_salvar.place(relx=0.55, rely=0.75)
        bt_cancelar = Button(self.janela_editar, text="CANCELAR", borderwidth=5, bg='red',
                                fg='white',font=("Arial", 10), command=lambda:self.cancelar(self.janela_editar,self.janela_alterar))
        bt_cancelar.place(relx=0.45, rely=0.75)


    #função para cadastrar na tela de cadastrar
    def cadastrar(self):
        nome = self.nome_entry.get().upper()
        categoria = self.categoria_entry.get().upper()
        setor = self.setor_entry.get().upper() or 'NÂO REGISTRADO'
        usuario = self.usuario_entry.get() or 'NÂO REGISTRADO'
        componentes = self.componente_entry.get().upper() or 'NÃO REGISTRADO'
        key = self.key_entry.get().upper() or 'NÃO REGISTRADO'
        observacao = self.obs_entry.get().upper() or 'SEM OBSERVAÇÃO'
        if not nome or not categoria:
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
        INSERT INTO equipamentos (nome, categoria, setor, usuario, componentes, key, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, categoria, setor, usuario, componentes, key, observacao))
        conn.commit()
        conn.close()
        self.limpar_campos()
        messagebox.showinfo("Sucesso", "Equipamento cadastrado com sucesso!")
        self.carregar_dados()
        self.janela_cadastro.destroy()


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
        self.frame1 = Frame(self.root, bd=4, bg='white', highlightbackground='#98F5FF',highlightthickness=2)
        self.frame1.place(relx= 0.02, rely= 0.02, relwidth= 0.96, relheight=0.46)
        self.frame2 = Frame(self.root, bd=4, bg='white', highlightbackground='#98F5FF', highlightthickness=2)
        self.frame2.place(relx= 0.02, rely= 0.5, relwidth= 0.96, relheight=0.46)


    def widgets_frame1(self):
        #imagem
        rotulo_imagem_alterar = tk.Label(self.frame1, image=self.imagem_tk, background='white')
        rotulo_imagem_alterar.place(relx=0.82, rely=0.04)
        #criando o botão cadastrar:
        self.bt_cadastrar = Button(self.frame1, text='CADASTRAR EQUIPAMENTO',bg='#107db2',fg='white',font=("Arial", 10), command=self.tela_cadastro,borderwidth=5)
        self.bt_cadastrar.place(relx=0.01, rely=0.01, relwidth=0.15, relheight=0.10)
        #criando o botão alterar:
        self.bt_alterar = Button(self.frame1, text='ALTERAR EQUIPAMENTO',borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10),command=self.alterar)
        self.bt_alterar.place(relx=0.01, rely=0.15, relwidth=0.15, relheight=0.10)
        #criando o botão excluir:
        self.bt_excluir = Button(self.frame1, text='EXCLUIR EQUIPAMENTO',borderwidth=5,bg='#107db2',fg='white',
                                 font=("Arial", 10), command=self.tela_excluir)
        self.bt_excluir.place(relx=0.01, rely=0.30, relwidth=0.15, relheight=0.10)
        #criando o botão de vincular nota fiscal:
        self.bt_fiscal = Button(self.frame1, text='NOTAS FISCAIS',borderwidth=5,bg='#107db2',fg='white',
                                font=("Arial", 10), command=self.tela_nota_fiscal)
        self.bt_fiscal.place(relx=0.01, rely=0.45, relwidth=0.15, relheight=0.10)
        #botão de chamados
        self.bt_chamado = Button(self.frame1, text='CHAMADOS',borderwidth=5,bg='#107db2',fg='white',
                                font=("Arial", 10), command=self.tela_chamado)
        self.bt_chamado.place(relx=0.01, rely=0.60, relwidth=0.15, relheight=0.10)
        #botão de eventos
        self.bt_eventos = Button(self.frame1, text='LOG DE EVENTOS',borderwidth=5,bg='#107db2',fg='white',
                                font=("Arial", 10), command=self.tela_eventos_1)
        self.bt_eventos.place(relx=0.01, rely=0.75, relwidth=0.15, relheight=0.10)
        #criando o botão para fechar o programa:
        self.bt_fechar = Button(self.frame1, text='FECHAR PROGRAMA',borderwidth=5,bg='red',fg='white',
                                font=("Arial", 10), command=self.root.destroy)
        self.bt_fechar.place(relx=0.01, rely=0.90, relwidth=0.15, relheight=0.10)


    def lista_frame2(self):
        #criando as colunas da lista do frame2
        self.listaequip = ttk.Treeview(self.frame2, height=3, columns=('col1', 'col2', 'col3', 'col4', 'col5'))
        self.carregar_dados()
        self.listaequip.heading('#0', text='')
        self.listaequip.heading('#1', text='ID')
        self.listaequip.heading('#2', text='Nome')
        self.listaequip.heading('#3', text='Categoria')
        self.listaequip.heading('#4', text='Setor')
        self.listaequip.heading('#5', text='Usuário')
        #posicionando e dimensionando as colunas
        self.listaequip.column('#0', width=1)
        self.listaequip.column('#1', width=10)
        self.listaequip.column('#2', width=50)
        self.listaequip.column('#3', width=50)
        self.listaequip.column('#4', width=50)
        self.listaequip.column('#5', width=50)
        self.listaequip.place(relx=0.01, rely=0.1, relwidth=0.95, relheight=0.85)
        #criando a barra de rolagem
        self.scroll_lista = Scrollbar(self.frame2, orient='vertical', command=self.listaequip.yview)
        self.listaequip.configure(yscrollcommand=self.scroll_lista.set)
        self.scroll_lista.place(relx=0.96, rely=0.1, relwidth=0.02, relheight=0.85)


banco_equipamentos()
banco_notas()
Application()