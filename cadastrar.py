
import cv2
import os
from pathlib import Path
"""
O programa vai:
1. Solicitar o nome da pessoa.
2. Abrir a webcam.
3. Aguardar você pressionar ESPAÇO.
4. Salvar a fotografia na pasta rostos.
"""
# Criar pasta caso não exista
PASTA_ROSTOS = "rostos"
os.makedirs(PASTA_ROSTOS, exist_ok=True)

# Solicitar nome
nome = input("Digite o nome da pessoa: ").strip()

if not nome:
    print("Nome inválido!")
    exit()

# Abrir webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Não foi possível acessar a webcam.")
    exit()

print("Posicione o rosto na câmera.")
print("Pressione ESPAÇO para capturar a foto.")
print("Pressione Q para cancelar.")

while True:
    sucesso, frame = camera.read()

    if not sucesso:
        print("Erro ao capturar imagem.")
        break

    cv2.imshow("Cadastro Facial", frame)

    tecla = cv2.waitKey(1) & 0xFF

    # Capturar imagem
    if tecla in (ord("a"), ord(" ")):
        caminho = os.path.join(
            PASTA_ROSTOS,
            nome + ".jpg"
        )

        if os.path.exists(caminho):
            print("Já existe uma pessoa cadastrada com esse nome.")
            continue

        sucesso, dados = cv2.imencode(".jpg", frame)
        if not sucesso:
            print("Não foi possível codificar a foto.")
            continue
        Path(caminho).write_bytes(dados.tobytes())
        print(f"Cadastro salvo: {caminho}")
        break

    # Cancelar
    elif tecla == ord("q"):
        print("Cadastro cancelado.")
        break

camera.release()
cv2.destroyAllWindows()
