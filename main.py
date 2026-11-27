from pathlib import Path

import cv2
import face_recognition

from abrir_terminal import abrir_terminal


PASTA_ROSTOS = Path(__file__).resolve().parent / "rostos"


def corrigir_nome(nome):
    """Recupera acentos de arquivos antigos gravados com codificação incorreta."""
    if "Ã" not in nome and "Â" not in nome:
        return nome
    try:
        return nome.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return nome


def carregar_rostos():
    """Carrega as fotos cadastradas e suas codificações faciais."""
    PASTA_ROSTOS.mkdir(exist_ok=True)
    rostos_conhecidos = []
    nomes_conhecidos = []

    for arquivo in sorted(PASTA_ROSTOS.iterdir()):
        if arquivo.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        imagem = face_recognition.load_image_file(str(arquivo))
        codificacoes = face_recognition.face_encodings(imagem)
        if len(codificacoes) == 1:
            rostos_conhecidos.append(codificacoes[0])
            nome = corrigir_nome(arquivo.stem)
            nomes_conhecidos.append(nome)
            print(f"Rosto cadastrado: {nome}")
        else:
            print(f"Foto ignorada (esperado um rosto): {arquivo.name}")

    return rostos_conhecidos, nomes_conhecidos


def reconhecer_rosto(frame, rostos_conhecidos, nomes_conhecidos):
    """Retorna a posição do rosto, nome e resultado para o design."""
    pequeno = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(pequeno, cv2.COLOR_BGR2RGB)
    localizacoes = face_recognition.face_locations(rgb)

    # O terminal atende uma pessoa por vez.
    if len(localizacoes) != 1:
        return None, None, None

    topo, direita, baixo, esquerda = localizacoes[0]
    escala_x = frame.shape[1] / pequeno.shape[1]
    escala_y = frame.shape[0] / pequeno.shape[0]
    posicao = (round(esquerda * escala_x), round(topo * escala_y),
               round((direita - esquerda) * escala_x),
               round((baixo - topo) * escala_y))

    codificacoes = face_recognition.face_encodings(rgb, localizacoes)
    if not codificacoes:
        return posicao, None, None
    if not rostos_conhecidos:
        return posicao, None, False

    distancias = face_recognition.face_distance(rostos_conhecidos, codificacoes[0])
    melhor_indice = distancias.argmin()
    if distancias[melhor_indice] <= 0.50:
        return posicao, nomes_conhecidos[melhor_indice], True

    return posicao, None, False


def main():
    rostos, nomes = carregar_rostos()
    abrir_terminal(lambda frame: reconhecer_rosto(frame, rostos, nomes))


if __name__ == "__main__":
    main()
