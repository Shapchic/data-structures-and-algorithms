#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 3. Простые сортировки и QuickSort с рандомизацией.

Реализация и экспериментальное исследование алгоритмов сортировки
в соответствии с КИМ-03 и методиками docs/reproducibility.md и docs/ai-verification.md.

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
# 1. Простые сортировки со счётчиками (сортируют КОПИЮ входа, вход не меняют)
#    Каждая функция возвращает кортеж: (отсортированный список,
#    число сравнений ключей, число обменов/перемещений элементов).
# ---------------------------------------------------------------------------


def bubble_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка пузырьком с оптимизацией досрочного выхода.

    Сложность:
      - Худший случай (обратный порядок): Theta(n^2) сравнений и обменов.
      - Средний случай (случайный массив): Theta(n^2) сравнений и обменов.
      - Лучший случай (уже отсортирован): Theta(n) сравнений (ровно n - 1), 0 обменов.
    Память: O(1) дополнительной памяти (на копии входа O(n)).
    Стабильность: стабильна (строгое неравенство > не меняет порядок равных).
    """
    res = list(a)
    n = len(res)
    comparisons = 0
    swaps = 0
    kfn = key if key is not None else (lambda x: x)

    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):
            comparisons += 1
            if kfn(res[j]) > kfn(res[j + 1]):
                res[j], res[j + 1] = res[j + 1], res[j]
                swaps += 1
                swapped = True
        # Досрочный выход: если за весь проход не было ни одного обмена,
        # массив уже отсортирован (лучший случай Theta(n)).
        if not swapped:
            break

    return res, comparisons, swaps


def insertion_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка вставками.

    Сложность:
      - Худший случай (обратный порядок): Theta(n^2) сравнений и сдвигов.
      - Средний случай: Theta(n^2) сравнений и сдвигов (~ n^2 / 4).
      - Лучший случай (уже отсортирован): Theta(n) сравнений (ровно n - 1), 0 сдвигов.
    Память: O(1) дополнительной памяти.
    Стабильность: стабильна (равные элементы не перескакивают друг через друга).
    """
    res = list(a)
    n = len(res)
    comparisons = 0
    moves = 0
    kfn = key if key is not None else (lambda x: x)

    for i in range(1, n):
        item = res[i]
        item_key = kfn(item)
        j = i - 1
        while j >= 0:
            comparisons += 1
            if kfn(res[j]) > item_key:
                res[j + 1] = res[j]
                moves += 1
                j -= 1
            else:
                break
        res[j + 1] = item

    return res, comparisons, moves


def selection_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка выбором.

    Сложность:
      - Худший, средний и лучший случаи по числу сравнений: строго Theta(n^2),
        всегда ровно n * (n - 1) // 2 сравнений независимо от характера входа.
      - Число обменов: не более n - 1 во всех случаях (минимум 0, максимум n - 1).
    Память: O(1) дополнительной памяти.
    Стабильность: НЕ стабильна (дальние перестановки нарушают относительный
    порядок равных ключей).
    """
    res = list(a)
    n = len(res)
    comparisons = 0
    swaps = 0
    kfn = key if key is not None else (lambda x: x)

    for i in range(n - 1):
        min_idx = i
        for j in range(i + 1, n):
            comparisons += 1
            if kfn(res[j]) < kfn(res[min_idx]):
                min_idx = j
        if min_idx != i:
            res[i], res[min_idx] = res[min_idx], res[i]
            swaps += 1

    return res, comparisons, swaps


# ---------------------------------------------------------------------------
# 2. QuickSort с рандомизированным опорным элементом
# ---------------------------------------------------------------------------


def quick_sort(
    a: list,
    rng: random.Random | None = None,
    key: Callable[[Any], Any] | None = None,
) -> list:
    """QuickSort с рандомизированным выбором опорного элемента (3-way partition).

    Сложность:
      - В среднем: O(n log n) на любых распределениях благодаря рандомизации.
      - В худшем случае: O(n^2), однако вероятность выбора плохих пивотов
        на каждом шаге при рандомизации экспоненциально мала (<= 1 / n!).
      - На массивах из одинаковых элементов: O(n) благодаря трехчастному
        разбиению Дейкстры (Dutch National Flag).
    Память: O(log n) для стека подзадач (меньший отрезок обрабатывается первым).
    Стабильность: НЕ стабильна (дальние перестановки при разбиении).
    """
    if rng is None:
        rng = random.Random()

    res = list(a)
    n = len(res)
    if n <= 1:
        return res

    kfn = key if key is not None else (lambda x: x)

    # Итеративная реализация со стеком отрезков [lo, hi)
    # Исключает переполнение системного стека вызовов Python (RecursionError)
    stack: list[tuple[int, int]] = [(0, n)]

    while stack:
        lo, hi = stack.pop()
        # Базовый случай для малых подмассивов
        if hi - lo <= 1:
            continue

        # Рандомизированный выбор опорного элемента
        pivot_idx = rng.randrange(lo, hi)
        pivot_val = res[pivot_idx]
        pivot_key = kfn(pivot_val)

        # 3-частное разбиение (Dutch National Flag) на [lo, hi)
        # res[lo..lt-1]  < pivot_key
        # res[lt..gt]    == pivot_key
        # res[gt+1..hi-1]> pivot_key
        lt = lo
        i = lo
        gt = hi - 1

        while i <= gt:
            cur_key = kfn(res[i])
            if cur_key < pivot_key:
                res[lt], res[i] = res[i], res[lt]
                lt += 1
                i += 1
            elif cur_key > pivot_key:
                res[i], res[gt] = res[gt], res[i]
                gt -= 1
            else:
                i += 1

        # Оптимизация глубины стека: сначала кладём больший отрезок,
        # затем меньший, что гарантирует размер стека <= O(log n)
        left_len = lt - lo
        right_len = hi - (gt + 1)

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
# 3. Демонстрация стабильности на парах (ключ, метка)
# ---------------------------------------------------------------------------


def stability_demo() -> dict[str, bool]:
    """Показать, какие из четырёх сортировок стабильны на парах (ключ, метка).

    Берём массив пар с повторяющимися ключами:
    [(2, "a"), (1, "b"), (2, "c"), (1, "d")].
    Сортируем только по ключу p[0].
    Стабильный алгоритм сохраняет относительный порядок меток:
    для ключа 1: ["b", "d"], для ключа 2: ["a", "c"].
    """
    sample_pairs = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
    expected_order = [(1, "b"), (1, "d"), (2, "a"), (2, "c")]

    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ СТАБИЛЬНОСТИ АЛГОРИТМОВ СОРТИРОВКИ")
    print("=" * 60)
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

    print("\nВывод:")
    print("  - Bubble Sort и Insertion Sort перемещают только смежные элементы")
    print("    при строгом нарушении порядка, поэтому они СТАБИЛЬНЫ.")
    print("  - Selection Sort и QuickSort совершают дальние перестановки через")
    print("    другие элементы, поэтому они НЕ СТАБИЛЬНЫ.")
    print("=" * 60 + "\n")
    return results


# ---------------------------------------------------------------------------
# 4. Классы входов (данные по варианту, детерминированно по seed)
# ---------------------------------------------------------------------------


def make_inputs(n: int, seed: int) -> dict[str, list[int]]:
    """Три класса входов размера n: упорядоченный, случайный, обратный."""
    rng = random.Random(seed + n)  # свой поток для каждого размера
    data = [rng.randint(-1_000_000, 1_000_000) for _ in range(n)]
    return {
        "упорядоченный": sorted(data),
        "случайный": data,
        "обратный": sorted(data, reverse=True),
    }


# ---------------------------------------------------------------------------
# 5. Верификация (шаги 1–3 методики docs/ai-verification.md)
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
    """Граничные случаи, инварианты сортировки и сверка с эталоном sorted()."""
    boundary = [
        [],                    # пустой массив
        [7],                   # один элемент
        [5, 5, 5, 5],          # все элементы равны
        [1, 2, 3, 4, 5],       # уже отсортирован
        [5, 4, 3, 2, 1],       # обратный порядок
    ]
    for name, fn in ALGORITHMS.items():
        for a in boundary:
            res = fn(list(a))
            assert is_sorted(res), f"{name}: нарушен порядок на {a}"
            assert sorted(res) == sorted(a), f"{name}: не перестановка входа {a}"

    # Сверка с эталоном из стандартной библиотеки на сотнях случайных входов.
    rng = random.Random(0)
    for _ in range(300):
        a = [rng.randint(-100, 100) for _ in range(rng.randint(0, 80))]
        expected = sorted(a)
        for name, fn in ALGORITHMS.items():
            assert fn(list(a)) == expected, f"{name}: расходится с sorted() на {a}"

    # Счётчики: у сортировки выбором ровно n*(n-1)/2 сравнений на любом входе.
    _, comparisons, _ = selection_sort([3, 1, 2, 5, 4])
    assert comparisons == 10, "selection_sort: неверный счётчик сравнений"

    # Дополнительные строгие проверки инвариантов (Шаг 1 методики ai-verification.md)
    # 1. Инвариант сохранения мультимножества: Counter(res) == Counter(a)
    for _ in range(50):
        a = [rng.randint(-50, 50) for _ in range(60)]
        for name, fn in ALGORITHMS.items():
            res = fn(list(a))
            assert collections.Counter(res) == collections.Counter(a), (
                f"{name}: нарушен инвариант мультимножества (потеряны/изменены элементы)"
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

SIZES_QUADRATIC = [500, 1_000, 2_000, 4_000, 8_000]     # для простых сортировок
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
    """Наклон прямой в осях (log n, log t) — оценка показателя степени."""
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
    """Надёжный поиск каталога для сохранения изображений."""
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
    """Построение информативных графиков в log-log осях и сохранение в PNG."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib не установлен — построение графиков пропущено.")
        return

    # 1. Трехпанельный log-log график по классам входов
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

    fig.suptitle("Сравнение алгоритмов сортировки в осях log-log", fontsize=14, fontweight="bold")
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

    # Теоретические опорные прямые O(n log n) и O(n^2)
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
    """Замеры всех алгоритмов на трёх классах входов; вывод подробных таблиц и построение графиков."""
    out_dir_resolved = find_output_dir(out_dir)

    plans = [
        ("bubble_sort", ALGORITHMS["bubble_sort"], SIZES_QUADRATIC),
        ("insertion_sort", ALGORITHMS["insertion_sort"], SIZES_QUADRATIC),
        ("selection_sort", ALGORITHMS["selection_sort"], SIZES_QUADRATIC),
        ("quick_sort", lambda a: quick_sort(a, random.Random(seed)), SIZES_QUICK),
    ]

    classes = ["упорядоченный", "случайный", "обратный"]

    # Структура для сбора замеров времени: algo -> class -> list of (n, t)
    times_data: dict[str, dict[str, list[tuple[int, float]]]] = {
        name: {cls: [] for cls in classes} for name, _, _ in plans
    }

    # 1. Сбор и вывод времени работы
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

    # 2. Сводная таблица наклонов log-log
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

    # 3. Сбор и вывод счётчиков операций (сравнения и обмены/сдвиги) для простых сортировок
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

    # 4. Построение графиков
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
