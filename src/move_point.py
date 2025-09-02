import os
import sys
import argparse
from typing import Optional

from qgis.core import (
    QgsApplication,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsSpatialIndex,
)


def load_layer(path: str, name: str) -> Optional[QgsVectorLayer]:
    """
    Загружает векторный слой из файла.

    Args:
        path: Путь к файлу слоя.
        name: Имя слоя.

    Returns:
        Объект QgsVectorLayer или None в случае ошибки.
    """
    if not os.path.exists(path):
        print(f"Ошибка: Файл не найден -> {path}", file=sys.stderr)
        return None

    layer = QgsVectorLayer(path, name, "ogr")
    if not layer.isValid():
        print(f"Ошибка: Не удалось загрузить слой -> {path}", file=sys.stderr)
        return None

    print(f"Слой '{name}' успешно загружен.")
    return layer


def get_sorted_rectangles(rect_layer: QgsVectorLayer) -> list[QgsFeature]:
    """
    Возвращает отсортированный список прямоугольников по координате X.

    Args:
        rect_layer: Слой с прямоугольниками.

    Returns:
        Отсортированный список объектов QgsFeature.
    """
    rectangles = list(rect_layer.getFeatures())
    # Сортируем по X-координате центроида
    rectangles.sort(key=lambda r: r.geometry().centroid().asPoint().x())
    print(f"Найдено и отсортировано {len(rectangles)} прямоугольников.")
    return rectangles


def create_spatial_index(layer: QgsVectorLayer) -> QgsSpatialIndex:
    """
    Создает и возвращает пространственный индекс для слоя.

    Args:
        layer: Векторный слой.

    Returns:
        Объект QgsSpatialIndex.
    """
    index = QgsSpatialIndex(layer.getFeatures())
    print(f"Пространственный индекс для слоя '{layer.name()}' создан.")
    return index


def map_points_to_rectangles(
    point_layer: QgsVectorLayer,
    rect_layer: QgsVectorLayer,
    rect_index: QgsSpatialIndex,
) -> dict[int, list[QgsFeature]]:
    """
    Сопоставляет точки с содержащими их прямоугольниками.

    Args:
        point_layer: Слой с точками.
        rect_layer: Слой с прямоугольниками.
        rect_index: Пространственный индекс прямоугольников.

    Returns:
        Словарь, где ключ - ID прямоугольника, значение - список точек.
    """
    point_map = {rect.id(): [] for rect in rect_layer.getFeatures()}

    for point_feat in point_layer.getFeatures():
        point_geom = point_feat.geometry()
        # Находим кандидатов для пересечения
        candidate_ids = rect_index.intersects(point_geom.boundingBox())

        for rect_id in candidate_ids:
            rect_feat = rect_layer.getFeature(rect_id)
            if rect_feat.geometry().contains(point_geom):
                point_map[rect_feat.id()].append(point_feat)
                break  # Точка может быть только в одном прямоугольнике

    total_points = sum(len(points) for points in point_map.values())
    print(f"Сопоставлено {total_points} точек с прямоугольниками.")
    return point_map


def move_points(
    point_layer: QgsVectorLayer,
    sorted_rects: list[QgsFeature],
    point_map: dict[int, list[QgsFeature]],
) -> bool:
    """
    Перемещает точки в следующие прямоугольники.

    Args:
        point_layer: Слой точек для обновления.
        sorted_rects: Отсортированный список прямоугольников.
        point_map: Словарь сопоставления точек и прямоугольников.

    Returns:
        True в случае успеха, False в противном случае.
    """
    if not sorted_rects:
        print("Ошибка: Нет прямоугольников для перемещения точек.", file=sys.stderr)
        return False

    num_rects = len(sorted_rects)

    point_layer.startEditing()

    try:
        for i, current_rect in enumerate(sorted_rects):
            target_index = (i + 1) % num_rects
            target_rect = sorted_rects[target_index]

            current_centroid = current_rect.geometry().centroid().asPoint()
            target_centroid = target_rect.geometry().centroid().asPoint()

            if current_rect.id() not in point_map:
                continue

            points_to_move = point_map[current_rect.id()]
            if not points_to_move:
                continue

            print(
                f"Перемещение {len(points_to_move)} точек из прямоугольника ID {current_rect.id()} в ID {target_rect.id()}"
            )

            for point_feat in points_to_move:
                old_geom = point_feat.geometry()
                old_point = old_geom.asPoint()

                # Вычисляем смещение относительно центроида старого прямоугольника
                offset_x = old_point.x() - current_centroid.x()
                offset_y = old_point.y() - current_centroid.y()

                # Применяем смещение к центроиду нового прямоугольника
                new_x = target_centroid.x() + offset_x
                new_y = target_centroid.y() + offset_y

                new_geom = QgsGeometry.fromPointXY(QgsPointXY(new_x, new_y))
                point_layer.changeGeometry(point_feat.id(), new_geom)

        if point_layer.commitChanges():
            print("Изменения успешно сохранены.")
            return True
        else:
            print("Ошибка: Не удалось сохранить изменения:", file=sys.stderr)
            for error in point_layer.commitErrors():
                print(f" - {error}", file=sys.stderr)
            point_layer.rollBack()
            return False

    except Exception as e:
        print(f"Критическая ошибка при перемещении точек: {e}", file=sys.stderr)
        point_layer.rollBack()
        return False


def process_layers(points_path: str, rects_path: str) -> bool:
    """
    Выполняет основную логику обработки слоев.
    """
    point_layer = load_layer(points_path, "points")
    rect_layer = load_layer(rects_path, "rectangles")

    if not point_layer or not rect_layer:
        return False

    # Основная логика
    sorted_rects = get_sorted_rectangles(rect_layer)
    rect_index = create_spatial_index(rect_layer)
    point_map = map_points_to_rectangles(point_layer, rect_layer, rect_index)

    success = move_points(point_layer, sorted_rects, point_map)

    # Явно удаляем объекты слоев, чтобы избежать падения
    del point_layer
    del rect_layer
    print("Объекты слоев очищены.")

    return success


def main():
    """
    Главная функция для выполнения скрипта.
    """
    parser = argparse.ArgumentParser(
        description="Перемещает точки из одного прямоугольника в следующий.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Пример использования:
  python src/move_point.py --points data/points.gpkg --rects data/rectangles.gpkg
""",
    )
    parser.add_argument("--points", required=True, help="Путь к слою с точками (.gpkg)")
    parser.add_argument(
        "--rects", required=True, help="Путь к слою с прямоугольниками (.gpkg)"
    )
    args = parser.parse_args()

    # Инициализация QGIS
    qgs = QgsApplication([], False)
    qgs.initQgis()
    print("QGIS инициализирован.")

    try:
        success = process_layers(args.points, args.rects)
        if not success:
            sys.exit(1)
    finally:
        # Очистка
        qgs.exitQgis()
        print("QGIS деинициализирован.")


if __name__ == "__main__":
    main()
