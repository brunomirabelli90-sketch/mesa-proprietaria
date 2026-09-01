"""
Autoclicker visual multi-conta.

Le um ou mais arquivos de config e registra hotkeys globais. Ao pressionar
uma hotkey de acao (compra/venda/zerar/cancelar_zerar), clica no botao
correspondente de cada conta cadastrada, na ordem em que aparecem no config
ativo.

Uso:
    python autoclicker.py [config1.json] [config2.json ...]

Passar mais de um config permite alternar entre "perfis" (ex: layout
normal vs layout de leilao) em tempo real com a hotkey 'trocar_perfil'
(padrao F10), sem fechar o programa.

Seguranca:
- Comeca DESARMADO. Pressione a hotkey 'armar_desarmar' (padrao F9) para
  armar antes de qualquer acao funcionar.
- modo_simulacao=true no config faz o script so imprimir o que faria,
  sem clicar de verdade. Use isso para validar a calibracao primeiro.
- pyautogui.FAILSAFE fica ligado: jogar o mouse para o canto superior
  esquerdo da tela aborta a acao em andamento.
- verificar_cor=true no config confere se a cor do pixel no ponto
  calibrado ainda bate com a cor capturada na calibracao antes de
  clicar; se mudou demais (layout deslocou), pula aquele clique em vez
  de arriscar clicar no lugar errado.

Cada acao disparada e' registrada com data/hora em historico.log.
"""
import json
import sys
import threading
import time
from datetime import datetime

import keyboard
import pyautogui

from licenca import validar_licenca

try:
    import winsound

    def _beep():
        try:
            winsound.Beep(1000, 120)
        except Exception:
            pass
except ImportError:
    def _beep():
        pass

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

CAMINHO_LOG = "historico.log"

# IMPRIMIR e' indireto (em vez de chamar print direto) pra permitir que uma
# interface grafica redirecione as mensagens pra um widget de log.
IMPRIMIR = print

ARMADO = False
ULTIMO_DISPARO = {}
DEBOUNCE_S = 0.5

PERFIS = []  # lista de (caminho, config)
INDICE_PERFIL = 0

CONTADORES = {
    "compra": 0, "venda": 0, "zerar": 0, "cancelar_zerar": 0,
    "apregoar_compra": 0, "apregoar_venda": 0,
}

# fallback pros hotkeys novos em configs antigos (calibrados antes dessa
# funcionalidade existir, que por isso nao tem essas chaves em "hotkeys").
HOTKEYS_PADRAO_EXTRAS = {"apregoar_compra": "f5", "apregoar_venda": "f6"}

ULTIMA_ATIVIDADE = time.monotonic()

# callback opcional (sem argumentos), chamado uma vez por acao disparada de
# verdade (armado) - usado pela interface grafica pra dar um feedback visual
# alem do beep.
AO_DISPARAR = None


def carregar_config(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_config(caminho, config):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def carregar_perfis(caminhos):
    global PERFIS, INDICE_PERFIL
    PERFIS = [(c, carregar_config(c)) for c in caminhos]
    INDICE_PERFIL = 0


def config_atual():
    return PERFIS[INDICE_PERFIL][1]


def registrar_historico(linha):
    carimbo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(CAMINHO_LOG, "a", encoding="utf-8") as f:
            f.write(f"{carimbo}  {linha}\n")
    except OSError:
        pass


def obter_pos_cor(valor):
    """Aceita tanto o formato antigo (lista [x, y]) quanto o novo
    ({"pos": [x, y], "cor": [r, g, b]}), pra nao quebrar configs velhos."""
    if isinstance(valor, dict):
        return valor.get("pos"), valor.get("cor")
    return valor, None


def cor_bate(pos, cor_esperada, tolerancia):
    if not cor_esperada:
        return True
    try:
        atual = pyautogui.pixel(*pos)
    except Exception:
        return True
    return all(abs(a - b) <= tolerancia for a, b in zip(atual, cor_esperada))


def pode_disparar(acao):
    agora = time.monotonic()
    ultimo = ULTIMO_DISPARO.get(acao, 0)
    if agora - ultimo < DEBOUNCE_S:
        return False
    ULTIMO_DISPARO[acao] = agora
    return True


def executar_acao(acao):
    global ARMADO, ULTIMA_ATIVIDADE

    if not pode_disparar(acao):
        return

    config = config_atual()

    if not ARMADO:
        IMPRIMIR(f"[{acao}] ignorado: autoclicker desarmado (pressione "
                 f"{config['hotkeys']['armar_desarmar'].upper()} para armar).")
        return

    ULTIMA_ATIVIDADE = time.monotonic()
    CONTADORES[acao] = CONTADORES.get(acao, 0) + 1

    simulacao = config.get("modo_simulacao", True)
    delay_s = config.get("delay_entre_cliques_ms", 80) / 1000.0
    verificar_cor = config.get("verificar_cor", False)
    tolerancia_cor = config.get("tolerancia_cor", 30)

    IMPRIMIR(f"[{acao}] disparando em {len(config['boletas'])} conta(s) "
             f"({'SIMULACAO' if simulacao else 'REAL'})...")

    for boleta in config["boletas"]:
        nome = boleta.get("nome", "?")
        valor = boleta.get("botoes", {}).get(acao)
        if valor is None:
            IMPRIMIR(f"  - {nome}: sem coordenada cadastrada para '{acao}', pulando.")
            continue

        pos, cor_esperada = obter_pos_cor(valor)
        x, y = pos

        if verificar_cor and not simulacao and not cor_bate(pos, cor_esperada, tolerancia_cor):
            IMPRIMIR(f"  - {nome}: cor no ponto ({x}, {y}) mudou, pulando "
                     "(layout pode ter mudado - recalibre se persistir).")
            registrar_historico(f"[{acao}] {nome}: PULADO (cor nao bate em {x},{y})")
            continue

        if simulacao:
            IMPRIMIR(f"  - {nome}: clicaria em ({x}, {y})")
        else:
            pyautogui.click(x, y)
            IMPRIMIR(f"  - {nome}: clicado em ({x}, {y})")

        registrar_historico(
            f"[{acao}] {nome}: {'SIMULADO' if simulacao else 'CLICADO'} em ({x}, {y})"
        )
        time.sleep(delay_s)

    _beep()
    if AO_DISPARAR is not None:
        try:
            AO_DISPARAR()
        except Exception:
            pass


def _boleta_mestre_apregoar(config):
    """A conta 'mestre' e' aquela onde voce digita o preco manualmente - o
    autoclicker copia dela e cola nas outras. Por padrao e' a primeira
    conta com 'campo_preco' calibrado; da pra forcar outra colocando
    "conta_mestre": "NomeDaConta" no config.json."""
    boletas = config["boletas"]
    nome_mestre = config.get("conta_mestre")
    if nome_mestre:
        for b in boletas:
            if b.get("nome") == nome_mestre:
                return b
    for b in boletas:
        if b.get("botoes", {}).get("campo_preco") is not None:
            return b
    return None


def executar_apregoar(direcao):
    """Copia o preco que voce digitou na boleta mestre (Ctrl+A, Ctrl+C) e
    cola (Ctrl+V) + clica '{direcao}' em todas as OUTRAS contas. A conta
    mestre fica de fora do disparo - voce manda a ordem dela manualmente,
    como sempre fez; isso so replica pras demais."""
    global ULTIMA_ATIVIDADE

    acao = f"apregoar_{direcao}"
    if not pode_disparar(acao):
        return

    config = config_atual()

    if not ARMADO:
        IMPRIMIR(f"[{acao}] ignorado: autoclicker desarmado (pressione "
                 f"{config['hotkeys']['armar_desarmar'].upper()} para armar).")
        return

    boleta_mestre = _boleta_mestre_apregoar(config)
    if boleta_mestre is None:
        IMPRIMIR(f"[{acao}] nenhuma conta com 'campo_preco' calibrado - "
                 "recalibre a conta que voce usa pra digitar o preco (calibrar.py, opcao 'r').")
        return

    valor_campo_mestre = boleta_mestre["botoes"]["campo_preco"]
    pos_campo_mestre, _ = obter_pos_cor(valor_campo_mestre)

    ULTIMA_ATIVIDADE = time.monotonic()
    CONTADORES[acao] = CONTADORES.get(acao, 0) + 1

    simulacao = config.get("modo_simulacao", True)
    delay_s = config.get("delay_entre_cliques_ms", 80) / 1000.0
    verificar_cor = config.get("verificar_cor", False)
    tolerancia_cor = config.get("tolerancia_cor", 30)

    outras = [b for b in config["boletas"] if b is not boleta_mestre]
    IMPRIMIR(f"[{acao}] copiando preco de '{boleta_mestre.get('nome')}' e replicando "
             f"em {len(outras)} outra(s) conta(s) ({'SIMULACAO' if simulacao else 'REAL'})...")

    if simulacao:
        IMPRIMIR(f"  - copiaria o preco do campo em {tuple(pos_campo_mestre)} (conta mestre)")
    else:
        pyautogui.click(*pos_campo_mestre)
        time.sleep(delay_s)
        keyboard.send("ctrl+a")
        time.sleep(delay_s)
        keyboard.send("ctrl+c")
        time.sleep(delay_s)

    for boleta in outras:
        nome = boleta.get("nome", "?")
        botoes = boleta.get("botoes", {})
        valor_campo = botoes.get("campo_preco")
        # o botao do apregoar (ex: "C Stop"/"V Limite") e' diferente do
        # botao de mercado (ex: "C Mercado"/"V Mercado") usado por
        # executar_acao - por isso e' uma chave propria, "apregoar_{direcao}",
        # e nao a mesma chave "compra"/"venda".
        chave_botao = f"apregoar_{direcao}"
        valor_acao = botoes.get(chave_botao)

        if valor_campo is None or valor_acao is None:
            IMPRIMIR(f"  - {nome}: sem 'campo_preco' ou '{chave_botao}' cadastrado, pulando.")
            continue

        pos_campo, _ = obter_pos_cor(valor_campo)
        pos_acao, cor_esperada = obter_pos_cor(valor_acao)
        xa, ya = pos_acao

        if verificar_cor and not simulacao and not cor_bate(pos_acao, cor_esperada, tolerancia_cor):
            IMPRIMIR(f"  - {nome}: cor no botao '{chave_botao}' ({xa}, {ya}) mudou, pulando "
                     "(layout pode ter mudado - recalibre se persistir).")
            registrar_historico(f"[{acao}] {nome}: PULADO (cor nao bate em {xa},{ya})")
            continue

        if simulacao:
            IMPRIMIR(f"  - {nome}: colaria o preco em {tuple(pos_campo)} e clicaria "
                     f"'{direcao}' em ({xa}, {ya})")
        else:
            pyautogui.click(*pos_campo)
            time.sleep(delay_s)
            keyboard.send("ctrl+a")
            time.sleep(delay_s)
            keyboard.send("ctrl+v")
            time.sleep(delay_s)
            pyautogui.click(xa, ya)
            IMPRIMIR(f"  - {nome}: preco colado, '{direcao}' clicado em ({xa}, {ya})")

        registrar_historico(
            f"[{acao}] {nome}: {'SIMULADO' if simulacao else 'EXECUTADO'} em ({xa}, {ya})"
        )
        time.sleep(delay_s)

    _beep()
    if AO_DISPARAR is not None:
        try:
            AO_DISPARAR()
        except Exception:
            pass


def alternar_armado():
    global ARMADO, ULTIMA_ATIVIDADE
    ARMADO = not ARMADO
    ULTIMA_ATIVIDADE = time.monotonic()
    estado = "ARMADO" if ARMADO else "desarmado"
    IMPRIMIR(f"\n*** Autoclicker {estado} ***\n")
    registrar_historico(f"Autoclicker {estado}")


def verificar_auto_desarme():
    """Se ARMADO e configurado auto_desarmar_minutos > 0, desarma sozinho
    apos esse tempo sem nenhum disparo. Chamar periodicamente (GUI usa
    root.after, CLI usa uma thread daemon - ver main())."""
    if not ARMADO:
        return
    minutos = config_atual().get("auto_desarmar_minutos", 0)
    if not minutos:
        return
    if time.monotonic() - ULTIMA_ATIVIDADE >= minutos * 60:
        IMPRIMIR(f"\n*** Auto-desarmado por inatividade ({minutos} min) ***\n")
        registrar_historico(f"Auto-desarmado por inatividade ({minutos} min)")
        alternar_armado()


def resumir_historico(caminho=CAMINHO_LOG):
    """Le o historico.log e devolve um resumo: {(acao, conta, resultado): contagem}."""
    import re

    padrao = re.compile(r"\[(\w+)\]\s+([^:]+):\s+(\w+)")
    contagem = {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                m = padrao.search(linha)
                if not m:
                    continue
                acao, conta, resultado = m.group(1), m.group(2).strip(), m.group(3)
                chave = (acao, conta, resultado)
                contagem[chave] = contagem.get(chave, 0) + 1
    except FileNotFoundError:
        pass
    return contagem


def alternar_modo_simulacao():
    config = config_atual()
    config["modo_simulacao"] = not config.get("modo_simulacao", True)
    caminho = PERFIS[INDICE_PERFIL][0]
    salvar_config(caminho, config)
    estado = "SIMULACAO" if config["modo_simulacao"] else "REAL"
    IMPRIMIR(f"\n*** Modo alterado para: {estado} ***\n")
    registrar_historico(f"Modo alterado para {estado}")


def trocar_perfil():
    global INDICE_PERFIL
    if len(PERFIS) < 2:
        IMPRIMIR("So existe um perfil carregado, nada pra trocar.")
        return
    INDICE_PERFIL = (INDICE_PERFIL + 1) % len(PERFIS)
    caminho, config = PERFIS[INDICE_PERFIL]
    IMPRIMIR(f"\n*** Perfil ativo agora: {caminho} "
             f"(contas: {[b.get('nome') for b in config['boletas']]}) ***\n")
    registrar_historico(f"Perfil trocado para {caminho}")


def _registrar_hotkeys_cli():
    hotkeys = config_atual()["hotkeys"]

    for acao in ("compra", "venda", "zerar", "cancelar_zerar"):
        tecla = hotkeys.get(acao)
        if tecla:
            keyboard.add_hotkey(tecla, executar_acao, args=(acao,))

    for direcao in ("compra", "venda"):
        acao = f"apregoar_{direcao}"
        tecla = hotkeys.get(acao, HOTKEYS_PADRAO_EXTRAS.get(acao))
        if tecla:
            keyboard.add_hotkey(tecla, executar_apregoar, args=(direcao,))

    keyboard.add_hotkey(hotkeys["armar_desarmar"], alternar_armado)

    tecla_modo = hotkeys.get("alternar_modo_simulacao", "f11")
    keyboard.add_hotkey(tecla_modo, alternar_modo_simulacao)

    if len(PERFIS) > 1:
        tecla_perfil = hotkeys.get("trocar_perfil", "f10")
        keyboard.add_hotkey(tecla_perfil, trocar_perfil)


def main():
    ok, motivo = validar_licenca()
    print(f"Licenca: {motivo}")
    if not ok:
        print("Autoclicker bloqueado.")
        sys.exit(1)

    caminhos = sys.argv[1:] if len(sys.argv) > 1 else ["config.json"]
    carregar_perfis(caminhos)
    config = config_atual()
    hotkeys = config["hotkeys"]

    print("Autoclicker carregado.")
    if len(PERFIS) > 1:
        print(f"Perfis carregados: {[c for c, _ in PERFIS]} (troca com "
              f"{hotkeys.get('trocar_perfil', 'f10').upper()})")
    print(f"Contas configuradas: {[b.get('nome') for b in config['boletas']]}")
    print(f"Modo simulacao: {config.get('modo_simulacao', True)}")
    print(f"Verificar cor antes de clicar: {config.get('verificar_cor', False)}")
    print("Hotkeys:")
    for acao, tecla in hotkeys.items():
        print(f"  {tecla.upper():>6}  ->  {acao}")
    print(f"\nComecando DESARMADO. Pressione {hotkeys['armar_desarmar'].upper()} para armar.\n")

    _registrar_hotkeys_cli()

    def _watchdog_auto_desarme():
        while True:
            time.sleep(30)
            verificar_auto_desarme()

    threading.Thread(target=_watchdog_auto_desarme, daemon=True).start()

    print(f"Pressione {hotkeys['sair'].upper()} para sair.")
    keyboard.wait(hotkeys["sair"])
    print(f"Disparos nesta sessao: {CONTADORES}")
    print("Encerrado.")


if __name__ == "__main__":
    main()
