#!/usr/bin/env python3
"""BatteryGuardian: alertas de bateria con voz y pitidos."""

import os, sys, time, glob, subprocess, fcntl

HOME = os.path.expanduser("~")
PIPER = os.path.join(HOME, "BatteryGuardian/.venv/bin/piper")
MODELO = os.path.join(HOME, "BatteryGuardian/voices/es_AR-daniela-high.onnx")
WAV = "/tmp/aviso_bateria.wav"
TEXTO = "La bateria esta llena. Por favor, desconecta el cargador."
PITIDO = os.path.join(HOME, "BatteryGuardian/pip.wav")
SYS_PS = "/sys/class/power_supply"
UMBRAL_80 = 80
PRUEBA = os.environ.get("PRUEBA") == "1"

def log(m):
    print(time.strftime("[%H:%M:%S] ") + m, flush=True)

def leer(ruta):
    try:
        with open(ruta) as f:
            return f.read().strip()
    except OSError:
        return None

def estado_bateria():
    porc = status = None
    for bat in sorted(glob.glob(SYS_PS + "/BAT*")):
        p = leer(bat + "/capacity")
        s = leer(bat + "/status")
        if p is not None:
            porc, status = int(p), (s or "").lower()
            break
    enchufado = False
    for ac in sorted(glob.glob(SYS_PS + "/A*")):
        if (leer(ac + "/type") or "").lower() == "mains":
            if leer(ac + "/online") == "1":
                enchufado = True
    return porc, status, enchufado

def override_audio():
    mute = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"],
                          capture_output=True, text=True).stdout.split()[-1]
    vol = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                         capture_output=True, text=True).stdout.split()[4]
    subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"])
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "100%"])
    return mute, vol

def restaurar_audio(mute, vol):
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", vol])
    subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", mute])

def hablar():
    with open(WAV, "wb") as f:
        subprocess.run([PIPER, "-m", MODELO, "-f", WAV],
                       input=TEXTO.encode(), stdout=f, check=True)
    estado = override_audio()
    try:
        subprocess.run(["aplay", "-q", WAV], check=True)
    finally:
        restaurar_audio(*estado)

def pip():
    estado = override_audio()
    try:
        subprocess.run(["paplay", PITIDO], check=False)
    finally:
        restaurar_audio(*estado)

def notificar(titulo, cuerpo):
    subprocess.run(["notify-send", "-u", "critical", titulo, cuerpo],
                   check=False)

def main():
    cerrojo = open("/tmp/batteryguardian.lock", "w")
    try:
        fcntl.flock(cerrojo, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("Ya hay otra instancia activa; saliendo.")
        return 1
    log("Monitor iniciado.")
    if PRUEBA:
        hablar()
        pip()
        log("Prueba completada.")
        return 0
    aviso80 = False
    en_bucle_100 = False
    while True:
        porc, status, enchufado = estado_bateria()
        if porc is None:
            time.sleep(10)
            continue
        if enchufado and porc >= UMBRAL_80 and porc < 100 and not aviso80:
            pip()
            notificar("Bateria al 80%", "Puedes desconectar el cargador.")
            aviso80 = True
        if porc < UMBRAL_80:
            aviso80 = False
        if enchufado and (porc >= 100 or status in ("full", "not charging")):
            if not en_bucle_100:
                hablar()
                notificar("Bateria llena", "Desconecta el cargador.")
                en_bucle_100 = True
            pip()  # pitidos constantes cada segundo
        else:
            en_bucle_100 = False
        time.sleep(1)
    return 0

if __name__ == "__main__":
    sys.exit(main())
