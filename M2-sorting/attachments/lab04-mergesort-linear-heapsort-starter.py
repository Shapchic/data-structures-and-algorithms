#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 4. MergeSort, Counting, Radix и HeapSort: оценка производительности.

=============================================================================
             ШПАРГАЛКА ДЛЯ ЗАЩИТЫ ЛАБОРАТОРНОЙ РАБОТЫ № 4
              (Памятка студента: читать при ответе на защите)
=============================================================================

1. СВОДНАЯ ТАБЛИЦА СВОЙСТВ АЛГОРИТМОВ:
┌─────────────────┬───────────────────┬──────────────┬──────────────┬──────────────┬────────────┬───────────┬───────────┬───────────────────────┐
│ Алгоритм        │ Принцип / Идея    │ Лучшее время │ Среднее время│ Худшее время │ Доп. память│ Стабилен? │ In-place? │ Ограничения / Нюансы  │
├─────────────────┼───────────────────┼──────────────┼──────────────┼──────────────┼────────────┼───────────┼───────────┼───────────────────────┤
│ MergeSort       │ Разделяй и слияние│Theta(n log n)│Theta(n log n)│Theta(n log n)│ O(n)       │   ДА      │   НЕТ     │ Всегда строго n log n │
│ CountingSort    │ Индексация ключами│ Theta(n + k) │ Theta(n + k) │ Theta(n + k) │ O(n + k)   │   ДА      │   НЕТ     │ Ключи целые, k <= n   │
│ RadixSort (LSD) │ Поразрядно от мл. │ O(d*(n + b)) │ O(d*(n + b)) │ O(d*(n + b)) │ O(n + b)   │   ДА      │   НЕТ     │ Ключи неотрицательные │
│ HeapSort        │ Двоичная max-куча │Theta(n log n)│Theta(n log n)│Theta(n log n)│ O(1)       │   НЕТ     │   ДА      │ Кэш-недружелюбен      │
│ QuickSort (ЛР 3)│ 3-way partition   │Theta(n log n)│Theta(n log n)│ O(n^2)*      │ O(log n)   │   НЕТ     │   ДА      │ Худший астрономич. ред│
│ sorted() Timsort│ Адаптивный гибрид │ Theta(n)     │Theta(n log n)│Theta(n log n)│ O(n)       │   ДА      │   НЕТ     │ Стандартный в Python  │
└─────────────────┴───────────────────┴──────────────┴──────────────┴──────────────┴────────────┴───────────┴───────────┴───────────────────────┘
  Обозначения: n — размер массива, k = max - min + 1 (диапазон ключей),
               d = ceil(log_b(max)) (число разрядов), b = 10 (основание системы счисления).

2. КЛЮЧЕВЫЕ ТЕОРЕТИЧЕСКИЕ ВОПРОСЫ ДЛЯ ЗАЩИТЫ:
 - Информационно-теоретический предел сортировок сравнением:
   Любая сортировка, использующая только попарные сравнения a[i] < a[j], в худшем
   и среднем случаях делает Omega(n log n) сравнений (доказательство через бинарное
   дерево решений с n! листьями: глубина h >= log2(n!) = Omega(n log n)).
 - Почему CountingSort и RadixSort могут работать быстрее Omega(n log n)?
   Потому что они НЕ сравнивают элементы друг с другом! Они используют цифровые
   (адресные) свойства ключей: используют значение числа как индекс ячейки массива за O(1).
 - Почему HeapSort на практике медленнее QuickSort при одинаковом O(n log n)?
   Из-за плохой локальности ссылок (L1/L2 Cache Misses): узлы кучи прыгают по индексам
   i -> 2*i + 1 -> 4*i + 3, заставляя процессор постоянно подгружать разные строки памяти.

Запуск:
    python lab04-mergesort-linear-heapsort-starter.py --variant 21
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import random
import statistics
import sys
import time
import traceback

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1. Алгоритмы сортировки
# ---------------------------------------------------------------------------


def merge(left: list, right: list, key=None) -> list:
    """Стабильное слияние двух отсортированных списков в новый единый список.

    📌 ЧТО ДЕЛАЕТ ФУНКЦИЯ (Суть простыми словами):
      Принимает два списка `left` и `right`, которые УЖЕ отсортированы.
      С помощью двух указателей `i` и `j` последовательно сравнивает их элементы
      и формирует новый общий отсортированный список `merged`.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ:
      1. Указатель `i` смотрит на начало `left`, а `j` — на начало `right`.
      2. Сравниваем ключи: `if kfn(left[i]) <= kfn(right[j]):`.
      3. Меньший элемент добавляем в результирующий список `merged`.
      4. ВАЖНО: знак `<=` гарантирует СТАБИЛЬНОСТЬ! При равных ключах элемент из левой
         половины всегда добавляется раньше, сохраняя исходный порядок следования.
      5. Когда один из списков исчерпан, оставшийся хвост второго списка
         просто дописывается в конец через `.extend()`.

    ⏱️ СЛОЖНОСТЬ:
      - Время: O(len(left) + len(right)) — каждый элемент просматривается ровно 1 раз.
      - Память: O(len(left) + len(right)) — создаётся новый список для результата.
      - Стабильность: строго СТАБИЛЬНА благодаря `<=` (приоритет левого элемента).
    """
    kfn = key if key is not None else (lambda x: x)
    merged = []
    i = 0  # Текущий индекс в левом списке
    j = 0  # Текущий индекс в правом списке
    len_left = len(left)
    len_right = len(right)

    # Основной цикл слияния: пока оба списка содержат непросмотренные элементы
    while i < len_left and j < len_right:
        # УСЛОВИЕ <= ОБЕСПЕЧИВАЕТ СТАБИЛЬНОСТЬ:
        # Если элементы равны, элемент из левой половины берётся первым!
        # Так как в исходном массиве он шёл раньше элементов правой половины,
        # их взаимный порядок сохраняется.
        if kfn(left[i]) <= kfn(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    # Если в одном из списков ещё остались элементы — дописываем их
    if i < len_left:
        merged.extend(left[i:])
    if j < len_right:
        merged.extend(right[j:])

    return merged


def merge_sort(a: list, key=lambda x: x) -> list:
    """Сортировка слиянием (MergeSort): возвращает новый отсортированный список.

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      Классическая реализация парадигмы «Разделяй и властвуй» (Divide and Conquer).
      Массив рекурсивно делится ровно пополам, пока не останутся кусочки длиной 0 или 1
      элемент (которые уже тривиально упорядочены). Затем отсортированные половинки
      попарно объединяются функцией `merge()`.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ:
      1. Базовый случай рекурсии: `if len(a) <= 1:` — массив уже отсортирован, возвращаем его копию.
      2. Точка разделения: `mid = len(a) // 2`.
      3. Рекурсивный спуск: сортируем левую половину `left = merge_sort(a[:mid])`
         и правую половину `right = merge_sort(a[mid:])`.
      4. Слияние: объединяем две половинки стабильной процедурой `merge(left, right)`.

    ⏱️ СЛОЖНОСТЬ:
      - Лучший, Средний, Худший случаи: СТРОГО Theta(n log n) во ВСЕХ случаях!
        Рекуррентное уравнение: T(n) = 2*T(n/2) + O(n).
        Глубина дерева деления всегда строго равна ceil(log2 n), а на каждом уровне
        суммарная работа слияния всех отрезков равна O(n).
      - Память: O(n) вспомогательная память (на каждом уровне создаются новые списки).
      - Стабильность: СТАБИЛЬНА.

    🎓 ШПАРГАЛКА ДЛЯ ОТВЕТА НА ЗАЩИТЕ:
      - Вопрос: «Почему сложность MergeSort всегда строго n log n, даже на отсортированном входе?»
        Ответ: «Потому что алгоритм делит массив пополам строго независимо от значений ключей,
        и дерево рекурсии всегда имеет фиксированную глубину log2 n».
      - Вопрос: «Где MergeSort незаменим?»
        Ответ: «При внешней сортировке (External Sorting) гигантских файлов на жёстком диске,
        так как слияние читает файлы строго последовательно блоками, и при сортировке связных списков».
    """
    # Базовый случай: пустой массив или массив из 1 элемента уже упорядочен
    if len(a) <= 1:
        return list(a)

    kfn = key if key is not None else (lambda x: x)
    # Находим середину массива для деления на 2 равные части
    mid = len(a) // 2

    # Рекурсивно сортируем левую и правую части
    left = merge_sort(a[:mid], key=kfn)
    right = merge_sort(a[mid:], key=kfn)

    # Сливаем две отсортированные половины в единый результат
    return merge(left, right, key=kfn)


def counting_sort(a: list[int], key_max: int) -> list[int]:
    """Устойчивая сортировка подсчётом (CountingSort) целых чисел из [0, key_max].

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      Алгоритм без сравнений (non-comparison sort). Подсчитывает, сколько раз каждое
      число встречается во входном массиве, вычисляет префиксные суммы (накопленные частоты)
      и сразу ставит каждое число на его правильную позицию в результирующем массиве.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ (3 ФАЗЫ):
      1. Фаза подсчёта (гистограмма): создаём массив счётчиков `count` длины `key_max + 1`.
         Для каждого `x in a` увеличиваем `count[x] += 1`. Время: O(n).
      2. Фаза префиксных сумм: в цикле превращаем `count[i] += count[i - 1]`.
         Теперь `count[x]` содержит количество элементов `<= x`, то есть правую границу
         индексов для размещения числа `x` в отсортированном массиве. Время: O(k).
      3. Фаза устойчивой расстановки: создаём выходной массив `res` длины `n`.
         Проходим исходный массив СТРОГО С КОНЦА (`reversed(a)`):
           `count[x] -= 1`
           `res[count[x]] = x`
         Время: O(n).

    ⏱️ СЛОЖНОСТЬ:
      - Время: Theta(n + k) во ВСЕХ случаях, где k = key_max + 1.
      - Память: Theta(n + k) (массив счётчиков O(k) + результирующий массив O(n)).
      - Стабильность: строго СТАБИЛЬНА благодаря обходу входного массива С КОНЦА.

    ⚠️ ГРАНИЦЫ ПРИМЕНИМОСТИ (ОБЯЗАТЕЛЬНО СПРОСЯТ!):
      - Алгоритм фантастически быстр (линейное время O(n)), когда диапазон ключей мал (k <= n).
      - Если диапазон велик (например, 32-битные числа k = 10^9 при n = 10^5):
        попытка выделить массив счётчиков `count` на 10^9 элементов потребует ~8 ГБ RAM
        и приведёт к `MemoryError`. В таких случаях CountingSort теряет смысл!

    🎓 ШПАРГАЛКА ДЛЯ ОТВЕТА НА ЗАЩИТЕ:
      - Вопрос: «Почему в фазе расстановки исходный массив обходится с конца (reversed)?»
        Ответ: «Это ключевое условие стабильности! Элемент с ключом x, стоявший во входе
        позже (правее), при обходе с конца обработается первым и займёт наибольшую доступную
        ячейку count[x] - 1. Предшествующий ему равный элемент займёт ячейку count[x] - 2.
        Так сохраняется исходный взаимный порядок дубликатов».
    """
    if not a:
        return []
    if key_max < 0:
        raise ValueError("key_max должен быть неотрицательным")

    # -----------------------------------------------------------------------
    # ФАЗА 1: Подсчёт частот появления каждого ключа
    # Создаём массив счётчиков размера k = key_max + 1
    # -----------------------------------------------------------------------
    count = [0] * (key_max + 1)
    for x in a:
        count[x] += 1

    # -----------------------------------------------------------------------
    # ФАЗА 2: Префиксные суммы (накопленные частоты)
    # После этого цикла count[i] показывает, сколько всего элементов <= i
    # -----------------------------------------------------------------------
    for i in range(1, len(count)):
        count[i] += count[i - 1]

    # -----------------------------------------------------------------------
    # ФАЗА 3: Устойчивая расстановка элементов в результирующий массив
    # КРИТИЧНО: обход строго с конца (reversed), чтобы обеспечить стабильность!
    # -----------------------------------------------------------------------
    res = [0] * len(a)
    for x in reversed(a):
        count[x] -= 1          # Декрементируем позицию для данного ключа
        res[count[x]] = x      # Записываем число на его точное законное место

    return res


def radix_sort_lsd(a: list[int]) -> list[int]:
    """Поразрядная сортировка (RadixSort LSD) целых неотрицательных чисел по основанию 10.

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      Сортирует числа по разрядам, начиная от самого младшего разряда (LSD — Least Significant
      Digit, единицы) к старшим (десятки, сотни, тысячи...).
      На каждом разряде применяется устойчивая сортировка подсчётом по текущей цифре.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ:
      1. Находим максимальное число `max_val`, чтобы определить число разрядов `d`.
      2. Переменная `exp` хранит текущий разряд (1 — единицы, 10 — десятки, 100 — сотни...).
      3. В цикле `while max_val // exp > 0:`:
         - Для каждого числа извлекаем текущую цифру: `digit = (x // exp) % 10`.
         - Сортируем массив устойчивым подсчётом (Counting Sort) по этой цифре (0..9).
         - Переходим к следующему разряду: `exp *= 10`.

    ⏱️ СЛОЖНОСТЬ:
      - Время: O(d * (n + b)), где d = ceil(log_b(max_val)) (число разрядов), b = 10 (основание).
        Для фиксированных чисел (например, 32-битных) d <= 10 — сложность линейна O(n)!
      - Память: O(n + b) (буферный массив O(n) + счётчик цифр O(b)).
      - Стабильность: строго СТАБИЛЬНА.

    ❗ ГЛАВНЫЙ ВОПРОС ЗАЩИТЫ (СПРОСИТ КАЖДЫЙ ПРЕПОДАВАТЕЛЬ!):
      - Вопрос: «Почему внутренний поразрядный проход ОБЯЗАН быть устойчивым (стабильным)?»
        Ответ: «Потому что перед началом сортировки по j-му разряду массив УЖЕ отсортирован
        по всем младшим разрядам (0 .. j-1). Если у двух чисел текущая цифра одинакова,
        их взаимный порядок должен определяться младшими цифрами! Если поразрядный проход
        нестабилен, он перемешает порядок равных по текущей цифре элементов и полностью
        уничтожит результат сортировки по всем предыдущим разрядам!»
    """
    if len(a) <= 1:
        return list(a)
    max_val = max(a)
    if max_val < 0:
        raise ValueError("radix_sort_lsd поддерживает только неотрицательные целые числа")
    if max_val == 0:
        return list(a)

    res = list(a)
    exp = 1       # Множитель текущего разряда: 1 (единицы), 10 (десятки), 100 (сотни)...
    base = 10     # Основание системы счисления (десятичная система: цифры 0..9)

    # Цикл продолжается, пока в максимальном числе есть необработанные разряды
    while max_val // exp > 0:
        # Внутренний проход: устойчивая сортировка подсчётом по текущей цифре (x // exp) % base
        count = [0] * base

        # Шаг 1: считаем, сколько раз встречается каждая цифра (0..9) в текущем разряде
        for x in res:
            digit = (x // exp) % base
            count[digit] += 1

        # Шаг 2: вычисляем префиксные суммы по массиву счётчиков цифр
        for i in range(1, base):
            count[i] += count[i - 1]

        # Шаг 3: устойчивая расстановка чисел с конца (reversed)
        out = [0] * len(res)
        for x in reversed(res):
            digit = (x // exp) % base
            count[digit] -= 1
            out[count[digit]] = x

        # Переносим результат прохода в res и переходим к следующему старшему разряду
        res = out
        exp *= base

    return res


def sift_down(a: list[int], i: int, n: int) -> None:
    """Просейка вниз (sift down) элемента с индексом i в max-куче a[0 .. n-1] на месте.

    📌 ЧТО ДЕЛАЕТ ПРОЦЕДУРА:
      Восстанавливает основное свойство двоичной max-кучи (родитель >= обоих детей)
      для вершины `i`, предполагая, что поддеревья её левого и правого потомков
      уже являются корректными кучами.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ:
      1. Узел `i` имеет двух детей в плоском массиве:
         - левый потомок: `left = 2 * i + 1`
         - правый потомок: `right = 2 * i + 2`
      2. Находим максимальный элемент среди вершины `i` и её существующих детей.
      3. Если наибольшим оказался ребенок (`largest != i`):
         меняем местами родителя и ребенка `a[i], a[largest] = a[largest], a[i]`,
         переходим на позицию ребенка `i = largest` и продолжаем спуск вниз.
      4. Если родитель больше обоих детей — свойство кучи выполнено, завершаем работу (`break`).

    ⏱️ СЛОЖНОСТЬ:
      - Время: O(log n) (высота спуска не превышает высоту кучи log2 n).
      - Память: O(1) (выполняется строго на месте, in-place).
    """
    while True:
        left = 2 * i + 1    # Индекс левого потомка в массиве
        right = 2 * i + 2   # Индекс правого потомка в массиве
        largest = i         # Предполагаем, что родитель i является наибольшим

        # Проверяем, существует ли левый потомок и больше ли он текущего максимума
        if left < n and a[left] > a[largest]:
            largest = left

        # Проверяем, существует ли правый потомок и больше ли он текущего максимума
        if right < n and a[right] > a[largest]:
            largest = right

        # Если один из детей оказался больше родителя — меняем и продолжаем спуск
        if largest != i:
            a[i], a[largest] = a[largest], a[i]
            i = largest  # Спускаемся на уровень ниже
        else:
            # Родитель больше или равен обоим детям: свойство кучи восстановлено!
            break


def heap_sort(a: list[int]) -> None:
    """Пирамидальная сортировка (HeapSort) in-place: сортирует переданный список на месте.

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      Использует структуру данных «двоичная max-куча», размещённую прямо в массиве без
      указателей. Сначала превращает исходный массив в max-кучу (в корне a[0] оказывается
      максимальный элемент). Затем поочерёдно меняет максимум с последним элементом
      и просеивает новый корень вниз, отрезая упорядоченный суффикс.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ (2 ФАЗЫ):
      1. Фаза построения max-кучи (Heapify) снизу вверх за O(n):
         Листья дерева (узлы от n//2 до n-1) просеивать не нужно — они уже кучи из 1 узла.
         Идём от последнего внутреннего узла `(n - 2) // 2` вниз до корня `0`:
         для каждого узла вызываем `sift_down(a, i, n)`.
      2. Фаза извлечения максимумов за O(n log n):
         В цикле `end` от `n - 1` вниз до 1:
           - Корень `a[0]` (текущий максимум) меняем с последним элементом неотсортированной
             части `a[end]`: теперь максимум стоит на своём окончательном месте!
           - Восстанавливаем кучу в сузившемся окне `a[0 .. end-1]`, просеивая корень:
             `sift_down(a, 0, end)`.

    ⏱️ СЛОЖНОСТЬ:
      - Время: СТРОГО Theta(n log n) в лучшем, среднем и худшем случаях!
      - Память: строго O(1) дополнительной памяти (строго in-place).
      - Стабильность: НЕ СТАБИЛЬНА! Дальние обмены `a[0]` с `a[end]` перебрасывают элементы
        через весь массив и нарушают взаимный порядок равных ключей.

    🎓 ШПАРГАЛКА ДЛЯ ОТВЕТА НА ЗАЩИТЕ:
      - Вопрос: «Почему фаза построения кучи работает за O(n), а не за O(n log n)?»
        Ответ: «Потому что большинство узлов кучи находятся на нижних уровнях: n/2 листьев
        вообще не требуют спуска (высота 0), n/4 узлов имеют высоту 1, n/8 высоту 2 и т.д.
        Сумма высот всех узлов даёт сходящийся ряд n * sum(h / 2^h) = 2*n = O(n)».
      - Вопрос: «Почему HeapSort на практике работает медленнее QuickSort при одинаковом O(n log n)?»
        Ответ: «Из-за плохой пространственной локальности ссылок (кэш-промахи процессора).
        В QuickSort память читается последовательно слева направо. В HeapSort узлы скачут по
        индексам 2*i + 1, постоянно обращаясь к разным нелокальным областям оперативной памяти,
        что вызывает частые промахи L1/L2 кэша».
    """
    n = len(a)
    if n <= 1:
        return

    # -----------------------------------------------------------------------
    # ФАЗА 1: Построение max-кучи снизу вверх за строго линейное время O(n)
    # Начинаем с последнего нелистового узла (родителя последнего элемента a[n-1])
    # -----------------------------------------------------------------------
    for i in range((n - 2) // 2, -1, -1):
        sift_down(a, i, n)

    # -----------------------------------------------------------------------
    # ФАЗА 2: Последовательное извлечение максимумов в конец массива за O(n log n)
    # -----------------------------------------------------------------------
    for end in range(n - 1, 0, -1):
        # Максимальный элемент a[0] переносим в конец активного окна a[end]
        a[0], a[end] = a[end], a[0]
        # Просеиваем новый корень вниз в уменьшенном окне длины end
        sift_down(a, 0, end)


def quick_sort(a: list[int], rng: random.Random | None = None) -> list[int]:
    """QuickSort с рандомизацией и 3-way partition (перенесено из ЛР 3).

    Сложность: O(n log n) в среднем на любых входах; O(n) на массивах равных ключей.
    Память: O(log n) глубина стека подзадач.
    Стабильность: НЕ стабильна.
    """
    if rng is None:
        rng = random.Random(42)

    res = list(a)
    n = len(res)
    if n <= 1:
        return res

    stack: list[tuple[int, int]] = [(0, n)]

    while stack:
        lo, hi = stack.pop()
        if hi - lo <= 1:
            continue

        pivot_idx = rng.randrange(lo, hi)
        pivot_val = res[pivot_idx]

        lt = lo
        i = lo
        gt = hi - 1

        while i <= gt:
            if res[i] < pivot_val:
                res[lt], res[i] = res[i], res[lt]
                lt += 1
                i += 1
            elif res[i] > pivot_val:
                res[i], res[gt] = res[gt], res[i]
                gt -= 1
            else:
                i += 1

        left_len = lt - lo
        right_len = hi - (gt + 1)

        # Ограничение глубины стека: сначала больший отрезок, затем меньший
        if left_len < right_len:
            if right_len > 1:
                stack.append((gt + 1, hi))
            if left_len > 1:
                stack.append((lo, lt))
        else:
            if left_len > 1:
                stack.append((lo, lt))
            if right_len > 1:
                stack.append((gt + 1, hi))

    return res


# ---------------------------------------------------------------------------
# 2. Верификация: инварианты + сверка с эталоном sorted()
#    (шаги 1–3 методики docs/ai-verification.md)
# ---------------------------------------------------------------------------


class SelfCheckError(Exception):
    """Нарушен контракт или инвариант реализации."""


def expect(condition: bool, message: str) -> None:
    """Явная проверка вместо assert: assert-ы исчезают при запуске python -O."""
    if not condition:
        raise SelfCheckError(message)


def heap_sorted(a: list[int]) -> list[int]:
    """heap_sort сортирует на месте: проверяется копия переданного списка."""
    buf = list(a)
    heap_sort(buf)
    return buf


# Реестр тестируемых сортировок
SORTS = {
    "merge_sort": lambda a: merge_sort(a),
    "counting_sort": lambda a: counting_sort(a, key_max=999),
    "radix_sort_lsd": lambda a: radix_sort_lsd(a),
    "heap_sort": lambda a: heap_sorted(a),
    "quick_sort": lambda a: quick_sort(a),
}


def check_sort(fn) -> None:
    """Граничные случаи, инварианты сортировки и сверка с эталоном sorted()."""
    boundary = [
        [],                    # Пустой массив
        [7],                   # Массив из одного элемента
        [0],                   # Нулевой ключ
        [5, 5, 5],             # Все элементы одинаковые
        [1, 2, 3, 4, 5],       # Уже отсортирован
        [5, 4, 3, 2, 1],       # Обратный порядок
    ]
    for a in boundary:
        res = fn(list(a))
        expect(isinstance(res, list), f"на {a} возвращён {type(res).__name__}, а не список")
        expect(res == sorted(a), f"на {a} получено {res}, ожидалось {sorted(a)}")

    # Случайные тесты: инвариант перестановки + сверка с эталоном
    rng = random.Random(0)
    for _ in range(200):
        a = [rng.randint(0, 999) for _ in range(rng.randint(0, 60))]
        res = fn(list(a))
        expect(sorted(res) == sorted(a), f"не перестановка входа {a}: получено {res}")
        expect(res == sorted(a), f"расходится с sorted() на {a}: получено {res}")


def check_merge_stability() -> None:
    """Стабильность слияния на парах (ключ, порядковый номер)."""
    rng = random.Random(0)
    pairs = [(rng.randint(0, 5), i) for i in range(100)]
    got = merge_sort(pairs, key=lambda p: p[0])
    expect(got == sorted(pairs, key=lambda p: p[0]),
           "merge_sort нестабилен: при равных ключах нарушен исходный порядок номеров")


def check_heap_property() -> None:
    """Проверка свойства max-кучи (a[i] >= a[2*i+1], a[i] >= a[2*i+2]) после фазы построения."""
    rng = random.Random(42)
    for size in [0, 1, 2, 3, 7, 15, 31, 100]:
        a = [rng.randint(-1000, 1000) for _ in range(size)]
        n = len(a)
        # Фаза 1 HeapSort: построение max-кучи за O(n)
        for i in range((n - 2) // 2, -1, -1):
            sift_down(a, i, n)
        # Проверка свойства кучи для каждого внутреннего узла
        for i in range(n):
            left = 2 * i + 1
            right = 2 * i + 2
            if left < n:
                expect(a[i] >= a[left],
                       f"Нарушено свойство кучи: a[{i}]={a[i]} < a[{left}]={a[left]}")
            if right < n:
                expect(a[i] >= a[right],
                       f"Нарушено свойство кучи: a[{i}]={a[i]} < a[{right}]={a[right]}")


def check_radix_stability() -> None:
    """Проверка корректности RadixSort и доказательство обязательности устойчивости поразрядного прохода."""
    rng = random.Random(123)
    for _ in range(50):
        data = [rng.randint(0, 99_999) for _ in range(40)]
        res = radix_sort_lsd(data)
        expect(res == sorted(data), f"RadixSort LSD ошибся на {data}")

    # Демонстрация: неустойчивый прямой проход расстановки ломает сортировку LSD
    def unstable_digit_pass(arr: list[int], exp: int) -> list[int]:
        count = [0] * 10
        for x in arr:
            count[(x // exp) % 10] += 1
        for i in range(1, 10):
            count[i] += count[i - 1]
        out = [0] * len(arr)
        for x in arr:  # прямой порядок обхода нарушает устойчивость
            d = (x // exp) % 10
            count[d] -= 1
            out[count[d]] = x
        return out

    sample = [21, 12, 11]
    p1 = unstable_digit_pass(sample, 1)
    p2 = unstable_digit_pass(p1, 10)
    expect(p2 != sorted(sample),
           "Неустойчивый проход должен приводить к ошибке сортировки")


def check_counting_stability() -> None:
    """Проверка стабильности сортировки подсчётом с обратным проходом на парах (ключ, метка)."""
    rng = random.Random(42)
    pairs = [(rng.randint(0, 5), i) for i in range(100)]
    key_max = 5
    count = [0] * (key_max + 1)
    for k, _ in pairs:
        count[k] += 1
    for i in range(1, len(count)):
        count[i] += count[i - 1]
    res = [None] * len(pairs)
    for pair in reversed(pairs):
        k = pair[0]
        count[k] -= 1
        res[count[k]] = pair
    expect(res == sorted(pairs, key=lambda p: p[0]),
           "counting_sort на парах нарушил относительный порядок равных ключей")


def self_check() -> None:
    """Все проверки по разделам; при любой ошибке замеры не выполняются."""
    checks = [(name, lambda fn=fn: check_sort(fn)) for name, fn in SORTS.items()]
    checks.append(("стабильность merge_sort", check_merge_stability))
    checks.append(("свойство max-кучи (heapify)", check_heap_property))
    checks.append(("устойчивость поразрядного прохода radix", check_radix_stability))
    checks.append(("стабильность counting_sort", check_counting_stability))
    failed = 0
    print("self_check:")
    for name, check in checks:
        try:
            check()
        except NotImplementedError as err:
            where = traceback.extract_tb(err.__traceback__)[-1].name
            print(f"  {name}: не реализовано — {where} (TODO)")
            failed += 1
        except SelfCheckError as err:
            print(f"  {name}: ОШИБКА — {err}")
            failed += 1
        except Exception:  # noqa: BLE001 — падение реализации тоже результат проверки
            print(f"  {name}: ИСКЛЮЧЕНИЕ")
            traceback.print_exc(file=sys.stdout)
            failed += 1
        else:
            print(f"  {name}: OK")

    if failed:
        raise SystemExit(f"self_check: не пройдено разделов — {failed}; "
                         f"замеры выполняются только после всех проверок.")
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 3. Бенчмарк (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES = [1_000, 3_000, 10_000, 30_000, 100_000]
REPEATS = 5
SMALL_KEY_MAX = 100        # Узкий диапазон: counting уместен
WIDE_KEY_MAX = 10**9       # Широкий диапазон: counting теряет смысл


def make_datasets(rng: random.Random, n: int) -> dict[str, list[int]]:
    """Массивы пяти распределений и диапазонов ключей для размера n."""
    almost = list(range(n))
    for _ in range(max(1, n // 100)):  # ~1 % случайных обменов
        i, j = rng.randrange(n), rng.randrange(n)
        almost[i], almost[j] = almost[j], almost[i]
    return {
        "random_wide": [rng.randint(0, WIDE_KEY_MAX) for _ in range(n)],
        "random_small": [rng.randint(0, SMALL_KEY_MAX) for _ in range(n)],
        "sorted": list(range(n)),
        "reversed": list(range(n, 0, -1)),
        "almost_sorted": almost,
    }


def bench(fn, data: list[int]) -> float:
    """Медиана времени fn на копии data по REPEATS запускам, с прогревом."""
    fn(list(data))  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        buf = list(data)
        t0 = time.perf_counter()
        fn(buf)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def find_output_dir(explicit: Path | None = None) -> Path:
    """Определение целевой директории для графиков."""
    if explicit is not None:
        explicit.mkdir(parents=True, exist_ok=True)
        return explicit
    for candidate in [
        Path("reports/images"),
        Path("../reports/images"),
        Path("../../reports/images"),
    ]:
        if candidate.parent.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
    fallback = Path("reports/images")
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def log_log_slope(points: list[tuple[int, float]]) -> float:
    """Оценка эмпирического порядка роста k в t(n) ~ c * n^k методом МНК в осях log10-log10."""
    valid = [(math.log10(n), math.log10(t)) for n, t in points if t > 0]
    if len(valid) < 2:
        return 0.0
    xs = [x for x, y in valid]
    ys = [y for x, y in valid]
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    numer = sum((x - x_mean) * (y - y_mean) for x, y in valid)
    return numer / denom


def plot_benchmarks(
    times_data: dict[str, dict[str, list[tuple[int, float]]]],
    out_dir: Path,
) -> None:
    """Построение log-log графиков для каждого распределения и сравнительных графиков."""
    out_dir.mkdir(parents=True, exist_ok=True)

    styles = {
        "merge_sort": {"color": "#1f77b4", "marker": "o", "label": "MergeSort"},
        "counting_sort": {"color": "#2ca02c", "marker": "s", "label": "CountingSort"},
        "radix_sort_lsd": {"color": "#d62728", "marker": "^", "label": "RadixSort LSD"},
        "heap_sort": {"color": "#9467bd", "marker": "D", "label": "HeapSort"},
        "quick_sort (ЛР 3)": {"color": "#ff7f0e", "marker": "v", "label": "QuickSort (ЛР 3)"},
        "sorted() (эталон)": {"color": "#7f7f7f", "marker": "x", "label": "sorted() (Timsort)"},
    }

    dist_titles = {
        "random_wide": "Случайный широкий (k = 10^9)",
        "random_small": "Случайный узкий (k = 100)",
        "sorted": "Упорядоченный",
        "reversed": "Обратно упорядоченный",
        "almost_sorted": "Почти упорядоченный (~1% перестановок)",
    }

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    axes_flat = axes.flatten()

    for idx, dist_name in enumerate(dist_titles.keys()):
        ax = axes_flat[idx]
        title = dist_titles[dist_name]
        for algo_name, style in styles.items():
            pts = times_data[dist_name].get(algo_name, [])
            if not pts:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            slope = log_log_slope(pts)
            ax.plot(
                xs,
                ys,
                color=style["color"],
                marker=style["marker"],
                linewidth=1.8,
                markersize=6,
                label=f"{style['label']} (k≈{slope:.2f})",
            )

        ref_n = SIZES
        if times_data[dist_name].get("sorted() (эталон)"):
            c_lin = times_data[dist_name]["sorted() (эталон)"][0][1] / ref_n[0]
            ref_lin = [c_lin * n for n in ref_n]
            ax.plot(ref_n, ref_lin, "k:", alpha=0.45, label="Теория O(n)")

        if times_data[dist_name].get("merge_sort"):
            c_nlogn = times_data[dist_name]["merge_sort"][-1][1] / (ref_n[-1] * math.log2(ref_n[-1]))
            ref_nlogn = [c_nlogn * n * math.log2(n) for n in ref_n]
            ax.plot(ref_n, ref_nlogn, "k--", alpha=0.55, label="Теория O(n log n)")

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Размер массива n", fontsize=10)
        ax.set_ylabel("Время t, с (медиана)", fontsize=10)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
        ax.legend(fontsize=8, loc="upper left")

    ax_summary = axes_flat[5]
    ax_summary.axis("off")
    summary_text = (
        "Сводка теоретических оценок:\n"
        "────────────────────────────────────────────\n"
        "• MergeSort:  O(n log n) время, O(n) память, стабилен\n"
        "• Counting:   O(n + k) время, O(k) память, стабилен\n"
        "• Radix LSD:  O(d·(n+b)) время, O(n+b) память, стабилен\n"
        "• HeapSort:   O(n log n) время, O(1) память, НЕ стабилен\n"
        "• QuickSort:  O(n log n) время, O(log n) память, НЕ стабилен\n"
        "• Timsort:    O(n log n) / O(n), O(n) память, стабилен\n"
        "────────────────────────────────────────────\n"
        "Особенности поведения:\n"
        "1. CountingSort пропущен на random_wide из-за\n"
        "   нехватки памяти под k = 10^9 счётчиков (~8 ГБ).\n"
        "2. Timsort демонстрирует O(n) на отсортированных\n"
        "   и почти упорядоченных массивах.\n"
        "3. HeapSort уступает QuickSort и MergeSort\n"
        "   по константе из-за частых кэш-промахов (L1/L2)."
    )
    ax_summary.text(
        0.05,
        0.5,
        summary_text,
        fontsize=9.5,
        family="monospace",
        verticalalignment="center",
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#f8f9fa", edgecolor="#ced4da"),
    )

    fig.suptitle(
        "ЛР 4: Сравнение алгоритмов сортировки в осях log-log (вариант 21, seed=51)",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )
    fig.tight_layout()
    plot_path1 = out_dir / "lab04_sorts_loglog.png"
    fig.savefig(plot_path1, dpi=160)
    plt.close(fig)

    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    for algo_name, style in styles.items():
        pts = times_data["random_small"].get(algo_name, [])
        if pts:
            ax1.plot(
                [p[0] for p in pts],
                [p[1] for p in pts],
                color=style["color"],
                marker=style["marker"],
                linewidth=2,
                label=style["label"],
            )
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Размер массива n", fontsize=11)
    ax1.set_ylabel("Время t, с", fontsize=11)
    ax1.set_title("Узкий диапазон ключей k = 100 (random_small)", fontsize=12, fontweight="bold")
    ax1.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
    ax1.legend(fontsize=9)

    for algo_name, style in styles.items():
        pts = times_data["random_wide"].get(algo_name, [])
        if pts:
            ax2.plot(
                [p[0] for p in pts],
                [p[1] for p in pts],
                color=style["color"],
                marker=style["marker"],
                linewidth=2,
                label=style["label"],
            )
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Размер массива n", fontsize=11)
    ax2.set_ylabel("Время t, с", fontsize=11)
    ax2.set_title("Широкий диапазон ключей k = 10^9 (random_wide)", fontsize=12, fontweight="bold")
    ax2.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
    ax2.legend(fontsize=9)

    fig2.suptitle(
        "Границы применимости: узкий диапазон (k=100) против широкого диапазона (k=10^9)",
        fontsize=13,
        fontweight="bold",
    )
    fig2.tight_layout()
    plot_path2 = out_dir / "lab04_linear_vs_comparison.png"
    fig2.savefig(plot_path2, dpi=160)
    plt.close(fig2)

    print(f"\nГрафики успешно сохранены:\n  1. {plot_path1}\n  2. {plot_path2}")


def run_benchmarks(seed: int, out_dir: Path | None = None) -> None:
    out_dir_resolved = find_output_dir(out_dir)
    rng = random.Random(seed)
    algorithms = [
        ("merge_sort", merge_sort),
        ("counting_sort", lambda a: counting_sort(a, key_max=max(a, default=0))),
        ("radix_sort_lsd", radix_sort_lsd),
        ("heap_sort", heap_sort),
        ("quick_sort (ЛР 3)", quick_sort),
        ("sorted() (эталон)", sorted),
    ]

    distributions = ["random_wide", "random_small", "sorted", "reversed", "almost_sorted"]
    times_data: dict[str, dict[str, list[tuple[int, float]]]] = {
        dist: {algo[0]: [] for algo in algorithms} for dist in distributions
    }

    print("\n" + "=" * 80)
    print("ЭМПИРИЧЕСКИЕ ЗАМЕРЫ ВРЕМЕНИ (В СЕКУНДАХ)")
    print("=" * 80)

    for n in SIZES:
        datasets = make_datasets(rng, n)
        print(f"\nn = {n}:")
        for dist_name, data in datasets.items():
            print(f"  распределение {dist_name}:")
            for algo_name, fn in algorithms:
                if algo_name == "counting_sort" and dist_name == "random_wide":
                    print(f"    {algo_name:>18}: пропуск (диапазон ключей k = 10^9)")
                    continue
                t_med = bench(fn, data)
                times_data[dist_name][algo_name].append((n, t_med))
                print(f"    {algo_name:>18}: t = {t_med:.6f} c")

    # Сводная таблица наклонов log-log
    print("\n" + "=" * 90)
    print("ОЦЕНКА НАКЛОНА В ОСЯХ LOG-LOG (ЭКСПЕРИМЕНТАЛЬНЫЙ ПОРЯДОК РОСТА k)")
    print("=" * 90)
    header = f"{'Алгоритм':<20} | {'random_wide':<12} | {'random_small':<12} | {'sorted':<12} | {'reversed':<12} | {'almost_sorted':<13}"
    print(header)
    print("-" * 90)
    for algo_name, _ in algorithms:
        row = [f"{algo_name:<20}"]
        for dist_name in distributions:
            pts = times_data[dist_name].get(algo_name, [])
            if pts:
                slope = log_log_slope(pts)
                row.append(f"{slope:>12.3f}")
            else:
                row.append(f"{'пропуск':>12}")
        print(" | ".join(row))
    print("-" * 90)

    # Построение графиков
    plot_benchmarks(times_data, out_dir_resolved)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", type=int, required=True, help="номер варианта")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="каталог для сохранения графиков (по умолчанию reports/images)",
    )
    args = ap.parse_args()
    seed = 30 + args.variant
    random.seed(seed)
    self_check()
    run_benchmarks(seed, args.out)


if __name__ == "__main__":
    main()
