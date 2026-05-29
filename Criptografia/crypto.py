import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken  # noqa: F401  (re-exportado para uso externo)

ITERACOES = 480_000


def _derivar_chave_aes(senha: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERACOES)
    return kdf.derive(senha.encode())


def _derivar_chave_fernet(senha: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERACOES)
    return base64.urlsafe_b64encode(kdf.derive(senha.encode()))


def criptografar_dados(caminho: str, senha: str) -> tuple[bytes, bytes, bytes]:
    """Lê o arquivo e retorna (salt, iv, ciphertext) prontos para embutir no HTML."""
    salt = os.urandom(16)
    iv = os.urandom(12)
    chave = _derivar_chave_aes(senha, salt)

    with open(caminho, "rb") as f:
        dados = f.read()

    return salt, iv, AESGCM(chave).encrypt(iv, dados, None)


def descriptografar_enc(caminho: str, senha: str) -> str:
    """Descriptografa um arquivo .enc (formato legado Fernet) e salva o original."""
    with open(caminho, "rb") as f:
        conteudo = f.read()

    salt, dados_enc = conteudo[:16], conteudo[16:]
    dados = Fernet(_derivar_chave_fernet(senha, salt)).decrypt(dados_enc)

    destino = caminho.removesuffix(".enc")
    if os.path.exists(destino):
        base, ext = os.path.splitext(destino)
        destino = f"{base}_descriptografado{ext}"

    with open(destino, "wb") as f:
        f.write(dados)

    return destino
