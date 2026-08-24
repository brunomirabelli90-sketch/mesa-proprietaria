"""
Rode este script na SUA maquina (nao precisa ser a maquina de destino)
para gerar um licenca.lic para outra pessoa.

Uso:
    python gerar_licenca.py <id_da_maquina> <AAAA-MM-DD>

O <id_da_maquina> e' o valor que a pessoa te enviou rodando
obter_id_maquina.py. <AAAA-MM-DD> e' ate quando a licenca vale.

NAO compartilhe este script nem licenca.py com quem vai receber a
licenca - envie so o licenca.lic gerado (e o autoclicker, de
preferencia ja compilado em .exe).
"""
import json
import sys

from licenca import gerar_licenca


def main():
    if len(sys.argv) != 3:
        print("Uso: python gerar_licenca.py <id_da_maquina> <AAAA-MM-DD>")
        sys.exit(1)

    maquina_id, expira_em = sys.argv[1], sys.argv[2]
    dados = gerar_licenca(maquina_id, expira_em)

    with open("licenca.lic", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2)

    print(f"licenca.lic gerada para a maquina {maquina_id}, valida ate {expira_em}.")
    print("Envie esse arquivo para a pessoa: ela deve colocar na mesma pasta do autoclicker.")


if __name__ == "__main__":
    main()
