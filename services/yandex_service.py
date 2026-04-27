"""
Сервис для работы с Yandex AI Studio API
Поддерживает: YandexGPT, SpeechKit (STT/TTS), Vision OCR, Embeddings
"""
import requests
import base64
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from utils.logger import logger
from config import (
    YANDEX_API_KEY, 
    YANDEX_FOLDER_ID, 
    YANDEX_API_URL, 
    YANDEX_GPT_MODEL,
    YANDEX_EMBEDDING_MODEL
)


class YandexAIService:
    """Клиент для работы с Yandex AI Studio"""

    def __init__(self):
        self.headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json"
        }
        logger.info("YandexAIService инициализирован")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def generate_text(self, prompt: str, system_prompt: str = None, temperature: float = 0.6) -> str:
        """
        Генерация текста через YandexGPT

        Args:
            prompt: Пользовательский запрос
            system_prompt: Системный промпт (опционально)
            temperature: Температура генерации (0.0-1.0)

        Returns:
            Сгенерированный текст
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})

        payload = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_GPT_MODEL}",
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": 2000
            },
            "messages": messages
        }

        response = requests.post(
            f"{YANDEX_API_URL}/completion",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()["result"]["alternatives"][0]["message"]["text"]
        logger.debug(f"YandexGPT ответ получен, длина: {len(result)} символов")
        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def speech_to_text(self, audio_path: str, lang: str = "ru-RU") -> str:
        """
        Распознавание речи через Yandex SpeechKit STT

        Args:
            audio_path: Путь к аудио файлу
            lang: Язык распознавания (ru-RU, en-US и т.д.)

        Returns:
            Распознанный текст
        """
        import subprocess
        import tempfile
        
        # Конвертируем в OGG OPUS если нужно
        converted_path = audio_path
        if audio_path.endswith('.mp3'):
            converted_path = audio_path.replace('.mp3', '.ogg')
            try:
                subprocess.run([
                    'ffmpeg', '-i', audio_path,
                    '-acodec', 'libopus',
                    '-f', 'ogg',
                    '-ar', '48000',
                    '-ac', '1',
                    converted_path
                ], check=True, capture_output=True)
                logger.info(f"Аудио конвертировано из MP3 в OGG OPUS")
            except Exception as e:
                logger.error(f"Ошибка конвертации аудио: {e}")
                raise
        
        with open(converted_path, "rb") as f:
            audio_data = f.read()

        stt_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        # Для STT API нужно убрать Content-Type из headers
        stt_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
        response = requests.post(
            stt_url,
            headers=stt_headers,
            data=audio_data,
            params={
                "lang": lang,
                "folderId": YANDEX_FOLDER_ID,
                "format": "oggopus",
                "sampleRateHertz": 48000
            },
            timeout=30
        )
        if response.status_code != 200:
            logger.error(f"STT API error {response.status_code}: {response.text}")
        response.raise_for_status()
        result = response.json().get("result", "")
        logger.debug(f"STT распознано: {len(result)} символов")
        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def text_to_speech(self, text: str, output_path: str, voice: str = "alena", lang: str = "ru-RU") -> str:
        """
        Синтез речи через Yandex SpeechKit TTS

        Args:
            text: Текст для озвучивания
            output_path: Путь для сохранения аудио
            voice: Голос (alena, filipp, ermil и т.д.)
            lang: Язык синтеза

        Returns:
            Путь к созданному файлу
        """
        tts_url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
        # Для TTS API нужно использовать query параметры и убрать Content-Type
        params = {
            "text": text,
            "lang": lang,
            "voice": voice,
            "folderId": YANDEX_FOLDER_ID,
            "format": "oggopus"
        }
        
        # Убираем Content-Type из headers для TTS запроса
        tts_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}

        response = requests.get(tts_url, headers=tts_headers, params=params, timeout=30)
        if response.status_code != 200:
            logger.error(f"TTS API error {response.status_code}: {response.text}")
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)
        logger.debug(f"TTS синтезирован файл: {output_path}")
        return output_path

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def analyze_image(self, image_path: str) -> dict:
        """
        Анализ изображения через Yandex Vision OCR

        Args:
            image_path: Путь к изображению

        Returns:
            Dict с полями 'text' (распознанный текст) и 'description' (описание)
        """
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        vision_url = "https://vision.api.cloud.yandex.net/vision/v1/batchAnalyze"
        payload = {
            "folderId": YANDEX_FOLDER_ID,
            "analyze_specs": [{
                "content": image_data,
                "features": [
                    {"type": "TEXT_DETECTION"},
                    {"type": "CLASSIFICATION"}
                ]
            }]
        }

        response = requests.post(vision_url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()

        results = response.json()["results"][0]["results"]
        text = ""
        description = ""

        for result in results:
            if "textDetection" in result:
                pages = result.get("textDetection", {}).get("pages", [])
                if pages:
                    text = " ".join([page.get("fullText", "") for page in pages])
            if "classification" in result:
                props = result.get("classification", {}).get("properties", [])
                if props:
                    description = props[0].get("name", "")

        logger.debug(f"Vision анализ: текст={len(text)} симв., описание={description}")
        return {"text": text, "description": description}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def get_embeddings(self, text: str) -> list:
        """
        Получение эмбеддингов текста для RAG

        Args:
            text: Текст для векторизации

        Returns:
            Список эмбеддингов (вектор размерности 256)
        """
        embed_url = f"{YANDEX_API_URL}/textEmbedding"
        payload = {
            "modelUri": f"emb://{YANDEX_FOLDER_ID}/{YANDEX_EMBEDDING_MODEL}",
            "text": text
        }

        response = requests.post(embed_url, headers=self.headers, json=payload, timeout=30)
        if response.status_code != 200:
            logger.error(f"Yandex API error {response.status_code}: {response.text}")
        response.raise_for_status()
        embedding = response.json()["embedding"]
        logger.info(f"Embeddings получены, размерность: {len(embedding)}")
        return embedding
