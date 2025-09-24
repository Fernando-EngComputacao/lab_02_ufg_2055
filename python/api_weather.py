# !pip install paho-mqtt requests -q

import paho.mqtt.client as mqtt
import requests
import json
import time

# --- 1. Configurações ---
# A chave de API está inserida diretamente no código conforme solicitado.
API_KEY = "807dcc76bb1575edaa655d5bae20a8e7"

# Configurações do MQTT Broker e OpenWeatherMap
BROKER_ADDRESS = "broker.mqtt-dashboard.com"
BROKER_PORT = 1883
MQTT_TOPIC = "ufg/2025/weather"
API_URL_BASE = "https://api.openweathermap.org/data/2.5/weather"
CIDADE = "Goiânia,br"

# --- 2. Funções Auxiliares ---

def get_weather_data(api_key, cidade):
    """Busca os dados do clima na API e retorna um dicionário formatado."""
    params = {'q': cidade, 'APPID': api_key, 'units': 'metric', 'lang': 'pt_br'}
    try:
        response = requests.get(API_URL_BASE, params=params)
        response.raise_for_status()
        data = response.json()
        payload_formatado = {
            "cidade": data.get("name"),
            "temperatura_c": data["main"].get("temp"),
            "sensacao_termica_c": data["main"].get("feels_like"),
            "umidade_percent": data["main"].get("humidity"),
            "clima_desc": data["weather"][0].get("description"),
            "timestamp_unix": data.get("dt")
        }
        return payload_formatado
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Erro HTTP ao buscar clima: {http_err}")
        if response.status_code == 401: print("   -> A API Key no código pode ser inválida ou ter expirado.")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado ao buscar clima: {e}")
    return None

def on_connect(client, userdata, flags, rc):
    """Callback de conexão."""
    if rc == 0:
        print("✅ Conectado ao Broker MQTT com sucesso!")
    else:
        print(f"Falha ao conectar, código de retorno: {rc}\n")

# --- 3. Lógica Principal ---

client = mqtt.Client(client_id=f"ufg_weather_publisher_{int(time.time())}")
client.on_connect = on_connect

print(f"Conectando ao broker {BROKER_ADDRESS}...")
client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
client.loop_start()

try:
    while True:
        print("\n------------------------------")
        weather_payload = get_weather_data(API_KEY, CIDADE)

        if weather_payload:
            message = json.dumps(weather_payload, ensure_ascii=False)
            result = client.publish(MQTT_TOPIC, message)

            if result[0] == 0:
                print(f"🛰️  Mensagem publicada com sucesso no tópico:")
                print(f"   '{MQTT_TOPIC}'")
                print(f"   Payload: {message}")
            else:
                print(f"⚠️  Falha ao enviar mensagem para o tópico '{MQTT_TOPIC}'")
        else:
            print("Não foi possível obter os dados do clima. Nova tentativa em 3 segundos.")

        time.sleep(5)

except KeyboardInterrupt:
    print("\n\n🛑 Publicação interrompida pelo usuário.")
finally:
    print("Desconectando do broker...")
    client.loop_stop()
    client.disconnect()
    print("Cliente desconectado.")