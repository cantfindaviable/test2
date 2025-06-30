from rmq.rmqconf import RabbitMQConfig
from llm import do_task
import pika
import time
import requests
import logging
import json
from services.ml.image_generator import ImageGenerator
from services.ml.prompt_enhancer import PromptEnhancer
from services.ml.rag_searcher import RAGSearcher

# Настраиваем общий уровень логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Устанавливаем уровень WARNING для логов pika
logging.getLogger('pika').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Определяем основной класс для обработки ML задач
class MLWorker:
    """
    Рабочий класс для обработки ML задач из очереди RabbitMQ.
    Обеспечивает подключение к очереди и обработку поступающих сообщений.
    """
    # Константы класса
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5
    RESULT_ENDPOINT = 'http://app:8080/api/ml/send_task_result'
    
    def __init__(self, config: RabbitMQConfig):
        """
        Инициализация обработчика с заданной конфигурацией.
        
        Args:
            config: Объект конфигурации RabbitMQ
        """
        # Сохраняем конфигурацию
        self.config = config
        # Инициализируем соединение как None
        self.connection = None
        # Инициализируем канал как None
        self.channel = None
        self.retry_count = 0
        
    def connect(self) -> None:
        """
        Установка соединения с сервером RabbitMQ с повторными попытками.
        """
        while True:
            try:
                connection_params = self.config.get_connection_params()
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.config.queue_name, durable=True)
                logger.info("Successfully connected to RabbitMQ")
                break
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                time.sleep(self.RETRY_DELAY)

    def cleanup(self):
        """Корректное закрытие соединений с RabbitMQ"""
        try:
            if self.channel:
                self.channel.close()
            if self.connection:
                self.connection.close()
            logger.info("Соединения успешно закрыты")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединений: {e}")

    def send_result(self, task_id: int, result_data: dict) -> bool:
        """
        Отправляет результат выполнения задачи в API.
        
        Args:
            task_id (int): ID задачи
            result_data (dict): Результаты обработки ML-моделей
        
        Returns:
            bool: True — успех, False — ошибка
        """
        try:
            logger.info(f"Отправка результатов задачи {task_id}. Результат: {result_data}")
            
            payload = {
                "task_id": task_id,
                "status": "completed",
                "enhanced_prompt": result_data.get("enhanced_prompt"),
                "image_url": result_data.get("image_url"),
                "context": " ".join([item for sublist in result_data.get("context") for item in sublist])
            }
            logger.info(f"Сформировали payload, отправляем на {self.RESULT_ENDPOINT}")
            url = f"{self.RESULT_ENDPOINT}/{task_id}"

            response = requests.post(url, json=payload)
            # response = requests.post(self.RESULT_ENDPOINT, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Результат успешно отправлен для задачи {task_id}")
                return True
            else:
                logger.error(f"Ошибка при отправке результата: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Не удалось отправить результат: {e}")
            return False

    def process_message(self, ch, method, properties, body):
        """
        Обработка полученного сообщения из очереди.
        
        Args:
            ch: Объект канала RabbitMQ
            method: Метод доставки сообщения
            properties: Свойства сообщения
            body: Тело сообщения
            
        Note:
            Симулирует обработку задачи с задержкой в 3 секунды
        """
        try:
            # Логируем информацию о полученном сообщении
            logger.info(f"Processing message: {body}")
            
            # Декодируем bytes в строку и затем парсим JSON
            data = json.loads(body.decode('utf-8'))

            if self.callback:
                # Вызываем внешний обработчик (process_task)
                result = self.callback(data)

                enhanced_prompt = result.get("enhanced_prompt")
                image_url = result.get("image_url")
                context = result.get("context")
                final_result = {
                    "enhanced_prompt": enhanced_prompt,
                    "image_url": image_url,
                    "context": context
                }
            else:
                # Резервный случай — если нет callback'а
                result = do_task(data['question'])
                final_result = {"result": result}

            logger.info(f"Final result: {final_result}")

            if self.send_result(data['task_id'], final_result):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                self.retry_count = 0
                logger.info("Task completed successfully")
            else:
                raise Exception("Failed to send result")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.retry_count += 1
            
            if self.retry_count >= self.MAX_RETRIES:
                logger.error("Max retries reached, rejecting message")
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                self.retry_count = 0
            else:
                time.sleep(self.RETRY_DELAY)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
              
    def send_to_next_queue(self, queue_name: str, message: dict):
        """Отправляет сообщение в указанную очередь"""
        channel = self.connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # persistent
        )
        logger.info(f"Сообщение отправлено в очередь {queue_name}: {message}")

    def start_consuming(self) -> None:
        """
        Запуск процесса получения сообщений из очереди.
        
        Note:
            Блокирующая операция, прерывается по Ctrl+C
        """
        try:
            # Настраиваем потребление сообщений из очереди
            self.channel.basic_consume(
                queue=self.config.queue_name,  # Имя очереди
                on_message_callback=self.process_message,  # Callback для обработки сообщений
                auto_ack=False  # Отключаем автоматическое подтверждение
            )
            # Логируем информацию о старте потребления сообщений
            logger.info('Started consuming messages. Press Ctrl+C to exit.')
            # Запускаем потребление сообщений
            self.channel.start_consuming()
        except KeyboardInterrupt:
            # Логируем информацию о завершении работы
            logger.info("Shutting down...")
        finally:
            # Закрываем соединение при завершении работы
            self.cleanup()
            
    def set_callback(self, callback):
        """Устанавливает пользовательский обработчик задач"""
        self.callback = callback
