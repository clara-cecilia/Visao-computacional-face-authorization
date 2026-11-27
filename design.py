
from pathlib import Path
from datetime import datetime
from time import monotonic
import tempfile
import shutil

import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parent
FUNDO_IMAGEM = BASE / "assets" / "images" / "fundo_catracas.png"
MODELO_ROSTO = BASE / "modelos" / "haarcascade_frontalface_default.xml"
VERDE = "#32FF80"


def cobrir(imagem, largura, altura):
    largura = max(1, int(largura))
    altura = max(1, int(altura))
    escala = max(
        largura / imagem.width,
        altura / imagem.height
    )
    w = max(1, round(imagem.width * escala))
    h = max(1, round(imagem.height * escala))
    redimensionada = imagem.resize(
        (w, h),
        Image.Resampling.LANCZOS
    )
    esquerda = (w - largura) // 2
    cima = (h - altura) // 2
    return redimensionada.crop(
        (
            esquerda,
            cima,
            esquerda + largura,
            cima + altura
        )
    )


def fonte(tamanho, negrito=False):
    if negrito:
        nomes = ["arialbd.ttf", "DejaVuSans-Bold.ttf"]
    else:
        nomes = ["arial.ttf", "DejaVuSans.ttf"]

    for nome in nomes:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            pass

    return ImageFont.load_default()


class TerminalAcesso(ctk.CTkFrame):

    def __init__(self, master, reconhecer=None):
        super().__init__(
            master,
            fg_color="#000000",
            corner_radius=0
        )

        self.reconhecer = reconhecer
        self.ativo = True
        self.camera = None
        self.detector = None
        self.segmentador = None
        self.imagem_camera = None

        self._temp_detector = None
        self._id_camera = None
        self._id_relogio = None

        self._ultimo_rosto = None
        self._quadros = 0

        self._scanner = 0.22
        self._direcao = 1

        self.nome_identificado = None
        self.resultado_acesso = None
        self._inicio_identificacao = None
        self._chave_identificacao = None
        self._mensagem_erro = None

        if not FUNDO_IMAGEM.is_file():
            raise FileNotFoundError(
                f"Imagem das catracas nao encontrada: {FUNDO_IMAGEM}"
            )

        self.fundo_original = Image.open(
            FUNDO_IMAGEM
        ).convert("RGB")

        w, h = self.fundo_original.size
        self.fundo_original = self.fundo_original.crop(
            (0, int(h * 0.20), w, h)
        )

        # LENTE SUPERIOR
        barra = ctk.CTkFrame(
            self,
            height=18,
            fg_color="#000000",
            corner_radius=0
        )
        barra.pack(fill="x")
        barra.pack_propagate(False)

        ctk.CTkFrame(
            barra,
            width=10,
            height=10,
            corner_radius=5,
            fg_color="#182832",
            border_width=1,
            border_color="#52646B"
        ).place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        # CABECALHO
        topo = ctk.CTkFrame(
            self,
            height=130,
            fg_color="#000000",
            corner_radius=0
        )
        topo.pack(fill="x")
        topo.pack_propagate(False)

        # LOGO
        logo = Image.new(
            "RGBA",
            (90, 90),
            (0, 0, 0, 0)
        )
        d = ImageDraw.Draw(logo)
        branco = (245, 248, 250, 255)

        d.line(
            [(5, 82), (85, 82)],
            fill=branco,
            width=4
        )
        d.line(
            [(14, 80), (14, 29), (49, 16), (49, 80)],
            fill=branco,
            width=4
        )
        d.line(
            [(49, 80), (49, 39), (76, 46), (76, 80)],
            fill=branco,
            width=4
        )

        for x in (24, 38):
            for y in (38, 53, 68):
                d.rectangle(
                    (x, y, x + 4, y + 6),
                    fill=branco
                )

        for x in (58, 69):
            for y in (55, 69):
                d.rectangle(
                    (x, y, x + 4, y + 5),
                    fill=branco
                )

        self.logo = ctk.CTkImage(
            light_image=logo,
            dark_image=logo,
            size=(58, 58)
        )

        ctk.CTkLabel(
            topo,
            image=self.logo,
            text=""
        ).place(
            x=12,
            rely=0.5,
            anchor="w"
        )

        # PRIMEIRA LINHA DIVISORIA
        ctk.CTkFrame(
            topo,
            width=2,
            height=65,
            fg_color="#E8EDF0",
            corner_radius=0
        ).place(
            x=81,
            rely=0.5,
            anchor="center"
        )

        ctk.CTkLabel(
            topo,
            text="FaceAccess",
            text_color="white",
            font=("Arial", 31, "bold")
        ).place(
            x=100,
            rely=0.40,
            anchor="w"
        )

        ctk.CTkLabel(
            topo,
            text="Controle de Acesso",
            text_color="#F0F2F4",
            font=("Arial", 15)
        ).place(
            x=101,
            rely=0.69,
            anchor="w"
        )

        # SEGUNDA LINHA DIVISORIA
        ctk.CTkFrame(
            topo,
            width=2,
            height=65,
            fg_color="#E8EDF0",
            corner_radius=0
        ).place(
            relx=0.665,
            rely=0.5,
            anchor="center"
        )

        self.data = ctk.CTkLabel(
            topo,
            text="",
            font=("Arial", 12),
            text_color="white"
        )
        self.data.place(
            relx=0.975,
            rely=0.36,
            anchor="e"
        )

        self.relogio = ctk.CTkLabel(
            topo,
            text="",
            font=("Arial", 30, "bold"),
            text_color="white"
        )
        self.relogio.place(
            relx=0.975,
            rely=0.66,
            anchor="e"
        )

        # AREA DA CAMERA
        self.area_camera = ctk.CTkFrame(
            self,
            fg_color="#000000",
            corner_radius=0
        )
        self.area_camera.pack(
            fill="both",
            expand=True
        )

        self.video = ctk.CTkLabel(
            self.area_camera,
            text="Preparando camera...",
            fg_color="#000000",
            text_color="#D1D5DB"
        )
        self.video.place(
            relx=0,
            rely=0,
            relwidth=1,
            relheight=1
        )

        self.atualizar_relogio()

        self.after(
            200,
            self.iniciar_dispositivos
        )
        self.after(
            100,
            self.configurar_tecla_q
        )

    # FECHAR COM Q OU X
    def configurar_tecla_q(self):
        if not self.ativo:
            return

        janela = self.winfo_toplevel()

        janela.bind(
            "<KeyPress-q>",
            self.fechar_pela_tecla
        )
        janela.bind(
            "<KeyPress-Q>",
            self.fechar_pela_tecla
        )
        janela.protocol(
            "WM_DELETE_WINDOW",
            self.fechar_janela
        )

        try:
            janela.focus_force()
        except Exception:
            pass

    def fechar_pela_tecla(self, evento=None):
        self.fechar_janela()

    def fechar_janela(self):
        self.encerrar()
        self.winfo_toplevel().destroy()

    # RELOGIO E DATA
    def atualizar_relogio(self):
        if not self.ativo:
            return

        agora = datetime.now()

        dias = [
            "Seg", "Ter", "Qua",
            "Qui", "Sex", "Sab", "Dom"
        ]

        self.data.configure(
            text=f"{dias[agora.weekday()]}, {agora:%d/%m/%Y}"
        )

        self.relogio.configure(
            text=agora.strftime("%H:%M:%S")
        )

        self._id_relogio = self.after(
            1000,
            self.atualizar_relogio
        )

    # INICIAR DISPOSITIVOS
    def iniciar_dispositivos(self):
        if not self.ativo:
            return

        try:
            if self.reconhecer is None:
                self.iniciar_detector()
            self.iniciar_segmentacao()
            self.iniciar_camera()

        except Exception as erro:
            self._mensagem_erro = str(erro)
            print("Erro ao iniciar dispositivos:", erro)

            if self.ativo:
                self.video.configure(
                    text=(
                        "Nao foi possivel iniciar a camera.\n"
                        "Veja o terminal do VS Code."
                    )
                )

    # DETECTOR FACIAL
    def iniciar_detector(self):
        if not MODELO_ROSTO.is_file():
            print(
                "Detector facial nao encontrado:",
                MODELO_ROSTO
            )
            return

        self._temp_detector = tempfile.TemporaryDirectory(
            prefix="faceaccess_detector_"
        )

        destino = Path(self._temp_detector.name) / "rosto.xml"

        shutil.copy2(
            MODELO_ROSTO,
            destino
        )

        detector = cv2.CascadeClassifier(str(destino))

        if detector.empty():
            print("Nao foi possivel carregar o detector facial.")
            return

        self.detector = detector
        print("Detector facial carregado!")

    # REMOCAO DE FUNDO
    def iniciar_segmentacao(self):
        try:
            import mediapipe as mp

            self.segmentador = (
                mp.solutions.selfie_segmentation
                .SelfieSegmentation(model_selection=1)
            )

            print("Remocao de fundo ativada!")

        except Exception as erro:
            self.segmentador = None
            print("Remocao de fundo indisponivel:", erro)

    # ABRIR WEBCAM
    def iniciar_camera(self):
        self.camera = cv2.VideoCapture(
            0,
            cv2.CAP_DSHOW
        )

        if not self.camera.isOpened():
            self.camera.release()
            self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            raise RuntimeError(
                "A webcam nao abriu. "
                "Feche outros aplicativos que estejam usando a camera."
            )

        self.camera.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640
        )
        self.camera.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480
        )

        print("Webcam iniciada!")
        self.atualizar_camera()

    def mensagem_acesso(self, detectado, agora=None):
        """Controla somente a apresentação visual da identificação."""
        neutro = (255, 255, 255, 255)
        agora = monotonic() if agora is None else agora

        if not detectado:
            self._inicio_identificacao = None
            self._chave_identificacao = None
            return "Aproxime seu rosto", "Posicione-se diante da câmera", neutro

        if self.reconhecer is None:
            return "Rosto localizado", "Aguardando identificação", neutro

        chave = (self.resultado_acesso, self.nome_identificado)
        if self._inicio_identificacao is None or chave != self._chave_identificacao:
            self._inicio_identificacao = agora
            self._chave_identificacao = chave

        decorrido = agora - self._inicio_identificacao
        if decorrido < 1:
            return "Rosto localizado", "Mantenha-se imóvel", neutro
        if decorrido < 3 or self.resultado_acesso is None:
            return "Identificando...", "Aguarde a verificação facial", neutro

        # O resultado permanece visível enquanto o mesmo rosto está presente.
        if self.resultado_acesso is True and self.nome_identificado:
            return f"Bem-vindo(a), {self.nome_identificado}!", "Acesso liberado", (50, 255, 128, 255)
        return "Pessoa não reconhecida", "Acesso negado", (255, 100, 100, 255)

    # ATUALIZAR CAMERA
    def atualizar_camera(self):
        if not self.ativo or self.camera is None:
            return

        try:
            sucesso, frame = self.camera.read()

            if not sucesso:
                raise RuntimeError(
                    "A webcam nao retornou imagem."
                )

            frame = cv2.flip(frame, 1)

            largura = max(
                200,
                self.area_camera.winfo_width()
            )
            altura = max(
                260,
                self.area_camera.winfo_height()
            )

            self._quadros += 1

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            pessoa = cobrir(
                Image.fromarray(rgb),
                largura,
                altura
            )
            pessoa_np = np.array(pessoa)

            fundo = np.array(
                cobrir(
                    self.fundo_original,
                    largura,
                    altura
                )
            )

            # PESSOA SOBRE AS CATRACAS
            if self.segmentador is not None:
                resultado = self.segmentador.process(rgb)
                mascara = resultado.segmentation_mask

                if mascara is not None:
                    mascara_img = Image.fromarray(
                        np.uint8(
                            np.clip(mascara, 0, 1) * 255
                        )
                    )

                    mascara_img = cobrir(
                        mascara_img,
                        largura,
                        altura
                    )

                    alfa = (
                        np.asarray(
                            mascara_img,
                            dtype=np.float32
                        ) / 255.0
                    )

                    alfa = cv2.GaussianBlur(
                        alfa,
                        (7, 7),
                        0
                    )

                    alfa = np.clip(
                        (alfa - 0.25) / 0.55,
                        0,
                        1
                    )[:, :, None]

                    fundo = np.uint8(
                        pessoa_np * alfa
                        + fundo * (1 - alfa)
                    )

                else:
                    fundo = pessoa_np

            else:
                fundo = pessoa_np

            # DETECCAO FACIAL
            rostos = []

            if self.reconhecer is not None:
                # O reconhecimento recebe o frame original, sem efeitos visuais.
                if self._quadros == 1 or self._quadros % 3 == 0:
                    self._ultimo_rosto, self.nome_identificado, self.resultado_acesso = self.reconhecer(frame)
                if self._ultimo_rosto is not None:
                    rostos = [self._ultimo_rosto]
            else:
                if (
                    self.detector is not None
                    and self._quadros % 3 == 0
                ):
                    cinza = cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2GRAY
                    )

                    rostos = self.detector.detectMultiScale(
                        cinza,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(60, 60)
                    )

                    if len(rostos):
                        self._ultimo_rosto = max(
                            rostos,
                            key=lambda r: r[2] * r[3]
                        )
                    else:
                        self._ultimo_rosto = None

                elif self._ultimo_rosto is not None:
                    rostos = [self._ultimo_rosto]

            imagem = Image.fromarray(fundo)
            desenho = ImageDraw.Draw(
                imagem,
                "RGBA"
            )

            # LINHA VERDE ANIMADA
            self._scanner += (
                0.013 * self._direcao
            )

            if self._scanner >= 0.78:
                self._scanner = 0.78
                self._direcao = -1

            elif self._scanner <= 0.18:
                self._scanner = 0.18
                self._direcao = 1

            sy = int(
                altura * self._scanner
            )

            desenho.line(
                [
                    (20, sy),
                    (largura - 20, sy)
                ],
                fill=(50, 255, 128, 185),
                width=2
            )

            # CANTOS VERDES DO ROSTO
            detectado = len(rostos) > 0

            if detectado:
                x, y, rw, rh = [
                    int(v) for v in rostos[0]
                ]

                origem_h, origem_w = rgb.shape[:2]

                escala = max(
                    largura / origem_w,
                    altura / origem_h
                )

                desloc_x = (
                    origem_w * escala - largura
                ) / 2

                desloc_y = (
                    origem_h * escala - altura
                ) / 2

                x1 = int(
                    x * escala - desloc_x
                )
                y1 = int(
                    y * escala - desloc_y
                )
                x2 = int(
                    (x + rw) * escala - desloc_x
                )
                y2 = int(
                    (y + rh) * escala - desloc_y
                )

                x1 = max(0, x1)
                x2 = min(largura - 1, x2)
                y1 = max(0, y1)
                y2 = min(altura - 1, y2)

                if x2 > x1 and y2 > y1:
                    canto = min(
                        18,
                        (x2 - x1) // 4,
                        (y2 - y1) // 4
                    )

                    pontos = (
                        (x1, y1, 1, 1),
                        (x2, y1, -1, 1),
                        (x1, y2, 1, -1),
                        (x2, y2, -1, -1)
                    )

                    for px, py, dx, dy in pontos:
                        desenho.line(
                            [
                                (px, py + dy * canto),
                                (px, py),
                                (px + dx * canto, py)
                            ],
                            fill=(50, 255, 128, 255),
                            width=4
                        )

            titulo, subtitulo, cor_status = self.mensagem_acesso(detectado)
            cor_borda = (230, 236, 240, 160) if cor_status == (255, 255, 255, 255) else cor_status

            # CAIXA TRANSPARENTE
            margem = max(
                12,
                int(largura * 0.055)
            )

            caixa_h = 80
            esquerda = margem
            direita = largura - margem
            baixo = altura - 60
            cima = baixo - caixa_h

            desenho.rounded_rectangle(
                (
                    esquerda,
                    cima,
                    direita,
                    baixo
                ),
                radius=19,
                fill=(7, 11, 15, 130),
                outline=cor_borda,
                width=2 if cor_borda == cor_status else 1
            )

            # ICONE DE PESSOA
            desenho.ellipse(
                (
                    esquerda + 17,
                    cima + 17,
                    esquerda + 31,
                    cima + 31
                ),
                outline=(245, 248, 250, 255),
                width=2
            )

            desenho.arc(
                (
                    esquerda + 12,
                    cima + 27,
                    esquerda + 36,
                    cima + 50
                ),
                185,
                355,
                fill=(245, 248, 250, 255),
                width=2
            )

            # DIVISOR DA CAIXA
            desenho.line(
                [
                    (esquerda + 51, cima + 13),
                    (esquerda + 51, baixo - 13)
                ],
                fill=(245, 248, 250, 140),
                width=1
            )

            limite = max(
                10,
                (direita - esquerda - 70) // 11
            )

            if len(subtitulo) > limite:
                subtitulo = (
                    subtitulo[:max(1, limite - 1)]
                    + "..."
                )

            desenho.text(
                (
                    esquerda + 64,
                    cima + 12
                ),
                titulo,
                font=fonte(16, True),
                fill=cor_status
            )

            desenho.text(
                (
                    esquerda + 64,
                    cima + 38
                ),
                subtitulo,
                font=fonte(12),
                fill=(215, 222, 227, 255)
            )

            # EXIBIR IMAGEM
            self.imagem_camera = ctk.CTkImage(
                light_image=imagem,
                dark_image=imagem,
                size=(largura, altura)
            )

            self.video.configure(
                image=self.imagem_camera,
                text=""
            )

        except Exception as erro:
            self.nome_identificado = None
            self.resultado_acesso = None
            self._ultimo_rosto = None
            self._inicio_identificacao = None
            self._chave_identificacao = None
            mensagem = str(erro)

            if mensagem != self._mensagem_erro:
                print(
                    "Erro ao atualizar imagem:",
                    erro
                )
                self._mensagem_erro = mensagem

        finally:
            if self.ativo:
                self._id_camera = self.after(
                    45,
                    self.atualizar_camera
                )

    # ENCERRAMENTO
    def encerrar(self):
        if not self.ativo:
            return

        self.ativo = False

        for identificador in (
            self._id_camera,
            self._id_relogio
        ):
            if identificador is not None:
                try:
                    self.after_cancel(identificador)
                except Exception:
                    pass

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        if self.segmentador is not None:
            self.segmentador.close()
            self.segmentador = None

        if self._temp_detector is not None:
            self._temp_detector.cleanup()
            self._temp_detector = None

    def destroy(self):
        self.encerrar()
        super().destroy()
