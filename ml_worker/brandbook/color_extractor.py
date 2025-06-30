import logging
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
from webcolors import rgb_to_hex
import cv2

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

def get_image(image_path):
    """Загружает изображение и преобразует в RGB"""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Не удалось загрузить изображение: {image_path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

def preprocess_image(image):
    """Преобразует изображение в плоский массив пикселей"""
    return image.reshape((image.shape[0] * image.shape[1], 3))

def auto_k_selection(image, max_k=6, sample_size=5000):
    """Автоматический выбор количества кластеров (k)"""
    logging.info(f"Начало автоматического выбора количества кластеров (max_k={max_k})")

    if len(image) > sample_size:
        np.random.shuffle(image)
        image = image[:sample_size]

    best_k = 2
    max_score = -np.inf
    possible_ks = [2, 3, 4, 5]

    for k in possible_ks:
        if k > len(image):
            continue
        kmeans = KMeans(n_clusters=k, n_init=3, init='random')
        labels = kmeans.fit_predict(image)
        score = -kmeans.inertia_
        logging.debug(f"k={k}, Inertia Score: {score:.2f}")
        if score > max_score:
            max_score = score
            best_k = k

    logging.info(f"Оптимальное количество кластеров: {best_k}")
    return best_k

def is_background_color(rgb, threshold=50):
    """Проверяет, является ли цвет фоном (черный или белый)"""
    white_dist = np.linalg.norm(np.array(rgb) - np.array([255, 255, 255]))
    black_dist = np.linalg.norm(np.array(rgb) - np.array([0, 0, 0]))
    return white_dist < threshold or black_dist < threshold

def get_dominant_colors(image, max_k=6, bg_threshold=50, sample_size=10000):
    """Извлечение основных цветов изображения без фона"""
    logging.info("Извлечение доминирующих цветов...")

    if len(image) > sample_size:
        np.random.shuffle(image)
        image = image[:sample_size]

    k = auto_k_selection(image, max_k)

    clf = KMeans(n_clusters=k, n_init=3, init='random')
    labels = clf.fit_predict(image)
    counts = Counter(labels)

    clusters = list(zip(counts.values(), clf.cluster_centers_))
    clusters.sort(key=lambda x: x[0], reverse=True)

    filtered_colors = []
    for count, color in clusters:
        rgb = np.array(color).astype(int).tolist()
        if not is_background_color(rgb, bg_threshold):
            filtered_colors.append(rgb)

    if filtered_colors:
        logging.info(f"Найдено {len(filtered_colors)} основных цветов (без фона)")
    else:
        logging.warning("Все найденные цвета — фоновые. Возвращается пустой список.")
    return [rgb_to_hex(color) for color in filtered_colors]

def extract_colors(image_path, num_colors=5):
    """Получение HEX-цветов из изображения по пути"""
    try:
        logging.info(f"Извлечение цветовой палитры из {image_path}")
        image = get_image(image_path)
        processed_image = preprocess_image(image)
        colors = get_dominant_colors(processed_image, num_colors)
        return colors
    except Exception as e:
        logging.error(f"Ошибка при обработке изображения {image_path}: {e}")
        return []