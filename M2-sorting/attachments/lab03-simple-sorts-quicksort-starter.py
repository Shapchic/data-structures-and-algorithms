#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 3. Простые сортировки (Bubble, Insertion, Selection) и QuickSort с рандомизацией.

=============================================================================
             ШПАРГАЛКА ДЛЯ ЗАЩИТЫ ЛАБОРАТОРНОЙ РАБОТЫ № 3
              (Памятка студента: читать при ответе на защите)
=============================================================================

1. СВОДНАЯ ТАБЛИЦА СВОЙСТВ АЛГОРИТМОВ:
┌─────────────────┬───────────────────┬──────────────┬──────────────┬──────────────┬────────────┬───────────┬───────────┐
│ Алгоритм        │ Принцип / Идея    │ Лучшее время │ Среднее время│ Худшее время │ Доп. память│ Стабилен? │ In-place? │
├─────────────────┼───────────────────┼──────────────┼──────────────┼──────────────┼────────────┼───────────┼───────────┤
│ Bubble Sort     │ Всплытие максимума│ Theta(n)     │ Theta(n^2)   │ Theta(n^2)   │ O(1)       │   ДА      │   ДА      │
│ Insertion Sort  │ Карты в руке      │ Theta(n)     │ Theta(n^2)   │ Theta(n^2)   │ O(1)       │   ДА      │   ДА      │
│ Selection Sort  │ Поиск минимума    │ Theta(n^2)   │ Theta(n^2)   │ Theta(n^2)   │ O(1)       │   НЕТ     │   ДА      │
│ QuickSort       │ Разделяй и властв.│Theta(n log n)│Theta(n log n)│ O(n^2)*      │ O(log n)   │   НЕТ     │   ДА      │
└─────────────────┴───────────────────┴──────────────┴──────────────┴──────────────┴────────────┴───────────┴───────────┘
 * Примечание: худший случай QuickSort при рандомизации практически невозможен (вероятность <= 2^n / n!).
   На массивах из одинаковых ключей благодаря 3-way partition работает за строго Theta(n).

2. ТЕРМИНЫ, КОТОРЫЕ СПРОСИТ ПРЕПОДАВАТЕЛЬ:
 - Стабильность (Stability): сохранение исходного относительного порядка элементов с равными ключами.
 - In-place (сортировка на месте): требует O(1) (или O(log n) для стека) вспомогательной памяти.
 - Адаптивность: алгоритм работает быстрее (вплоть до O(n)), если вход частично или полностью упорядочен.
 - Информационно-теоретическая нижняя граница: любой алгоритм сортировки на основе попарных
   сравнений в худшем и среднем случаях требует Omega(n log n) сравнений (доказательство через
   бинарное дерево решений с n! листьями: h >= log2(n!) = Omega(n log n)).

Запуск:
    python lab03-simple-sorts-quicksort-starter.py --variant 21
"""
from __future__ import annotations

import argparse
import collections
import math
import os
import random
import statistics
import time
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 1. Простые сортировки со счётчиками операций
#    Каждая функция сортирует КОПИЮ переданного списка (не мутирует исходный)
#    и возвращает кортеж: (отсортированный список, число сравнений, число перемещений).
# ---------------------------------------------------------------------------


def bubble_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка пузырьком (Bubble Sort) с оптимизацией досрочного выхода.

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      Многократно проходит по массиву слева направо. На каждом шаге сравнивает
      соседние элементы `res[j]` и `res[j+1]`. Если левый больше правого — они
      меняются местами. За счёт этого максимальный элемент за один проход
      гарантированно «всплывает» в самый конец массива, подобно пузырьку воздуха в воде.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ:
      1. Запускается внешний цикл `i` от 0 до `n-1` (счётчик завершённых проходов).
      2. В начале каждого прохода ставится флаг `swapped = False`.
      3. Внутренний цикл `j` идёт от 0 до `n - 1 - i`. Мы вычитаем `i`, потому что
         последние `i` элементов уже стоят на своих финальных местах и их проверять не нужно.
      4. Сравниваются пары: `if kfn(res[j]) > kfn(res[j + 1]):`.
      5. При нарушении порядка элементы меняются местами, увеличивается счётчик `swaps += 1`
         и выставляется `swapped = True`.
      6. Досрочный выход: если за весь проход не произошло ни одного обмена (`not swapped`),
         значит массив уже упорядочен, и мы немедленно прерываем цикл через `break`.

    ⏱️ СЛОЖНОСТЬ:
      - Лучший случай (уже отсортирован): Theta(n) по времени.
        Делает ровно 1 проход (n - 1 сравнений) и 0 обменов благодаря флагу `swapped`.
      - Средний случай (случайный массив): Theta(n^2) по времени.
        В среднем ~ n^2 / 2 сравнений и ~ n^2 / 4 обменов.
      - Худший случай (обратный порядок): Theta(n^2) по времени.
        Ровно n*(n-1)/2 сравнений и столько же обменов (максимум инверсий).
      - Память: O(1) вспомогательной памяти сверх копии списка.
      - Стабильность: СТАБИЛЬНА (строгое неравенство `>` не меняет порядок равных ключей).

    🎓 ШПАРГАЛКА ДЛЯ ОТВЕТА НА ЗАЩИТЕ:
      - Вопрос: «Зачем нужен флаг swapped?»
        Ответ: «Для оптимизации досрочного выхода. На уже отсортированном массиве он
        позволяет завершить работу за O(n) после первого же прохода, сделав ровно n-1 сравнений».
      - Вопрос: «Почему внутренний цикл идёт до n - 1 - i?»
        Ответ: «Потому что после каждого i-го прохода i наибольших элементов гарантированно
        оказываются в конце массива на своих правильных местах, и повторно их смотреть нет смысла».
    """
    # Создаём независимую копию списка, чтобы не модифицировать входной массив вызывающего кода
    res = list(a)
    n = len(res)

    # Инициализация счётчиков элементарных операций
    comparisons = 0  # Счётчик сравнений ключей элементов
    swaps = 0        # Счётчик перестановок (обменов) элементов местами

    # Функция извлечения ключа сравнения (если не задана — сравниваем сами элементы)
    kfn = key if key is not None else (lambda x: x)

    # ВНЕШНИЙ ЦИКЛ: количество проходов по массиву (максимум n проходов)
    for i in range(n):
        # Флаг досрочного выхода: отслеживает, был ли хотя бы один обмен на текущем проходе
        swapped = False

        # ВНУТРЕННИЙ ЦИКЛ: попарное сравнение соседних элементов
        # Верхняя граница (n - 1 - i): последние i элементов уже встали на свои места!
        for j in range(n - 1 - i):
            # Фиксируем операцию сравнения ключей двух соседних элементов
            comparisons += 1

            # Проверяем условие инверсии: левый элемент строго больше правого
            # СТРОГОЕ '>' критично для стабильности: равные ключи не трогаем!
            if kfn(res[j]) > kfn(res[j + 1]):
                # Меняем соседние элементы местами
                res[j], res[j + 1] = res[j + 1], res[j]
                swaps += 1        # Увеличиваем счётчик выполненных обменов
                swapped = True    # Отмечаем, что массив ещё не был полностью отсортирован

        # ОПТИМИЗАЦИЯ ДОСРОЧНОГО ВЫХОДА:
        # Если за весь проход по массиву не случилось ни одного обмена,
        # значит, каждый элемент меньше или равен своему соседу справа — массив отсортирован!
        if not swapped:
            break

    # Возвращаем отсортированную копию и показания счётчиков
    return res, comparisons, swaps


def insertion_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка вставками (Insertion Sort).

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      Работает точно так же, как человек раскладывает карты в руке. Массив виртуально
      делится на две части: левая часть `res[0 .. i-1]` уже отсортирована, а правая
      `res[i .. n-1]` ещё нет. На каждом шаге берётся очередной элемент `res[i]`
      и «проталкивается» влево на своё правильное место среди уже отсортированных карт,
      сдвигая большие элементы вправо.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ:
      1. Начинаем со 2-го элемента (`i = 1`), так как один первый элемент (`res[0]`)
         тривиально уже образует отсортированный префикс длины 1.
      2. Запоминаем текущий вставляемый элемент в переменную `item = res[i]` (освобождаем ячейку).
      3. Идём указателем `j = i - 1` влево к началу массива.
      4. Сравниваем: если элемент левее строго больше нашего (`res[j] > item_key`),
         сдвигаем его вправо на одну ячейку: `res[j + 1] = res[j]`, увеличивая счётчик сдвигов `moves += 1`.
      5. Как только встретили элемент `<= item_key` (или дошли до начала массива `j < 0`),
         останавливаемся.
      6. Помещаем наш элемент в освободившуюся позицию: `res[j + 1] = item`.

    ⏱️ СЛОЖНОСТЬ:
      - Лучший случай (уже отсортирован): Theta(n) по времени.
        Ровно n - 1 сравнений и 0 сдвигов (внутренний цикл сразу прерывается на первом сравнении).
      - Средний случай: Theta(n^2) по времени (~ n^2 / 4 сравнений и сдвигов).
      - Худший случай (обратный порядок): Theta(n^2) по времени.
        Ровно n*(n-1)/2 сравнений и столько же сдвигов (каждый элемент сдвигает весь префикс).
      - Память: O(1) дополнительной памяти.
      - Стабильность: СТАБИЛЬНА (внутренний цикл останавливается при `res[j] <= item`,
        поэтому вставляемый элемент ставится ПОСЛЕ равных ему).

    🎓 ШПАРГАЛКА ДЛЯ ОТВЕТА НА ЗАЩИТЕ:
      - Вопрос: «Почему Insertion Sort на практике почти всегда быстрее Bubble Sort?»
        Ответ: «1) Вставка делает 1 сдвиг (присваивание res[j+1]=res[j]), удерживая вставляемый
        элемент в регистре, а пузырёк делает кортежный обмен двух ячеек памяти.
        2) Внутренний цикл вставок читает непрерывную память назад, что отлично укладывается
        в кэш процессора L1/L2 (высокая пространственная локальность)».
      - Вопрос: «Где применяется Insertion Sort на практике?»
        Ответ: «В гибридных алгоритмах Timsort (Python sorted) и IntroSort (C++ std::sort).
        Когда размер подмассива становится малым (<= 16-32 элементов), переключаются на
        вставки, так как у них нулевые накладные расходы на рекурсию и стек».
    """
    res = list(a)
    n = len(res)

    comparisons = 0  # Счётчик сравнений ключей
    moves = 0        # Счётчик сдвигов (перемещений) элементов вправо
    kfn = key if key is not None else (lambda x: x)

    # ВНЕШНИЙ ЦИКЛ: перебираем элементы начиная со второго (индекс 1)
    for i in range(1, n):
        # Сохраняем вставляемый элемент во временную переменную (как карту, вынутую из колоды)
        item = res[i]
        item_key = kfn(item)

        # j указывает на последний элемент уже отсортированного левого префикса
        j = i - 1

        # ВНУТРЕННИЙ ЦИКЛ: ищем позицию вставки, сдвигая большие элементы вправо
        while j >= 0:
            comparisons += 1
            # Если элемент левее больше вставляемого — сдвигаем его вправо
            if kfn(res[j]) > item_key:
                res[j + 1] = res[j]  # Сдвиг элемента вправо
                moves += 1           # Фиксируем перемещение ячейки
                j -= 1               # Шагаем дальше влево
            else:
                # Встретили элемент <= item_key: правильная позиция найдена!
                # Благодаря остановке на равных элементах сортировка СТАБИЛЬНА
                break

        # Вставляем наш элемент в освободившуюся позицию (j + 1)
        res[j + 1] = item

    return res, comparisons, moves


def selection_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка выбором (Selection Sort).

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      На каждом $i$-м шаге просматривает всю неотсортированную правую часть массива
      (`res[i .. n-1]`), находит в ней самый маленький (минимальный) элемент
      и меняет его местами с текущим элементом `res[i]`. В результате отсортированный
      префикс слева увеличивается на 1 элемент.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ:
      1. Внешний цикл `i` идёт от 0 до `n - 2`. На шаге `i` мы ищем претендента на позицию `i`.
      2. Изначально считаем, что минимум находится в текущей ячейке: `min_idx = i`.
      3. Внутренний цикл `j` просматривает все последующие ячейки от `i + 1` до `n - 1`.
      4. Если `res[j] < res[min_idx]`, обновляем индекс минимума: `min_idx = j`.
      5. После полного просмотра суффикса: если минимум оказался не на позиции `i`
         (`min_idx != i`), производим ОДИН обмен элементов: `res[i], res[min_idx] = res[min_idx], res[i]`.

    ⏱️ СЛОЖНОСТЬ:
      - Число сравнений: СТРОГО n*(n-1)/2 во ВСЕХ случаях (лучший, средний, худший)!
        Алгоритм неадаптивен: он всегда просматривает суффикс до конца независимо от входа.
      - Число обменов: не более n - 1 во всех случаях (минимум 0, максимум n - 1).
      - Память: O(1) дополнительной памяти.
      - Стабильность: НЕ СТАБИЛЬНА! Дальний обмен найденного минимума с `res[i]` перебрасывает
        элемент через равные ему ключи, нарушая их порядок.
        Контрпример: [(2, "a"), (2, "b"), (1, "c")] -> минимум (1, "c") меняется с (2, "a") ->
        получаем [(1, "c"), (2, "b"), (2, "a")] — ключи 2 поменялись местами!

    🎓 ШПАРГАЛКА ДЛЯ ОТВЕТА НА ЗАЩИТЕ:
      - Вопрос: «Почему число сравнений всегда строго n*(n-1)/2?»
        Ответ: «Потому что во внутреннем цикле for j in range(i + 1, n) нет никаких условий
        досрочного выхода. Минимум можно гарантированно найти только просмотрев весь суффикс целиком».
      - Вопрос: «В чём единственное достоинство Selection Sort?»
        Ответ: «Минимальное число записей в память: строго не более n - 1 обменов. Это важно
        для устройств с дорогой записью, например Flash-памяти или EEPROM с ограниченным числом циклов».
    """
    res = list(a)
    n = len(res)

    comparisons = 0  # Счётчик сравнений
    swaps = 0        # Счётчик обменов элементов
    kfn = key if key is not None else (lambda x: x)

    # ВНЕШНИЙ ЦИКЛ: позиция i, для которой мы сейчас ищем минимальный элемент
    for i in range(n - 1):
        # Предполагаем, что минимальный элемент находится на позиции i
        min_idx = i

        # ВНУТРЕННИЙ ЦИКЛ: полный просмотр суффикса массива от i + 1 до конца
        for j in range(i + 1, n):
            comparisons += 1
            # Если нашли элемент меньше текущего известного минимума — запоминаем его индекс
            if kfn(res[j]) < kfn(res[min_idx]):
                min_idx = j

        # Если минимальный элемент находится не на позиции i, меняем их местами
        if min_idx != i:
            res[i], res[min_idx] = res[min_idx], res[i]
            swaps += 1  # За один шаг внешнего цикла выполняется максимум 1 обмен!

    return res, comparisons, swaps


# ---------------------------------------------------------------------------
# 2. QuickSort с рандомизированным опорным элементом и 3-way partition
# ---------------------------------------------------------------------------


def quick_sort(
    a: list,
    rng: random.Random | None = None,
    key: Callable[[Any], Any] | None = None,
) -> list:
    """Быстрая сортировка (QuickSort) с рандомизацией и 3-way partition (Дейкстра).

    📌 ЧТО ДЕЛАЕТ АЛГОРИТМ (Суть простыми словами):
      Реализует принцип «Разделяй и властвуй». Случайным образом выбирает опорный
      элемент (pivot) и делит отрезок массива на три зоны:
        1) элементы строго меньше пивота;
        2) элементы равные пивоту (они уже встали на своё окончательное место!);
        3) элементы строго больше пивота.
      Затем алгоритм независимо упорядочивает левую (<) и правую (>) зоны.

    ⚙️ ПОШАГОВЫЙ ПРИНЦИП РАБОТЫ (Разбиение голландского флага Дейкстры):
      1. Отрезок [lo, hi) разбивается тремя указателями:
         - `lt` (less than): указывает на границу элементов, меньших пивота.
         - `i`: текущий рассматриваемый элемент.
         - `gt` (greater than): указывает на границу элементов, больших пивота.
      2. Инвариант трёхчастного разбиения:
         - `res[lo .. lt-1] < pivot`
         - `res[lt .. i-1] == pivot`
         - `res[i .. gt]` — ещё не просмотренные элементы
         - `res[gt+1 .. hi-1] > pivot`
      3. Правила перехода:
         - Если `res[i] < pivot`: меняем `res[lt]` и `res[i]`, сдвигаем `lt += 1`, `i += 1`.
         - Если `res[i] > pivot`: меняем `res[i]` и `res[gt]`, сдвигаем `gt -= 1`
           (внимание: `i` не увеличиваем, т.к. пришедший справа элемент ещё не проверен!).
         - Если `res[i] == pivot`: просто сдвигаем `i += 1`.
      4. Элементы из центральной зоны `res[lt .. gt]` РАВНЫ пивоту и больше в сортировке
         не участвуют! Это даёт время Theta(n) на массивах из одинаковых элементов.
      5. Управление стеком (Tail Call Optimization):
         - Вместо рекурсии используется явный стек `stack` (защита от RecursionError).
         - В стек ПЕРВЫМ кладётся БОЛЬШИЙ подмассив, а МЕНЬШИЙ обрабатывается сразу.
         - Это строго гарантирует, что глубина стека в памяти никогда не превысит O(log n)
           (для 100 000 элементов глубина стека не более 17 пар!).

    ⏱️ СЛОЖНОСТЬ:
      - В среднем: Theta(n log n) на любых распределениях данных.
      - На массиве из одинаковых элементов: строго Theta(n) благодаря 3-way partition.
      - Худший случай: O(n^2), но при случайном выборе пивота вероятность худшего случая
        экспоненциально мала (<= 2^n / n! ~ 10^-128 при n = 100).
      - Память: O(log n) для хранения границ отрезков в стеке.
      - Стабильность: НЕ СТАБИЛЬНА (дальние перестановки нарушают взаимный порядок равных ключей).

    🎓 ШПАРГАЛКА ДЛЯ ОТВЕТА НА ЗАЩИТЕ:
      - Вопрос: «Зачем нужна рандомизация опорного элемента?»
        Ответ: «Она лишает противника возможности подобрать плохой вход (например, уже отсортированный
        или обратно отсортированный массив), на котором детерминированный QuickSort с крайним
        пивотом вырождается в O(n^2). С рандомизацией матожидание времени работы O(n log n)
        гарантировано на АБСОЛЮТНО ЛЮБОМ входе».
      - Вопрос: «Зачем трёхчастное разбиение (3-way partition)?»
        Ответ: «Обычное разбиение Хоара/Ломуто на массиве из одинаковых элементов делит массив
        крайне неэффективно. 3-way partition Дейкстры собирает все равные пивоту элементы в центр
        за один проход и исключает их из рекурсии, обеспечивая время O(n)».
      - Вопрос: «Как вы защитились от переполнения стека (RecursionError)?»
        Ответ: «Рекурсия заменена итеративным стеком отрезков [lo, hi). При разбиении мы сначала
        кладём в стек больший отрезок, а меньший обрабатываем первым. Так как размер меньшего
        отрезка не превышает n/2, глубина стека строго ограничена ceil(log2 n) <= 17 при n=100 000».
    """
    if rng is None:
        rng = random.Random()

    res = list(a)
    n = len(res)
    # Базовый случай: массив из 0 или 1 элемента уже упорядочен
    if n <= 1:
        return res

    kfn = key if key is not None else (lambda x: x)

    # Итеративный стек отрезков [lo, hi).
    # Исключает системное переполнение стека вызовов Python (RecursionError).
    stack: list[tuple[int, int]] = [(0, n)]

    while stack:
        # Извлекаем границы очередного подмассива [lo, hi)
        lo, hi = stack.pop()

        # Базовый случай: подмассив из 0 или 1 элемента сортировать не нужно
        if hi - lo <= 1:
            continue

        # Рандомизированный выбор опорного элемента (pivot)
        pivot_idx = rng.randrange(lo, hi)
        pivot_val = res[pivot_idx]
        pivot_key = kfn(pivot_val)

        # -------------------------------------------------------------------
        # 3-частное разбиение (Dutch National Flag / флаг Дейкстры) на [lo, hi)
        # res[lo .. lt-1]   < pivot_key   (строго меньше опорного)
        # res[lt .. gt]     == pivot_key  (в точности равны опорному)
        # res[gt+1 .. hi-1] > pivot_key   (строго больше опорного)
        # -------------------------------------------------------------------
        lt = lo        # Указатель на начало блока равных элементов
        i = lo         # Текущий рассматриваемый элемент
        gt = hi - 1    # Указатель на конец непроверенного блока (граница больших элементов)

        while i <= gt:
            cur_key = kfn(res[i])
            if cur_key < pivot_key:
                # Элемент меньше опорного: меняем с res[lt] и сдвигаем оба указателя
                res[lt], res[i] = res[i], res[lt]
                lt += 1
                i += 1
            elif cur_key > pivot_key:
                # Элемент больше опорного: меняем с res[gt] и сдвигаем только gt
                # i НЕ увеличиваем, т.к. пришедший с позиции gt элемент ещё не проверен!
                res[i], res[gt] = res[gt], res[i]
                gt -= 1
            else:
                # Элемент равен опорному: оставляем на месте, просто шагаем дальше
                i += 1

        # -------------------------------------------------------------------
        # Оптимизация глубины стека (Tail Call Optimization):
        # Центральный блок res[lt .. gt] состоит из элементов == pivot_key.
        # Они уже заняли свои окончательные позиции и больше сортироваться не будут!
        # Сортировать нужно только два отрезка: левый [lo, lt) и правый [gt + 1, hi).
        # Чтобы глубина стека не превысила O(log n), сначала кладём в стек БОЛЬШИЙ
        # отрезок, а МЕНЬШИЙ обрабатываем следующим (он извлечётся первым через pop()).
        # -------------------------------------------------------------------
        left_len = lt - lo
        right_len = hi - (gt + 1)

        if left_len < right_len:
            # Правый отрезок больше: кладём его первым на дно стека
            if right_len > 1:
                stack.append((gt + 1, hi))
            if left_len > 1:
                stack.append((lo, lt))
        else:
            # Левый отрезок больше: кладём его первым на дно стека
            if left_len > 1:
                stack.append((lo, lt))
            if right_len > 1:
                stack.append((gt + 1, hi))

    return res


# ---------------------------------------------------------------------------
# 3. Демонстрация стабильности на парах (ключ, метка)
# ---------------------------------------------------------------------------


def stability_demo() -> dict[str, bool]:
    """Наглядная демонстрация стабильности алгоритмов сортировки на парах (ключ, метка).

    📌 ЧТО ТАКОЕ СТАБИЛЬНОСТЬ:
      Сортировка называется стабильной (устойчивой), если она сохраняет исходный
      относительный порядок элементов с одинаковыми ключами.

    ТЕСТОВЫЙ ПРИМЕР:
      Берём массив: [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
      Сортируем ТОЛЬКО по первому элементу (ключу p[0]).
      В стабильной сортировке:
        - для ключа 1: метка "b" обязана идти раньше "d" (порядок [("b"), ("d")]);
        - для ключа 2: метка "a" обязана идти раньше "c" (порядок [("a"), ("c")]).
      Ожидаемый результат стабильной сортировки:
        [(1, "b"), (1, "d"), (2, "a"), (2, "c")].
    """
    sample_pairs = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
    expected_order = [(1, "b"), (1, "d"), (2, "a"), (2, "c")]

    print("\n" + "=" * 65)
    print("ДЕМОНСТРАЦИЯ СТАБИЛЬНОСТИ АЛГОРИТМОВ СОРТИРОВКИ (ЛР 3)")
    print("=" * 65)
    print(f"Исходный массив пар (ключ, метка): {sample_pairs}")
    print(f"Ожидаемый порядок стабильной сортировки: {expected_order}\n")

    results: dict[str, bool] = {}

    algorithms = [
        ("Bubble Sort", lambda a: bubble_sort(a, key=lambda p: p[0])[0]),
        ("Insertion Sort", lambda a: insertion_sort(a, key=lambda p: p[0])[0]),
        ("Selection Sort", lambda a: selection_sort(a, key=lambda p: p[0])[0]),
        ("QuickSort", lambda a: quick_sort(a, rng=random.Random(1), key=lambda p: p[0])),
    ]

    for name, fn in algorithms:
        sorted_pairs = fn(sample_pairs)
        is_stable = sorted_pairs == expected_order
        results[name] = is_stable
        status = "СТАБИЛЬНА" if is_stable else "НЕ СТАБИЛЬНА"
        print(f"  {name:15s} -> {sorted_pairs}  [{status}]")

    print("\nПОЯСНЕНИЕ ДЛЯ ЗАЩИТЫ:")
    print("  - Bubble Sort и Insertion Sort перемещают только смежные элементы")
    print("    при СТРОГОМ нарушении порядка, поэтому они СТАБИЛЬНЫ.")
    print("  - Selection Sort и QuickSort совершают дальние перестановки через")
    print("    промежуточные элементы, поэтому они НЕ СТАБИЛЬНЫ.")
    print("=" * 65 + "\n")
    return results


# ---------------------------------------------------------------------------
# 4. Генерация классов входов по варианту (детерминированно по seed)
# ---------------------------------------------------------------------------


def make_inputs(n: int, seed: int) -> dict[str, list[int]]:
    """Генерация трёх классов входов размера n: упорядоченный, случайный, обратный.

    seed = 30 + variant (детерминированная воспроизводимость замеров).
    """
    rng = random.Random(seed + n)  # Свой изолированный поток для каждого размера
    data = [rng.randint(-1_000_000, 1_000_000) for _ in range(n)]
    return {
        "упорядоченный": sorted(data),
        "случайный": data,
        "обратный": sorted(data, reverse=True),
    }


# ---------------------------------------------------------------------------
# 5. Верификация инвариантов сортировок (docs/ai-verification.md)
# ---------------------------------------------------------------------------

ALGORITHMS = {
    "bubble_sort": lambda a: bubble_sort(a)[0],
    "insertion_sort": lambda a: insertion_sort(a)[0],
    "selection_sort": lambda a: selection_sort(a)[0],
    "quick_sort": lambda a: quick_sort(a, random.Random(0)),
}


def is_sorted(a: list) -> bool:
    """Инвариант 1: неубывающий порядок элементов."""
    return all(a[i] <= a[i + 1] for i in range(len(a) - 1))


def self_check() -> None:
    """Граничные случаи, строгие инварианты сортировки и сверка с эталоном sorted()."""
    boundary = [
        [],                    # Пустой массив
        [7],                   # Массив из одного элемента
        [5, 5, 5, 5],          # Все элементы одинаковые (мультимножество)
        [1, 2, 3, 4, 5],       # Уже отсортированный массив
        [5, 4, 3, 2, 1],       # Обратно отсортированный массив
    ]
    for name, fn in ALGORITHMS.items():
        for a in boundary:
            res = fn(list(a))
            assert is_sorted(res), f"{name}: нарушен порядок неубывания на {a}"
            assert sorted(res) == sorted(a), f"{name}: не является перестановкой входа {a}"

    # Сверка с эталоном из стандартной библиотеки на сотнях случайных входов
    rng = random.Random(0)
    for _ in range(300):
        a = [rng.randint(-100, 100) for _ in range(rng.randint(0, 80))]
        expected = sorted(a)
        for name, fn in ALGORITHMS.items():
            assert fn(list(a)) == expected, f"{name}: расходится с sorted() на {a}"

    # Счётчики: у сортировки выбором ровно n*(n-1)/2 сравнений на любом входе
    _, comparisons, _ = selection_sort([3, 1, 2, 5, 4])
    assert comparisons == 10, "selection_sort: неверный счётчик сравнений"

    # Дополнительные строгие проверки инвариантов
    # 1. Инвариант сохранения мультимножества: Counter(res) == Counter(a)
    for _ in range(50):
        a = [rng.randint(-50, 50) for _ in range(60)]
        for name, fn in ALGORITHMS.items():
            res = fn(list(a))
            assert collections.Counter(res) == collections.Counter(a), (
                f"{name}: нарушен инвариант мультимножества (потеряны или изменены элементы)"
            )

    # 2. Инвариант числа сравнений Selection Sort: строго n*(n-1)//2 на любом входе
    for n_test in (1, 2, 5, 10, 20):
        expected_cmp = n_test * (n_test - 1) // 2
        for test_arr in (
            list(range(n_test)),
            list(range(n_test, 0, -1)),
            [42] * n_test,
            [rng.randint(0, 100) for _ in range(n_test)],
        ):
            _, c, _ = selection_sort(test_arr)
            assert c == expected_cmp, f"selection_sort: сравнений {c} != {expected_cmp} на n={n_test}"

    # 3. Инвариант лучшего случая Bubble Sort и Insertion Sort на отсортированном входе:
    # ровно n - 1 сравнений и 0 обменов / сдвигов
    for n_test in (2, 5, 10, 30):
        sorted_arr = list(range(n_test))
        _, b_cmp, b_swp = bubble_sort(sorted_arr)
        assert b_cmp == n_test - 1, f"bubble_sort: сравнений {b_cmp} != {n_test - 1}"
        assert b_swp == 0, f"bubble_sort: обменов {b_swp} != 0 на упорядоченном массиве"

        _, i_cmp, i_mov = insertion_sort(sorted_arr)
        assert i_cmp == n_test - 1, f"insertion_sort: сравнений {i_cmp} != {n_test - 1}"
        assert i_mov == 0, f"insertion_sort: сдвигов {i_mov} != 0 на упорядоченном массиве"

    # 4. Инвариант худшего случая Bubble Sort и Insertion Sort на обратном массиве без дубликатов:
    # ровно n*(n-1)//2 сравнений и перемещений
    for n_test in (2, 5, 10, 20):
        rev_arr = list(range(n_test, 0, -1))
        expected_worst = n_test * (n_test - 1) // 2
        _, b_cmp, b_swp = bubble_sort(rev_arr)
        assert b_cmp == expected_worst and b_swp == expected_worst, (
            f"bubble_sort худший случай: cmp={b_cmp}, swp={b_swp}, exp={expected_worst}"
        )

        _, i_cmp, i_mov = insertion_sort(rev_arr)
        assert i_cmp == expected_worst and i_mov == expected_worst, (
            f"insertion_sort худший случай: cmp={i_cmp}, mov={i_mov}, exp={expected_worst}"
        )

    print("self_check: OK (все инварианты, граничные случаи и сверка с sorted() пройдены)")


# ---------------------------------------------------------------------------
# 6. Бенчмарк (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES_QUADRATIC = [500, 1_000, 2_000, 4_000, 8_000]     # для простых квадратичных сортировок
SIZES_QUICK = [1_000, 3_000, 10_000, 30_000, 100_000]   # для QuickSort
REPEATS = 5


def bench(fn: Callable[[list], Any], data: list) -> float:
    """Медиана времени выполнения fn(копия data) по REPEATS запускам, с прогревом."""
    fn(list(data))  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        arg = list(data)  # свежая копия: сортировка не должна получать свой результат
        t0 = time.perf_counter()
        fn(arg)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def log_log_slope(points: list[tuple[int, float]]) -> float:
    """Наклон прямой в осях (log n, log t) методом МНК — оценка показателя степени роста."""
    valid = [(n, t) for n, t in points if t > 0]
    if len(valid) < 2:
        return 0.0
    xs = [math.log10(n) for n, _ in valid]
    ys = [math.log10(t) for _, t in valid]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    denom = sum((x - mx) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denom


def find_output_dir(custom_path: Path | None = None) -> Path:
    """Поиск каталога для сохранения графиков."""
    if custom_path is not None:
        custom_path.mkdir(parents=True, exist_ok=True)
        return custom_path

    candidates = [
        Path("reports/images"),
        Path("../../reports/images"),
        Path("../reports/images"),
    ]
    for p in candidates:
        if p.parent.exists():
            p.mkdir(parents=True, exist_ok=True)
            return p

    default = Path("reports/images")
    default.mkdir(parents=True, exist_ok=True)
    return default


def plot_benchmark_results(
    times_data: dict[str, dict[str, list[tuple[int, float]]]],
    out_dir: Path,
) -> None:
    """Построение графиков в log-log осях и сохранение в PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib не установлен — построение графиков пропущено.")
        return

    # 1. Трёхпанельный log-log график по классам входов
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    classes = ["упорядоченный", "случайный", "обратный"]
    algo_names = ["bubble_sort", "insertion_sort", "selection_sort", "quick_sort"]
    algo_labels = {
        "bubble_sort": "Bubble Sort",
        "insertion_sort": "Insertion Sort",
        "selection_sort": "Selection Sort",
        "quick_sort": "QuickSort (рандомизир.)",
    }
    markers = {
        "bubble_sort": "o",
        "insertion_sort": "s",
        "selection_sort": "^",
        "quick_sort": "D",
    }
    colors = {
        "bubble_sort": "#e41a1c",
        "insertion_sort": "#377eb8",
        "selection_sort": "#4daf4a",
        "quick_sort": "#984ea3",
    }

    for idx, cls in enumerate(classes):
        ax = axes[idx]
        for algo in algo_names:
            points = times_data[algo][cls]
            ns = [p[0] for p in points]
            ts = [p[1] for p in points]
            slope = log_log_slope(points)
            ax.plot(
                ns,
                ts,
                marker=markers[algo],
                color=colors[algo],
                linewidth=1.8,
                label=f"{algo_labels[algo]} (наклон ≈ {slope:.2f})",
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Размер массива n", fontsize=11)
        if idx == 0:
            ax.set_ylabel("Время t, с (медиана)", fontsize=11)
        ax.set_title(f"Вход: {cls}", fontsize=12, fontweight="bold")
        ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
        ax.legend(fontsize=8.5, loc="upper left")

    fig.suptitle("Сравнение алгоритмов сортировки в осях log-log (ЛР 3)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    plot_path1 = out_dir / "lab03_sorts_loglog.png"
    fig.savefig(plot_path1, dpi=160)
    plt.close(fig)

    # 2. Детальный график масштабирования QuickSort на всех классах входов
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    qs_colors = {
        "упорядоченный": "#377eb8",
        "случайный": "#4daf4a",
        "обратный": "#e41a1c",
    }
    qs_markers = {
        "упорядоченный": "s",
        "случайный": "o",
        "обратный": "^",
    }

    for cls in classes:
        points = times_data["quick_sort"][cls]
        ns = [p[0] for p in points]
        ts = [p[1] for p in points]
        slope = log_log_slope(points)
        ax2.plot(
            ns,
            ts,
            marker=qs_markers[cls],
            color=qs_colors[cls],
            linewidth=2,
            label=f"QuickSort ({cls}, наклон ≈ {slope:.2f})",
        )

    # Теоретические опорные прямые O(n log n)
    ref_n = SIZES_QUICK
    c_nlogn = times_data["quick_sort"]["случайный"][-1][1] / (ref_n[-1] * math.log2(ref_n[-1]))
    ref_nlogn = [c_nlogn * n * math.log2(n) for n in ref_n]
    ax2.plot(ref_n, ref_nlogn, "k--", alpha=0.6, label="Теория O(n log n)")

    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("Размер массива n", fontsize=11)
    ax2.set_ylabel("Время t, с", fontsize=11)
    ax2.set_title("QuickSort с рандомизацией на различных классах входов", fontsize=12, fontweight="bold")
    ax2.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)
    ax2.legend(fontsize=9.5)
    fig2.tight_layout()
    plot_path2 = out_dir / "lab03_quicksort.png"
    fig2.savefig(plot_path2, dpi=160)
    plt.close(fig2)

    print(f"\nГрафики успешно сохранены:\n  1. {plot_path1}\n  2. {plot_path2}")


def run_benchmarks(seed: int, out_dir: Path | None = None) -> None:
    """Замеры всех алгоритмов на трёх классах входов; вывод таблиц и графиков."""
    out_dir_resolved = find_output_dir(out_dir)

    plans = [
        ("bubble_sort", ALGORITHMS["bubble_sort"], SIZES_QUADRATIC),
        ("insertion_sort", ALGORITHMS["insertion_sort"], SIZES_QUADRATIC),
        ("selection_sort", ALGORITHMS["selection_sort"], SIZES_QUADRATIC),
        ("quick_sort", lambda a: quick_sort(a, random.Random(seed)), SIZES_QUICK),
    ]

    classes = ["упорядоченный", "случайный", "обратный"]

    times_data: dict[str, dict[str, list[tuple[int, float]]]] = {
        name: {cls: [] for cls in classes} for name, _, _ in plans
    }

    print("\n" + "=" * 75)
    print("ЭМПИРИЧЕСКИЕ ЗАМЕРЫ ВРЕМЕНИ (В СЕКУНДАХ)")
    print("=" * 75)

    for name, fn, sizes in plans:
        print(f"\n>>> Алгоритм: {name}")
        for n in sizes:
            inputs = make_inputs(n, seed)
            for cls in classes:
                data = inputs[cls]
                t_med = bench(fn, data)
                times_data[name][cls].append((n, t_med))
                print(f"  n={n:>7}  вход={cls:<13} t={t_med:.6f} c")

    print("\n" + "=" * 75)
    print("ОЦЕНКА НАКЛОНА В ОСЯХ LOG-LOG (ЭКСПЕРИМЕНТАЛЬНЫЙ ПОРЯДОК РОСТА)")
    print("=" * 75)
    print(f"{'Алгоритм':<18} | {'Упорядоченный':<15} | {'Случайный':<15} | {'Обратный':<15}")
    print("-" * 75)
    for name, _, _ in plans:
        s_sort = log_log_slope(times_data[name]["упорядоченный"])
        s_rand = log_log_slope(times_data[name]["случайный"])
        s_rev = log_log_slope(times_data[name]["обратный"])
        print(f"{name:<18} | {s_sort:>13.3f}   | {s_rand:>13.3f}   | {s_rev:>13.3f}")
    print("-" * 75)

    print("\n" + "=" * 75)
    print("СЧЁТЧИКИ ОПЕРАЦИЙ (СРАВНЕНИЯ И ОБМЕНЫ/СДВИГИ)")
    print("=" * 75)
    simple_sort_fns = {
        "bubble_sort": bubble_sort,
        "insertion_sort": insertion_sort,
        "selection_sort": selection_sort,
    }

    for name, s_fn in simple_sort_fns.items():
        print(f"\n>>> Счётчики для {name}:")
        print(f"{'n':>7} | {'Класс входа':<14} | {'Сравнения':>12} | {'Обмены/Сдвиги':>14} | {'n(n-1)/2 (Теория)':>18}")
        print("-" * 75)
        for n in SIZES_QUADRATIC:
            inputs = make_inputs(n, seed)
            for cls in classes:
                data = inputs[cls]
                _, cmp_count, mov_count = s_fn(data)
                theory_worst = n * (n - 1) // 2
                print(f"{n:>7} | {cls:<14} | {cmp_count:>12} | {mov_count:>14} | {theory_worst:>18}")

    plot_benchmark_results(times_data, out_dir_resolved)


def main() -> None:
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

    print(f"Запуск ЛР 3 для Варианта {args.variant} (seed = {seed})")
    self_check()
    stability_demo()
    run_benchmarks(seed, args.out)


if __name__ == "__main__":
    main()
