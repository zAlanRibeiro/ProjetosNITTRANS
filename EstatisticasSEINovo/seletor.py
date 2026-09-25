# -*- coding: utf-8 -*-
"""
Janela que escolhe a competência das Estatísticas SEI.

Em vez de pedir os PDFs um a um, pergunta o ano e o mês e busca os
arquivos na pasta sincronizada — a biblioteca do SharePoint que o fluxo do
Power Automate alimenta e que o cliente do OneDrive espelha como uma pasta
comum do Windows.

A pasta raiz é escolhida uma única vez, no botão "Procurar", e fica
guardada em config.json para as próximas execuções.

Enquanto a biblioteca não estiver sincronizada nesta máquina, o botão
"Escolher os PDFs manualmente" mantém a ferramenta utilizável.
"""

import json
import os
import shutil
import sys
import tempfile
import textwrap
import threading
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

try:
    from EstatisticasSEINovo import estatisticasSEI
    from EstatisticasSEINovo.estatisticasSEI import (
        MESES_NOME, anos_disponiveis, detectar_pasta_sincronizada,
        listar_pdfs, resolver_pasta_competencia)
except ImportError:
    import estatisticasSEI
    from estatisticasSEI import (
        MESES_NOME, anos_disponiveis, detectar_pasta_sincronizada,
        listar_pdfs, resolver_pasta_competencia)

# ── Paleta idêntica ao Hub ────────────────────────────────────────────────
COR_VIDRO_BLENDED = "#0A2548"
_AZUL_SUB = "#A3C2F0"
_LARANJA = "#F97316"
_LAR_HOV = "#EA580C"
_BRANCO = "#FFFFFF"
_SUCESSO = "#4ADE80"
_ERRO = "#F87171"
_FONTE = "Segoe UI"

ARQUIVO_CONFIG = "config.json"


def _pasta_da_ferramenta():
    """
    Pasta EstatisticasSEINovo, tanto rodando pelo .py quanto pelo .exe.
    No empacotado os módulos ficam dentro do bundle, mas as pastas das
    ferramentas ficam ao lado do executável.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "EstatisticasSEINovo"
    return Path(__file__).resolve().parent


def carregar_pasta_raiz():
    """Caminho guardado da biblioteca sincronizada, ou '' na primeira vez."""
    caminho = _pasta_da_ferramenta() / ARQUIVO_CONFIG
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo).get("pasta_raiz", "")
    except (OSError, ValueError):
        return ""


def salvar_config(pasta_raiz, competencia=None):
    """
    Guarda a pasta da biblioteca e a competência desta execução.

    A competência é reescrita toda vez — inclusive vazia, quando os PDFs
    vêm da seleção manual — para a ferramenta nunca rotular a planilha com
    o mês de uma execução anterior. É ela também que diz à ferramenta se
    cabe conferir quais unidades deixaram de entregar.
    """
    caminho = _pasta_da_ferramenta() / ARQUIVO_CONFIG
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            json.dump({"pasta_raiz": str(pasta_raiz),
                       "competencia_escolhida": competencia or ""},
                      arquivo, ensure_ascii=False, indent=2)
    except OSError as erro:
        # Não poder guardar a preferência não impede a consolidação:
        # o usuário só terá de escolher a pasta de novo na próxima vez.
        print(f"Não foi possível guardar a pasta escolhida: {erro}")


def _amostra(pasta, limite=6):
    """Nomes das subpastas, para o aviso de erro dizer algo aproveitável."""
    try:
        nomes = sorted(p.name for p in Path(pasta).iterdir() if p.is_dir())
    except OSError:
        return "não consegui ler o conteúdo"
    if not nomes:
        return "nenhuma subpasta"
    if len(nomes) > limite:
        return ", ".join(nomes[:limite]) + f" (+{len(nomes) - limite})"
    return ", ".join(nomes)


def _preparar_com_unidade(pdfs, pasta_mes):
    """
    Leva o nome da unidade da pasta para o nome do arquivo.

    Os relatórios ficam soltos na pasta do mês, e aí não há o que
    renomear: os caminhos originais são devolvidos sem cópia. Isto existe
    para os meses anteriores a agosto de 2026, organizados com uma
    subpasta por unidade ('2026/Julho/NIT-NITTRANS-PROTOCOLO/') e com o PDF
    de todas chamado igual — 'SEI - Estatísticas da Unidade.pdf'. Como o
    Hub copia tudo achatado para 'entrada', sem isto os arquivos daqueles
    meses ficariam indistinguíveis entre si.
    """
    pasta_mes = Path(pasta_mes)
    caminhos = [Path(p) for p in pdfs]
    if all(c.parent == pasta_mes for c in caminhos):
        return [str(c) for c in caminhos]

    destino = Path(tempfile.mkdtemp(prefix="estatisticas_sei_"))
    preparados = []
    for caminho in caminhos:
        if caminho.parent == pasta_mes:
            nome = caminho.name
        else:
            nome = f"{caminho.stem} - {caminho.parent.name}{caminho.suffix}"
        alvo = destino / nome
        shutil.copy(caminho, alvo)
        preparados.append(str(alvo))
    return preparados


def _competencia_anterior():
    """
    Mês fechado, que é o que se costuma consolidar: em agosto, julho.
    """
    hoje = date.today()
    ano, mes = (hoje.year - 1, 12) if hoje.month == 1 else (hoje.year,
                                                            hoje.month - 1)
    return str(ano), f"{mes:02d}"


class JanelaCompetencia(ctk.CTkToplevel):
    """Pergunta ano e mês e devolve os PDFs encontrados em self.resultado."""

    def __init__(self, mestre):
        super().__init__(mestre)
        self.resultado = None
        self._ano_padrao, self._mes_padrao = _competencia_anterior()

        # Na primeira vez, tenta achar a biblioteca sincronizada sozinha,
        # para o usuário não ter de caçar o caminho no Explorador.
        self._pasta_raiz = carregar_pasta_raiz()
        self._detectada = False
        if not self._pasta_raiz:
            achada = detectar_pasta_sincronizada()
            if achada:
                self._pasta_raiz = str(achada)
                self._detectada = True
                salvar_config(self._pasta_raiz)

        self.title("Estatísticas SEI — escolher competência")
        self.geometry("520x500")
        self.resizable(False, False)
        self.configure(fg_color=COR_VIDRO_BLENDED)
        self.transient(mestre)

        self._montar()
        self._centralizar()
        self.after(50, self._aplicar_icone)

        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancelar)

    # ── Construção da tela ────────────────────────────────────────────────
    def _montar(self):
        ctk.CTkLabel(
            self, text="Consolidar Estatísticas SEI",
            font=(_FONTE, 18, "bold"), text_color=_BRANCO,
        ).pack(pady=(22, 2))
        ctk.CTkLabel(
            self,
            text="Escolha o mês; os PDFs são buscados na pasta sincronizada.",
            font=(_FONTE, 12), text_color=_AZUL_SUB,
        ).pack(pady=(0, 18))

        # Pasta raiz
        moldura_pasta = ctk.CTkFrame(self, fg_color="transparent")
        moldura_pasta.pack(fill="x", padx=24)
        ctk.CTkLabel(moldura_pasta, text="Pasta da biblioteca sincronizada",
                     font=(_FONTE, 12, "bold"), text_color=_BRANCO,
                     anchor="w").pack(fill="x")

        linha_pasta = ctk.CTkFrame(moldura_pasta, fg_color="transparent")
        linha_pasta.pack(fill="x", pady=(4, 0))
        self._campo_pasta = ctk.CTkEntry(
            linha_pasta, font=(_FONTE, 11), height=34,
            placeholder_text="Nenhuma pasta escolhida ainda")
        self._campo_pasta.pack(side="left", fill="x", expand=True)
        self._campo_pasta.insert(0, self._pasta_raiz)
        ctk.CTkButton(
            linha_pasta, text="Procurar", width=90, height=34,
            font=(_FONTE, 12, "bold"), fg_color=_LARANJA,
            hover_color=_LAR_HOV, command=self._procurar_pasta,
        ).pack(side="left", padx=(8, 0))

        # Ano e mês
        linha_data = ctk.CTkFrame(self, fg_color="transparent")
        linha_data.pack(fill="x", padx=24, pady=(18, 0))

        coluna_ano = ctk.CTkFrame(linha_data, fg_color="transparent")
        coluna_ano.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(coluna_ano, text="Ano", font=(_FONTE, 12, "bold"),
                     text_color=_BRANCO, anchor="w").pack(fill="x")
        self._menu_ano = ctk.CTkOptionMenu(
            coluna_ano, values=[self._ano_padrao], height=34,
            font=(_FONTE, 12), fg_color=_LARANJA, button_color=_LAR_HOV,
            button_hover_color=_LAR_HOV, command=lambda _: self._conferir())
        self._menu_ano.pack(fill="x", pady=(4, 0))

        coluna_mes = ctk.CTkFrame(linha_data, fg_color="transparent")
        coluna_mes.pack(side="left", fill="x", expand=True, padx=(12, 0))
        ctk.CTkLabel(coluna_mes, text="Mês", font=(_FONTE, 12, "bold"),
                     text_color=_BRANCO, anchor="w").pack(fill="x")
        self._menu_mes = ctk.CTkOptionMenu(
            coluna_mes,
            values=[f"{n} — {MESES_NOME[n]}" for n in sorted(MESES_NOME)],
            height=34, font=(_FONTE, 12), fg_color=_LARANJA,
            button_color=_LAR_HOV, button_hover_color=_LAR_HOV,
            command=lambda _: self._conferir())
        self._menu_mes.pack(fill="x", pady=(4, 0))
        self._menu_mes.set(
            f"{self._mes_padrao} — {MESES_NOME[self._mes_padrao]}")

        # Ações — empacotadas antes da situação para os botões nunca
        # serem espremidos quando a mensagem ocupar várias linhas.
        acoes = ctk.CTkFrame(self, fg_color="transparent")
        acoes.pack(side="bottom", fill="x", padx=24, pady=20)
        self._botao_ok = ctk.CTkButton(
            acoes, text="Consolidar", height=42, font=(_FONTE, 14, "bold"),
            fg_color=_LARANJA, hover_color=_LAR_HOV, command=self._confirmar)
        self._botao_ok.pack(fill="x")
        ctk.CTkButton(
            acoes, text="Escolher os PDFs manualmente", height=34,
            font=(_FONTE, 12), fg_color="transparent", border_width=1,
            border_color=_AZUL_SUB, text_color=_AZUL_SUB,
            hover_color="#123A5E",
            command=self._escolher_manualmente).pack(fill="x", pady=(8, 0))
        ctk.CTkButton(
            acoes, text="Cancelar", height=30, font=(_FONTE, 12),
            fg_color="transparent", text_color=_AZUL_SUB,
            hover_color="#123A5E", command=self._cancelar).pack(fill="x",
                                                                pady=(4, 0))

        # Situação da busca
        self._rotulo_situacao = ctk.CTkLabel(
            self, text="", font=(_FONTE, 12), text_color=_AZUL_SUB,
            wraplength=470, justify="left", anchor="w")
        self._rotulo_situacao.pack(fill="x", padx=24, pady=(18, 0))

        self._recarregar_anos()

    def _aplicar_icone(self):
        for caminho in ("logo.ico",
                        os.path.join(os.path.dirname(__file__), "..",
                                     "logo.ico"),
                        os.path.join(os.path.dirname(sys.executable),
                                     "_internal", "logo.ico")):
            try:
                if os.path.exists(caminho):
                    self.iconbitmap(caminho)
                    return
            except Exception:
                pass

    def _centralizar(self):
        self.update_idletasks()
        largura, altura = self.winfo_width(), self.winfo_height()
        tela_l, tela_a = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{largura}x{altura}"
                      f"+{(tela_l - largura) // 2}+{(tela_a - altura) // 2}")

    # ── Comportamento ─────────────────────────────────────────────────────
    def _procurar_pasta(self):
        escolhida = filedialog.askdirectory(
            parent=self,
            title="Selecione a pasta raiz das Estatísticas SEI"
                  " (a que contém as pastas de ano)",
            initialdir=self._pasta_raiz or None)
        if not escolhida:
            return
        self._pasta_raiz = escolhida
        self._campo_pasta.delete(0, "end")
        self._campo_pasta.insert(0, escolhida)
        salvar_config(escolhida)
        self._recarregar_anos()

    def _recarregar_anos(self):
        """Lista como anos as pastas que existem de verdade na raiz."""
        anos = anos_disponiveis(self._pasta_raiz) if self._pasta_raiz else []
        if not anos:
            # Sem pasta válida ainda: deixa a lista utilizável mesmo assim.
            atual = date.today().year
            anos = [str(a) for a in range(atual, atual - 5, -1)]
        self._menu_ano.configure(values=anos)
        self._menu_ano.set(self._ano_padrao if self._ano_padrao in anos
                           else anos[0])
        self._conferir()

    def _competencia_escolhida(self):
        return self._menu_ano.get(), self._menu_mes.get()[:2]

    def _pasta_do_mes(self):
        if not self._pasta_raiz:
            return None
        ano, mes = self._competencia_escolhida()
        return resolver_pasta_competencia(self._pasta_raiz, ano, mes)

    def _conferir(self):
        """Diz, antes de rodar, o que foi encontrado para a competência."""
        if not self._pasta_raiz:
            self._situacao(
                "Não encontrei a biblioteca sincronizada nesta máquina."
                " Abra a pasta EstatisticaSEI no SharePoint e clique em"
                " 'Sincronizar' — depois volte aqui. Enquanto isso, dá para"
                " escolher os PDFs manualmente.", _AZUL_SUB)
            return
        if not Path(self._pasta_raiz).is_dir():
            self._situacao("A pasta guardada não existe mais:"
                           f" {self._pasta_raiz}", _ERRO)
            return

        ano, mes = self._competencia_escolhida()
        pasta = self._pasta_do_mes()
        if pasta is None:
            self._situacao(self._diagnostico(ano, mes), _ERRO)
            return

        pdfs = listar_pdfs(pasta)
        if not pdfs:
            self._situacao(f"A pasta {pasta.name} existe, mas não tem"
                           " nenhum PDF.", _ERRO)
            return
        origem = " (biblioteca localizada automaticamente)" if self._detectada else ""
        self._situacao(f"{len(pdfs)} PDF(s) encontrados em"
                       f" {pasta.name} — um por unidade.{origem}", _SUCESSO)

    def _diagnostico(self, ano, mes):
        """
        Diz o que existe na pasta quando a competência não é encontrada.

        Um "não achei" seco não distingue os três motivos possíveis: a raiz
        está errada, a estrutura de pastas é diferente da combinada, ou o
        mês simplesmente ainda não foi gerado. Mostrar o conteúdo resolve
        isso sem precisar abrir o Explorador.
        """
        raiz = Path(self._pasta_raiz)
        pasta_ano = raiz / ano

        if not pasta_ano.is_dir():
            soltos = len(listar_pdfs(raiz))
            extra = (f" Há {soltos} PDF(s) direto na raiz — se for assim que"
                     " os arquivos chegam, me avise que eu ajusto."
                     if soltos else "")
            return (f"Não há pasta '{ano}' em {raiz.name}."
                    f" Lá dentro vejo: {_amostra(raiz)}.{extra}")

        return (f"Não achei o mês {mes} em {raiz.name}\\{ano}."
                f" Lá dentro vejo: {_amostra(pasta_ano)}.")

    def _situacao(self, texto, cor):
        self._rotulo_situacao.configure(text=texto, text_color=cor)

    def _confirmar(self):
        pasta = self._pasta_do_mes()
        pdfs = listar_pdfs(pasta)
        if not pdfs:
            self._conferir()
            return
        try:
            self.resultado = _preparar_com_unidade(pdfs, pasta)
        except OSError as erro:
            self._situacao(f"Não consegui ler os PDFs da pasta: {erro}", _ERRO)
            return
        ano, mes = self._competencia_escolhida()
        salvar_config(self._pasta_raiz, f"{ano}-{mes}")
        self._fechar()

    def _escolher_manualmente(self):
        caminhos = filedialog.askopenfilenames(
            parent=self,
            title="Selecione os PDFs de Estatísticas da Unidade"
                  " (um por unidade)",
            filetypes=[("Arquivos PDF", "*.pdf")])
        if not caminhos:
            return
        # Sem pasta de mês, a competência tem de sair do próprio relatório:
        # limpar a guardada evita rotular com o mês da execução anterior.
        salvar_config(self._pasta_raiz, None)
        self.resultado = list(caminhos)
        self._fechar()

    def _cancelar(self):
        self.resultado = None
        self._fechar()

    def _fechar(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


def _codigo_curto(unidade):
    """'NIT/NITTRANS/PROTOCOLO' -> 'PROTOCOLO', para caber na janela."""
    return unidade.rstrip("/").rsplit("/", 1)[-1]


def _confirmador(mestre):
    """
    Monta a função que pergunta se deve gerar a planilha faltando unidades.

    A consolidação roda numa thread de trabalho, e janela do tkinter só
    pode ser criada na thread principal — daí o after() para agendar a
    pergunta lá e o Event para a thread de trabalho ficar esperando a
    resposta em vez de seguir em frente.
    """
    def perguntar(faltantes, competencia):
        resposta = {}
        respondido = threading.Event()

        def mostrar():
            try:
                nomes = textwrap.fill(
                    ", ".join(_codigo_curto(u) for u in faltantes), 64)
                resposta["seguir"] = messagebox.askokcancel(
                    "Estatísticas SEI — unidades faltando",
                    f"Está faltando o relatório de {len(faltantes)} de"
                    f" {len(estatisticasSEI.UNIDADES_NITTRANS)} unidades"
                    f" em {competencia}:\n\n{nomes}\n\n"
                    "Elas entram na planilha com a quantidade em branco.\n\n"
                    "Gerar a planilha assim mesmo?",
                    icon=messagebox.WARNING, default=messagebox.CANCEL,
                    parent=mestre)
            finally:
                respondido.set()

        mestre.after(0, mostrar)
        respondido.wait()
        return bool(resposta.get("seguir"))

    return perguntar


def escolher_pdfs(mestre):
    """
    Abre a janela e espera. Devolve a lista de PDFs escolhidos, ou None se
    o usuário desistiu.
    """
    janela = JanelaCompetencia(mestre)
    mestre.wait_window(janela)
    if janela.resultado:
        estatisticasSEI.confirmar_faltantes = _confirmador(mestre)
    return janela.resultado
