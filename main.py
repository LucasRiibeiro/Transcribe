from flask import Flask, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
from functools import wraps
import io
import logging
from datetime import datetime
import os

app = Flask(__name__)

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Define IP permitido diretamente
ALLOWED_IPS = {"transcribe-8ia099ami-projetotranscrevers-projects.vercel.app"}

logging.info(f"IPs permitidos: {ALLOWED_IPS}")

def check_ip(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if not ALLOWED_IPS or request.host not in ALLOWED_IPS:
            logging.warning(f"Tentativa de acesso não autorizada do IP: {request_ip}")
            return 'Acesso não autorizado', 403
        logging.info(f"Acesso autorizado do IP: {request_ip}")
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def log_request_info():
    logging.info(f"Request IP: {request.remote_addr}")
    logging.info(f"Headers: {dict(request.headers)}")

@app.route('/', methods=['GET'])
@check_ip
def home():
    return '<center><h1>[POST] /transcrever with "audio" form file (wav, ogg, mp3)</h1></center>'

@app.route('/transcrever', methods=['POST'])
@check_ip
def transcrever():
    request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    request_ip = request.remote_addr

    logging.info(f"Requisição recebida do IP: {request_ip}")

    if 'audio' not in request.files:
        logging.error(f"{request_time} - Nenhum arquivo de áudio enviado - IP: {request_ip}")
        return jsonify({'erro': 'Nenhum arquivo de áudio enviado'}), 400

    audio_file = request.files['audio']
    if not audio_file:
        logging.error(f"{request_time} - Arquivo de áudio inválido - IP: {request_ip}")
        return jsonify({'erro': 'Arquivo de áudio inválido'}), 400

    content_type = audio_file.content_type
    filename = audio_file.filename
    extension = os.path.splitext(filename)[1].lower()
    logging.info(f"Content-Type: {content_type}, Filename: {filename}")

    if extension in ['.ogg', '.mp3', '.wav']:
        content_type = f'audio/{extension[1:]}'

    supported_types = ['audio/wav', 'audio/ogg', 'audio/mp3']

    if content_type not in supported_types:
        logging.error(f"{request_time} - Tipo de arquivo não suportado: {content_type} - IP: {request_ip}")
        return jsonify({'erro': 'Apenas arquivos WAV, OGG e MP3 são permitidos'}), 400

    try:
        raw_data = audio_file.read()
        audio_file.seek(0)

        if content_type in ['audio/ogg', 'audio/mp3']:
            audio = AudioSegment.from_file(io.BytesIO(raw_data))
            audio = audio.set_frame_rate(16000).set_channels(1)
            wav_io = io.BytesIO()
            audio.export(wav_io, format='wav')
            wav_io.seek(0)
            audio_file = wav_io

        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            transcribed_text = recognizer.recognize_google(audio_data, language='pt-BR')

        logging.info(f"{request_time} - Transcrição bem-sucedida: {transcribed_text} - IP: {request_ip}")
        return jsonify({'transcricao': transcribed_text}), 200

    except sr.UnknownValueError:
        logging.error(f"{request_time} - Não foi possível reconhecer o áudio - IP: {request_ip}")
        return jsonify({'erro': 'Não foi possível reconhecer o áudio'}), 400
    except sr.RequestError as e:
        logging.error(f"{request_time} - Erro ao se comunicar com o serviço de reconhecimento de fala: {e} - IP: {request_ip}")
        return jsonify({'erro': 'Erro ao se comunicar com o serviço de reconhecimento de fala'}), 500
    except Exception as e:
        logging.error(f"{request_time} - Erro inesperado: {e} - IP: {request_ip}")
        return jsonify({'erro': 'Erro interno no servidor'}), 500

# O Vercel usa o app diretamente
handler = app
