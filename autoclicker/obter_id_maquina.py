"""
Rode este script na maquina de quem vai RECEBER a licenca (amigo/aluno)
e envie o ID impresso para quem vai gerar a licenca (gerar_licenca.py).
"""
from licenca import obter_id_maquina

if __name__ == "__main__":
    print("ID desta maquina (envie para quem vai gerar sua licenca):")
    print(obter_id_maquina())
    input("\nPressione ENTER para fechar...")
