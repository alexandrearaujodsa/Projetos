import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import pandas as pd
import os
from tkinter import font as tkfont
from ttkthemes import ThemedTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np


class MiniExcel:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Excel Pro")
        self.root.state('zoomed')  # Iniciar maximizado
        self.dataframe = None
        self.filename = None
        self.clipboard = None
        self.selected_cells = []
        self.undo_stack = []
        self.redo_stack = []
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure("Treeview", rowheight=25)
        self.style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        
        # Configurar menu
        self.setup_menu()

        # Frame principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame para a barra de ferramentas
        self.toolbar = ttk.Frame(self.main_frame)
        self.toolbar.pack(fill=tk.X, padx=5, pady=2)
        self.setup_toolbar()

        # Frame para a barra de fórmulas
        self.formula_bar = ttk.Frame(self.main_frame)
        self.formula_bar.pack(fill=tk.X, padx=5, pady=2)
        self.setup_formula_bar()

        # Frame para a tabela e barra de status
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # Painel esquerdo para múltiplas planilhas
        self.sheets_frame = ttk.Frame(self.content_frame, width=150)
        self.sheets_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.setup_sheets_panel()

        # Frame para a tabela (Treeview)
        self.tree_frame = ttk.Frame(self.content_frame)
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars
        self.setup_scrollbars()
        
        self.tree = None
        self.current_sheet = None
        self.sheets = {}

        # Barra de status
        self.status_bar = ttk.Label(self.root, text="Pronto", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Configurar atalhos de teclado
        self.setup_shortcuts()
        
        # Criar primeira planilha
        self.new_sheet("Planilha1")

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Novo", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Abrir", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Salvar", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)

        # Menu Editar
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Desfazer", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Refazer", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Copiar", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Colar", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_command(label="Recortar", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_separator()
        edit_menu.add_command(label="Buscar", command=self.show_search_dialog, accelerator="Ctrl+F")
        edit_menu.add_command(label="Substituir", command=self.show_replace_dialog, accelerator="Ctrl+H")

        # Menu Formatar
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Formatar", menu=format_menu)
        format_menu.add_command(label="Negrito", command=lambda: self.format_cell("bold"))
        format_menu.add_command(label="Itálico", command=lambda: self.format_cell("italic"))
        format_menu.add_command(label="Sublinhado", command=lambda: self.format_cell("underline"))
        format_menu.add_separator()
        format_menu.add_command(label="Cor do Texto", command=self.choose_text_color)
        format_menu.add_command(label="Cor do Fundo", command=self.choose_background_color)
        format_menu.add_separator()
        format_menu.add_command(label="Alinhar à Esquerda", command=lambda: self.align_cell("left"))
        format_menu.add_command(label="Centralizar", command=lambda: self.align_cell("center"))
        format_menu.add_command(label="Alinhar à Direita", command=lambda: self.align_cell("right"))

        # Menu Visualizar
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Visualizar", menu=view_menu)
        view_menu.add_command(label="Zoom +", command=self.zoom_in)
        view_menu.add_command(label="Zoom -", command=self.zoom_out)
        view_menu.add_separator()
        view_menu.add_command(label="Congelar Painéis", command=self.freeze_panes)

        # Menu Dados
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dados", menu=data_menu)
        data_menu.add_command(label="Ordenar (Crescente)", command=lambda: self.sort_data("asc"))
        data_menu.add_command(label="Ordenar (Decrescente)", command=lambda: self.sort_data("desc"))
        data_menu.add_separator()
        data_menu.add_command(label="Filtrar", command=self.toggle_filters)
        data_menu.add_separator()
        data_menu.add_command(label="Criar Gráfico", command=self.create_chart)

    def setup_toolbar(self):
        # Estilo para os botões
        button_style = {"width": 3, "padding": 2}
        
        # Frame para formatação de texto
        format_frame = ttk.LabelFrame(self.toolbar, text="Formatação")
        format_frame.pack(side=tk.LEFT, padx=5, pady=2)

        ttk.Button(format_frame, text="N", style="Bold.TButton", command=lambda: self.format_cell("bold"), **button_style).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="I", style="Italic.TButton", command=lambda: self.format_cell("italic"), **button_style).pack(side=tk.LEFT, padx=2)
        ttk.Button(format_frame, text="S", style="Underline.TButton", command=lambda: self.format_cell("underline"), **button_style).pack(side=tk.LEFT, padx=2)

        # Frame para alinhamento
        align_frame = ttk.LabelFrame(self.toolbar, text="Alinhamento")
        align_frame.pack(side=tk.LEFT, padx=5, pady=2)

        ttk.Button(align_frame, text="←", command=lambda: self.align_cell("left"), **button_style).pack(side=tk.LEFT, padx=2)
        ttk.Button(align_frame, text="↔", command=lambda: self.align_cell("center"), **button_style).pack(side=tk.LEFT, padx=2)
        ttk.Button(align_frame, text="→", command=lambda: self.align_cell("right"), **button_style).pack(side=tk.LEFT, padx=2)

        # Frame para cores
        color_frame = ttk.LabelFrame(self.toolbar, text="Cores")
        color_frame.pack(side=tk.LEFT, padx=5, pady=2)

        self.text_color_btn = ttk.Button(color_frame, text="A", command=self.choose_text_color, **button_style)
        self.text_color_btn.pack(side=tk.LEFT, padx=2)

        self.bg_color_btn = ttk.Button(color_frame, text="█", command=self.choose_background_color, **button_style)
        self.bg_color_btn.pack(side=tk.LEFT, padx=2)

        # Frame para fórmulas
        formula_frame = ttk.LabelFrame(self.toolbar, text="Fórmulas")
        formula_frame.pack(side=tk.LEFT, padx=5, pady=2)

        formulas = ["Selecione uma fórmula", "SOMA", "MÉDIA", "MÁXIMO", "MÍNIMO", "CONTAGEM", "MEDIANA"]
        self.formula_var = tk.StringVar()
        self.formula_combo = ttk.Combobox(formula_frame, textvariable=self.formula_var, values=formulas, width=20)
        self.formula_combo.pack(side=tk.LEFT, padx=2)
        self.formula_combo.set(formulas[0])
        self.formula_combo.bind("<<ComboboxSelected>>", self.apply_formula)

    def setup_formula_bar(self):
        # Label para mostrar a referência da célula
        self.cell_ref_label = ttk.Label(self.formula_bar, text="A1", width=10)
        self.cell_ref_label.pack(side=tk.LEFT, padx=5)

        # Entry para edição de fórmulas
        self.formula_entry = ttk.Entry(self.formula_bar)
        self.formula_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.formula_entry.bind("<Return>", self.apply_formula_from_bar)

    def setup_sheets_panel(self):
        # Lista de planilhas
        self.sheets_list = ttk.Treeview(self.sheets_frame, show="tree", selectmode="browse")
        self.sheets_list.pack(fill=tk.BOTH, expand=True)
        self.sheets_list.bind("<<TreeviewSelect>>", self.change_sheet)

        # Botões para gerenciar planilhas
        btn_frame = ttk.Frame(self.sheets_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(btn_frame, text="+", command=lambda: self.new_sheet(f"Planilha{len(self.sheets)+1}"), width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="-", command=self.delete_sheet, width=3).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✎", command=self.rename_sheet, width=3).pack(side=tk.LEFT, padx=2)

    def setup_scrollbars(self):
        # Scrollbar horizontal
        self.h_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Scrollbar vertical
        self.v_scrollbar = ttk.Scrollbar(self.tree_frame)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def new_sheet(self, name):
        if name not in self.sheets:
            self.sheets[name] = pd.DataFrame()
            self.sheets_list.insert("", "end", text=name, iid=name)
            if not self.current_sheet:
                self.current_sheet = name
                self.populate_tree(name)

    def change_sheet(self, event):
        selection = self.sheets_list.selection()
        if selection:
            sheet_name = selection[0]
            self.current_sheet = sheet_name
            self.populate_tree(sheet_name)

    def delete_sheet(self):
        if len(self.sheets) <= 1:
            messagebox.showwarning("Aviso", "Não é possível excluir a última planilha!")
            return
        if self.current_sheet:
            if messagebox.askyesno("Confirmar", f"Deseja excluir a planilha {self.current_sheet}?"):
                del self.sheets[self.current_sheet]
                self.sheets_list.delete(self.current_sheet)
                self.current_sheet = next(iter(self.sheets))
                self.populate_tree(self.current_sheet)

    def rename_sheet(self):
        if self.current_sheet:
            new_name = tk.simpledialog.askstring("Renomear", "Novo nome da planilha:", 
                                               initialvalue=self.current_sheet)
            if new_name and new_name != self.current_sheet:
                if new_name not in self.sheets:
                    self.sheets[new_name] = self.sheets.pop(self.current_sheet)
                    self.sheets_list.item(self.current_sheet, text=new_name)
                    self.sheets_list.item(self.current_sheet, iid=new_name)
                    self.current_sheet = new_name
                else:
                    messagebox.showwarning("Erro", "Já existe uma planilha com este nome!")

    def show_search_dialog(self):
        search_dialog = tk.Toplevel(self.root)
        search_dialog.title("Buscar")
        search_dialog.geometry("300x100")
        search_dialog.transient(self.root)
        
        ttk.Label(search_dialog, text="Buscar:").pack(padx=5, pady=5)
        search_entry = ttk.Entry(search_dialog)
        search_entry.pack(fill=tk.X, padx=5)
        
        def do_search():
            text = search_entry.get()
            self.search_in_cells(text)
            
        ttk.Button(search_dialog, text="Buscar", command=do_search).pack(pady=5)

    def show_replace_dialog(self):
        replace_dialog = tk.Toplevel(self.root)
        replace_dialog.title("Substituir")
        replace_dialog.geometry("300x150")
        replace_dialog.transient(self.root)
        
        ttk.Label(replace_dialog, text="Buscar:").pack(padx=5, pady=5)
        search_entry = ttk.Entry(replace_dialog)
        search_entry.pack(fill=tk.X, padx=5)
        
        ttk.Label(replace_dialog, text="Substituir por:").pack(padx=5, pady=5)
        replace_entry = ttk.Entry(replace_dialog)
        replace_entry.pack(fill=tk.X, padx=5)
        
        def do_replace():
            search_text = search_entry.get()
            replace_text = replace_entry.get()
            self.replace_in_cells(search_text, replace_text)
            
        ttk.Button(replace_dialog, text="Substituir", command=do_replace).pack(pady=5)

    def new_file(self):
        self.dataframe = pd.DataFrame()
        self.filename = None
        self.populate_tree()

    def copy(self):
        if not self.tree:
            return
        selection = self.tree.selection()
        if not selection:
            return
        self.clipboard = []
        for item in selection:
            values = self.tree.item(item)["values"]
            self.clipboard.append(values)

    def paste(self):
        if not self.clipboard or not self.tree:
            return
        selection = self.tree.selection()
        if not selection:
            return
        start_idx = self.tree.index(selection[0])
        for i, values in enumerate(self.clipboard):
            if start_idx + i < len(self.dataframe):
                for j, value in enumerate(values):
                    if j < len(self.dataframe.columns):
                        self.dataframe.iloc[start_idx + i, j] = value
        self.populate_tree()

    def cut(self):
        self.copy()
        selection = self.tree.selection()
        if not selection:
            return
        for item in selection:
            idx = self.tree.index(item)
            self.dataframe.iloc[idx] = None
        self.populate_tree()

    def insert_row(self):
        if self.dataframe is None:
            return
        selection = self.tree.selection()
        if not selection:
            idx = len(self.dataframe)
        else:
            idx = self.tree.index(selection[0])
        self.dataframe.loc[idx + 0.5] = None
        self.dataframe = self.dataframe.sort_index().reset_index(drop=True)
        self.populate_tree()

    def delete_row(self):
        selection = self.tree.selection()
        if not selection:
            return
        for item in selection:
            idx = self.tree.index(item)
            self.dataframe = self.dataframe.drop(idx).reset_index(drop=True)
        self.populate_tree()

    def format_cell(self, format_type):
        """Aplicar formatação às células selecionadas"""
        selection = self.tree.selection()
        if not selection:
            return

        for item in selection:
            current_tags = list(self.tree.item(item)["tags"] or ())
            
            if format_type == "bold":
                if "bold" in current_tags:
                    current_tags.remove("bold")
                else:
                    current_tags.append("bold")
                    
            elif format_type == "italic":
                if "italic" in current_tags:
                    current_tags.remove("italic")
                else:
                    current_tags.append("italic")
                    
            elif format_type == "underline":
                if "underline" in current_tags:
                    current_tags.remove("underline")
                else:
                    current_tags.append("underline")
                    
            self.tree.item(item, tags=current_tags)
            
        # Configurar estilos
        self.tree.tag_configure("bold", font=("TkDefaultFont", 10, "bold"))
        self.tree.tag_configure("italic", font=("TkDefaultFont", 10, "italic"))
        self.tree.tag_configure("underline", font=("TkDefaultFont", 10, "underline"))

    def align_cell(self, alignment):
        """Alinhar conteúdo das células selecionadas"""
        selection = self.tree.selection()
        if not selection:
            return

        for item in selection:
            current_tags = list(self.tree.item(item)["tags"] or ())
            
            # Remover alinhamentos anteriores
            for align in ["left", "center", "right"]:
                if align in current_tags:
                    current_tags.remove(align)
                    
            current_tags.append(alignment)
            self.tree.item(item, tags=current_tags)
            
        # Configurar estilos
        self.tree.tag_configure("left", anchor="w")
        self.tree.tag_configure("center", anchor="center")
        self.tree.tag_configure("right", anchor="e")

    def apply_formula(self, event):
        """Aplicar fórmula às células selecionadas"""
        if not self.tree or not self.dataframe.size:
            return
            
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione as células para aplicar a fórmula")
            return
            
        formula = self.formula_var.get()
        if formula == "Selecione uma fórmula":
            return
            
        try:
            values = []
            for item in selection:
                row_values = self.tree.item(item)["values"]
                for value in row_values:
                    try:
                        values.append(float(value))
                    except (ValueError, TypeError):
                        continue
            
            if not values:
                messagebox.showwarning("Aviso", "Nenhum valor numérico encontrado nas células selecionadas")
                return
                
            if formula == "SOMA":
                result = sum(values)
            elif formula == "MÉDIA":
                result = sum(values) / len(values)
            elif formula == "MÁXIMO":
                result = max(values)
            elif formula == "MÍNIMO":
                result = min(values)
            elif formula == "CONTAGEM":
                result = len(values)
            elif formula == "MEDIANA":
                result = sorted(values)[len(values)//2]
                
            messagebox.showinfo("Resultado", f"O resultado da {formula} é: {result:.2f}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao calcular fórmula: {str(e)}")

    def open_file(self):
        # Aceita Excel (.xlsx, .xls) e CSV
        filetypes = [("Arquivos Excel", "*.xlsx;*.xls"), ("Arquivos CSV", "*.csv"), ("Todos os arquivos", "*.*")]
        self.filename = filedialog.askopenfilename(filetypes=filetypes)
        if not self.filename:
            return
        ext = os.path.splitext(self.filename)[1].lower()
        try:
            if ext in [".xlsx", ".xls"]:
                self.dataframe = pd.read_excel(self.filename)
            elif ext == ".csv":
                self.dataframe = pd.read_csv(self.filename)
            else:
                messagebox.showerror("Erro", "Formato não suportado!")
                return
            self.populate_tree()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def populate_tree(self, sheet_name=None):
        if sheet_name:
            self.dataframe = self.sheets[sheet_name]
        
        # Se já existir uma tabela, destrói-a para criar uma nova
        if self.tree:
            self.tree.destroy()

        # Criar nova Treeview com scrollbars
        self.tree = ttk.Treeview(self.tree_frame, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Configurar scrollbars
        self.tree.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        self.v_scrollbar.configure(command=self.tree.yview)
        self.h_scrollbar.configure(command=self.tree.xview)

        if self.dataframe is None or self.dataframe.empty:
            # Criar DataFrame vazio com algumas colunas padrão
            self.dataframe = pd.DataFrame(columns=[f"Coluna{i+1}" for i in range(5)])
            self.sheets[sheet_name] = self.dataframe

        # Configurar colunas
        self.tree["columns"] = list(self.dataframe.columns)
        for col in self.dataframe.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=100, minwidth=50)

        # Inserir dados
        for index, row in self.dataframe.iterrows():
            self.tree.insert("", "end", values=list(row))

        # Configurar eventos
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Menu de contexto
        self.tree.bind("<Control-c>", lambda e: self.copy())
        self.tree.bind("<Control-v>", lambda e: self.paste())
        self.tree.bind("<Control-x>", lambda e: self.cut())
        self.tree.bind("<<TreeviewSelect>>", self.update_formula_bar)

        # Atualizar barra de status
        self.status_bar.config(text=f"Planilha: {sheet_name or 'Sem nome'}")

    def sort_by_column(self, col):
        """Ordenar dados ao clicar no cabeçalho da coluna"""
        try:
            # Alternar entre ordem crescente e decrescente
            if hasattr(self, '_last_sort') and self._last_sort == (col, True):
                self.dataframe.sort_values(by=col, ascending=False, inplace=True)
                self._last_sort = (col, False)
            else:
                self.dataframe.sort_values(by=col, ascending=True, inplace=True)
                self._last_sort = (col, True)
            
            self.populate_tree(self.current_sheet)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ordenar: {str(e)}")

    def show_context_menu(self, event):
        """Mostrar menu de contexto ao clicar com botão direito"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Copiar", command=self.copy)
        context_menu.add_command(label="Colar", command=self.paste)
        context_menu.add_command(label="Recortar", command=self.cut)
        context_menu.add_separator()
        context_menu.add_command(label="Inserir Linha", command=self.insert_row)
        context_menu.add_command(label="Excluir Linha", command=self.delete_row)
        context_menu.add_separator()
        
        # Submenu de formatação
        format_menu = tk.Menu(context_menu, tearoff=0)
        format_menu.add_command(label="Cor do Texto", command=self.choose_text_color)
        format_menu.add_command(label="Cor do Fundo", command=self.choose_background_color)
        format_menu.add_separator()
        format_menu.add_command(label="Negrito", command=lambda: self.format_cell("bold"))
        format_menu.add_command(label="Itálico", command=lambda: self.format_cell("italic"))
        context_menu.add_cascade(label="Formatar", menu=format_menu)
        
        context_menu.tk_popup(event.x_root, event.y_root)

    def update_formula_bar(self, event=None):
        """Atualizar barra de fórmulas quando uma célula é selecionada"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
            if column:
                col_num = int(column.replace("#", ""))
                row_num = self.tree.index(item) + 1
                col_letter = chr(64 + col_num)  # Converter número para letra (A, B, C, ...)
                self.cell_ref_label.config(text=f"{col_letter}{row_num}")
                
                # Atualizar conteúdo da barra de fórmulas
                value = self.tree.item(item)["values"][col_num - 1]
                self.formula_entry.delete(0, tk.END)
                self.formula_entry.insert(0, str(value))

    def save_file(self):
        if self.dataframe is None:
            messagebox.showerror("Erro", "Nenhum arquivo aberto!")
            return
        # Seleciona o formato de salvamento (Excel ou CSV)
        save_filename = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                     filetypes=[("Arquivos Excel", "*.xlsx"),
                                                                ("Arquivos CSV", "*.csv")])
        if not save_filename:
            return
        ext = os.path.splitext(save_filename)[1].lower()
        try:
            if ext == ".csv":
                self.dataframe.to_csv(save_filename, index=False)
            else:
                self.dataframe.to_excel(save_filename, index=False)
            messagebox.showinfo("Sucesso", f"Arquivo salvo como {save_filename}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def undo(self):
        if self.undo_stack:
            action = self.undo_stack.pop()
            self.redo_stack.append(action)
            # Implementar a lógica de desfazer
            self.status_bar.config(text="Ação desfeita")

    def redo(self):
        if self.redo_stack:
            action = self.redo_stack.pop()
            self.undo_stack.append(action)
            # Implementar a lógica de refazer
            self.status_bar.config(text="Ação refeita")

    def zoom_in(self):
        current_height = int(self.style.lookup("Treeview", "rowheight"))
        self.style.configure("Treeview", rowheight=current_height + 5)

    def zoom_out(self):
        current_height = int(self.style.lookup("Treeview", "rowheight"))
        if current_height > 15:
            self.style.configure("Treeview", rowheight=current_height - 5)

    def freeze_panes(self):
        if not self.tree:
            return
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione uma célula para congelar os painéis")
            return
        # Implementar lógica de congelamento de painéis
        self.status_bar.config(text="Painéis congelados")

    def sort_data(self, order="asc"):
        if not self.tree:
            return
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Aviso", "Selecione uma coluna para ordenar")
            return
        
        column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
        col_num = int(column.replace("#", "")) - 1
        col_name = self.dataframe.columns[col_num]
        
        try:
            if order == "asc":
                self.dataframe.sort_values(by=col_name, inplace=True)
            else:
                self.dataframe.sort_values(by=col_name, ascending=False, inplace=True)
            self.populate_tree(self.current_sheet)
            self.status_bar.config(text=f"Dados ordenados por {col_name}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def toggle_filters(self):
        if not self.tree:
            return
        # Implementar lógica de filtros
        self.status_bar.config(text="Filtros aplicados")

    def create_chart(self):
        if not self.tree or not self.dataframe.size:
            messagebox.showinfo("Aviso", "Não há dados para criar um gráfico")
            return

        chart_window = tk.Toplevel(self.root)
        chart_window.title("Criar Gráfico")
        chart_window.geometry("800x600")

        # Frame para opções do gráfico
        options_frame = ttk.LabelFrame(chart_window, text="Opções do Gráfico")
        options_frame.pack(fill=tk.X, padx=5, pady=5)

        # Tipo de gráfico
        ttk.Label(options_frame, text="Tipo:").pack(side=tk.LEFT, padx=5)
        chart_type = ttk.Combobox(options_frame, values=["Linha", "Barra", "Pizza", "Dispersão"])
        chart_type.pack(side=tk.LEFT, padx=5)
        chart_type.set("Linha")

        # Seleção de dados
        data_frame = ttk.LabelFrame(chart_window, text="Seleção de Dados")
        data_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(data_frame, text="Eixo X:").pack(side=tk.LEFT, padx=5)
        x_axis = ttk.Combobox(data_frame, values=list(self.dataframe.columns))
        x_axis.pack(side=tk.LEFT, padx=5)

        ttk.Label(data_frame, text="Eixo Y:").pack(side=tk.LEFT, padx=5)
        y_axis = ttk.Combobox(data_frame, values=list(self.dataframe.columns))
        y_axis.pack(side=tk.LEFT, padx=5)

        def plot_chart():
            try:
                x = self.dataframe[x_axis.get()]
                y = self.dataframe[y_axis.get()]
                
                fig, ax = plt.subplots(figsize=(8, 6))
                
                if chart_type.get() == "Linha":
                    ax.plot(x, y)
                elif chart_type.get() == "Barra":
                    ax.bar(x, y)
                elif chart_type.get() == "Pizza":
                    ax.pie(y, labels=x, autopct='%1.1f%%')
                elif chart_type.get() == "Dispersão":
                    ax.scatter(x, y)
                
                ax.set_xlabel(x_axis.get())
                ax.set_ylabel(y_axis.get())
                ax.set_title(f"Gráfico de {chart_type.get()}")
                
                canvas = FigureCanvasTkAgg(fig, master=chart_window)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        ttk.Button(data_frame, text="Criar Gráfico", command=plot_chart).pack(side=tk.LEFT, padx=5)

    def choose_text_color(self):
        color = colorchooser.askcolor(title="Escolha a cor do texto")
        if color[1]:
            selection = self.tree.selection()
            if selection:
                for item in selection:
                    self.tree.tag_configure(f"text_color_{item}", foreground=color[1])
                    self.tree.item(item, tags=(f"text_color_{item}",))

    def choose_background_color(self):
        color = colorchooser.askcolor(title="Escolha a cor do fundo")
        if color[1]:
            selection = self.tree.selection()
            if selection:
                for item in selection:
                    self.tree.tag_configure(f"bg_color_{item}", background=color[1])
                    self.tree.item(item, tags=(f"bg_color_{item}",))

    def search_in_cells(self, text):
        if not text or not self.tree:
            return
        
        self.tree.selection_remove(*self.tree.selection())
        found = False
        
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            for value in values:
                if str(text).lower() in str(value).lower():
                    self.tree.selection_add(item)
                    self.tree.see(item)
                    found = True
        
        if not found:
            messagebox.showinfo("Busca", "Texto não encontrado")

    def replace_in_cells(self, search_text, replace_text):
        if not search_text or not self.tree:
            return
            
        count = 0
        for item in self.tree.get_children():
            values = list(self.tree.item(item)["values"])
            for i, value in enumerate(values):
                if str(search_text).lower() in str(value).lower():
                    values[i] = str(value).replace(str(search_text), str(replace_text))
                    count += 1
            self.tree.item(item, values=values)
            
        if count > 0:
            messagebox.showinfo("Substituir", f"{count} ocorrências substituídas")
        else:
            messagebox.showinfo("Substituir", "Nenhuma ocorrência encontrada")

    def apply_formula_from_bar(self, event):
        if not self.tree:
            return
        formula = self.formula_entry.get()
        try:
            # Implementar parser de fórmulas
            result = eval(formula)  # Simplificado para exemplo
            selection = self.tree.selection()
            if selection:
                self.tree.set(selection[0], "#1", result)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na fórmula: {str(e)}")

    def on_double_click(self, event):
        """Manipular edição de célula com duplo clique"""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)
        if not row or not column:
            return
            
        # Obter coordenadas e dimensões da célula
        x, y, width, height = self.tree.bbox(row, column)
        
        # Obter valor atual
        item = self.tree.item(row)
        col_index = int(column.replace("#", "")) - 1
        current_value = item["values"][col_index]
        
        # Criar widget de entrada
        entry = ttk.Entry(self.tree)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.select_range(0, tk.END)
        entry.focus()

        def on_enter(event=None):
            new_value = entry.get()
            
            # Salvar estado atual para desfazer
            old_value = self.tree.item(row)["values"]
            self.undo_stack.append({
                "type": "edit_cell",
                "row": row,
                "column": column,
                "old_value": old_value,
                "new_value": list(old_value)
            })
            
            # Atualizar valor
            self.tree.set(row, column, new_value)
            
            # Atualizar DataFrame
            row_index = self.tree.index(row)
            col_name = self.dataframe.columns[col_index]
            self.dataframe.at[row_index, col_name] = new_value
            
            # Atualizar barra de fórmulas
            self.formula_entry.delete(0, tk.END)
            self.formula_entry.insert(0, new_value)
            
            entry.destroy()
            
            # Atualizar barra de status
            self.status_bar.config(text=f"Célula {chr(64 + col_index + 1)}{row_index + 1} editada")

        def on_escape(event=None):
            entry.destroy()

        entry.bind("<Return>", on_enter)
        entry.bind("<Escape>", on_escape)
        entry.bind("<FocusOut>", on_enter)


if __name__ == "__main__":
    root = tk.Tk()
    app = MiniExcel(root)
    root.mainloop()
