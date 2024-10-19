import os
import requests
import logging

from flask import Flask, request, jsonify
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Credenciales de la API de WhatsApp Business
WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

# Token de verificación para el webhook
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'my_verify_token')

# Endpoint del Amazon API Gateway
API_GATEWAY_ENDPOINT = 'https://2tgxvp0kea.execute-api.us-west-2.amazonaws.com/dev/ask'

logging.basicConfig(level=logging.DEBUG)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Handle verification challenge
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Invalid verification token', 403
    elif request.method == 'POST':
        # Handle incoming messages
        data = request.get_json()
        # Check if data contains 'entry'
        if data and data.get('entry'):
            entries = data['entry']
            for entry in entries:
                changes = entry.get('changes')
                if changes:
                    for change in changes:
                        value = change.get('value')
                        if value and value.get('messages'):
                            messages = value['messages']
                            for message in messages:
                                # Extract message details
                                sender_id = message.get('from')  # Phone number of sender
                                message_type = message.get('type')
                                # Handle text messages
                                if message_type == 'text':
                                    message_text = message['text']['body']
                                    # Generate response
                                    response_text = generar_respuesta(message_text)
                                    # Send response back via WhatsApp
                                    enviar_mensaje_whatsapp(response_text, sender_id)
                                else:
                                    # Handle other message types (e.g., image, audio, etc.)
                                    # For now, we can send a default message or ignore
                                    enviar_mensaje_whatsapp("Lo siento, solo puedo procesar mensajes de texto por ahora.", sender_id)
        else:
            # Return a 404 if no entries found
            return 'No entries to process', 404
        # Return a 200 OK response
        return 'Event received', 200

def generar_respuesta(mensaje_usuario):
    """
    Sends the user's message as a prompt to the API Gateway endpoint
    and returns the response.
    """
    payload = {
        "prompt": mensaje_usuario
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(API_GATEWAY_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        # Adjust the response extraction based on the actual response format
        respuesta = data.get('response', 'Lo siento, no pude procesar tu solicitud.')
        return respuesta
    except requests.exceptions.RequestException as e:
        print(f"Error al llamar al endpoint de API Gateway: {e}")
        return 'Lo siento, ocurrió un error al procesar tu solicitud.'

def enviar_mensaje_whatsapp(mensaje, numero_destino):
    """
    Sends a message via WhatsApp to the specified recipient.
    """
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        # You can log or process the response if needed
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar mensaje por WhatsApp: {e}")
        return None

if __name__ == '__main__':
    # Run the Flask app
    app.run(port=5000, debug=True)
