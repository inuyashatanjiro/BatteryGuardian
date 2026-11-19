# Battery Guardian 1.0

Alertas de batería para Ubuntu 24.04 con voz natural, pitidos y notificaciones.

## Qué hace

1. Al 80 % con cargador conectado: suena un pitido y aparece la notificación "Bateria al 80 %".
2. Al 100 %: una voz femenina en español anuncia "La batería está llena. Por favor, desconecta el cargador".
3. Si el cargador sigue conectado: suena "pip, pip, pip" cada segundo hasta desconectarlo.
4. Cada alerta suena aunque el sistema esté en silencio: se ajusta el volumen temporalmente y se restaura al terminar.

## Requisitos

- Ubuntu 24.04 (o Linux con PipeWire/PulseAudio y Python 3)

## Instalación

    sudo apt update
    sudo apt install -y python3-venv pulseaudio-utils aplay curl
    python3 -m venv ~/BatteryGuardian/.venv
    ~/BatteryGuardian/.venv/bin/pip install --upgrade piper-tts
    mkdir -p ~/BatteryGuardian/voices
    curl -fL -o ~/BatteryGuardian/voices/es_AR-daniela-high.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx
    curl -fL -o ~/BatteryGuardian/voices/es_AR-daniela-high.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx.json

Copia alerta_bateria.py y pip.wav a ~/BatteryGuardian/ y prueba:

    PRUEBA=1 python3 ~/BatteryGuardian/alerta_bateria.py

### Arranque automático

Crea ~/.config/systemd/user/batteryguardian.service con este contenido:

    [Unit]
    Description=Monitor de batería BatteryGuardian
    PartOf=graphical-session.target
    After=graphical-session.target

    [Service]
    Type=simple
    ExecStart=/usr/bin/python3 %h/BatteryGuardian/alerta_bateria.py
    Restart=always
    RestartSec=5

    [Install]
    WantedBy=default.target

Y actívalo:

    systemctl --user daemon-reload
    systemctl --user enable --now batteryguardian

## Comandos útiles

    systemctl --user status batteryguardian    # ver estado
    systemctl --user restart batteryguardian   # reiniciar
    journalctl --user -u batteryguardian -f    # log en vivo

## Personalización

Los valores editables están al inicio de alerta_bateria.py:
UMBRAL_80 (umbral del primer aviso), TEXTO (frase de la voz),
PITIDO (sonido del pitido) y MODELO (voz de Piper).

## Notas

- El aviso del 80 % suena solo al cruzar el umbral con el monitor activo.
- La voz Daniela pesa cerca de 110 MB y se descarga de Hugging Face.

## Licencia

MIT
