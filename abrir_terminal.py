
import customtkinter as ctk
from design import TerminalAcesso


def abrir_terminal(reconhecer=None):
    ctk.set_appearance_mode("dark")

    janela = ctk.CTk()
    janela.title("FaceAccess - Terminal Facial")

    # Tamanho do terminal
    LARGURA = 600
    ALTURA = 900

    # Centralizar na tela
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()

    # Ajustar caso a tela seja menor
    LARGURA = min(LARGURA, largura_tela - 80)
    ALTURA = min(ALTURA, altura_tela - 100)

    x = (largura_tela - LARGURA) // 2
    y = (altura_tela - ALTURA) // 2

    janela.geometry(f"{LARGURA}x{ALTURA}+{x}+{y}")
    janela.resizable(False, False)

    terminal = TerminalAcesso(janela, reconhecer=reconhecer)
    terminal.pack(fill="both", expand=True)


    def fechar(event=None):
        terminal.encerrar()
        janela.destroy()


    # Fechar pelo X, Q ou ESC
    janela.protocol("WM_DELETE_WINDOW", fechar)
    janela.bind_all("<KeyPress-q>", fechar)
    janela.bind_all("<KeyPress-Q>", fechar)
    janela.bind_all("<Escape>", fechar)

    janela.mainloop()


if __name__ == "__main__":
    abrir_terminal()
