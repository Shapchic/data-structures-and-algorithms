#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 3. Простые сортировки и QuickSort с рандомизацией.

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
#    Каждая функция сортирует копию входа и возвращает:
#    (отсортированный список, число сравнений, число перемещений/обменов).
# ---------------------------------------------------------------------------


def bubble_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка пузырьком с досрочным выходом.

    Идея: попарные сравнения соседних элементов; за проход максимум всплывает вправо.
    Время: O(n) лучший (уже отсортирован), O(n^2) средний и худший.
    Память: O(1) доп. память. Стабильна (строгое > не меняет равные).
    """
    res = list(a)
    n = len(res)
    comparisons = 0
    swaps = 0
    kfn = key if key is not None else (lambda x: x)

    # Проходы по массиву (максимум n раз)
    for i in range(n):
        swapped = False  # флаг: был ли хоть один обмен на текущем проходе

        # Сравниваем соседние пары; последние i элементов уже на своих местах
        for j in range(n - 1 - i):
            comparisons += 1
            # Строгое > : равные элементы не меняются (сохраняет стабильность)
            if kfn(res[j]) > kfn(res[j + 1]):
                res[j], res[j + 1] = res[j + 1], res[j]  # обмен: больший всплывает вправо
                swaps += 1
                swapped = True

        # Досрочный выход: если за весь проход 0 обменов, массив уже упорядочен (O(n))
        if not swapped:
            break

    return res, comparisons, swaps


def insertion_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка вставками.

    Идея: как карты в руке — элемент вставляется на нужное место в отсортированный префикс.
    Время: O(n) лучший (уже отсортирован), O(n^2) средний и худший.
    Память: O(1) доп. память. Стабильна.
    """
    res = list(a)
    n = len(res)
    comparisons = 0
    moves = 0
    kfn = key if key is not None else (lambda x: x)

    # Перебираем элементы со 2-го (первый элемент res[0] уже образует префикс длины 1)
    for i in range(1, n):
        item = res[i]       # запоминаем вставляемый элемент (освобождаем позицию i)
        item_key = kfn(item)
        j = i - 1           # идём влево по отсортированному префиксу

        # Ищем позицию вставки, сдвигая большие элементы вправо
        while j >= 0:
            comparisons += 1
            if kfn(res[j]) > item_key:
                res[j + 1] = res[j]  # сдвиг элемента вправо
                moves += 1
                j -= 1
            else:
                # Встретили <= item_key: место найдено (остановка на равных дает стабильность)
                break

        # Вставляем элемент в освободившуюся позицию
        res[j + 1] = item

    return res, comparisons, moves


def selection_sort(
    a: list, key: Callable[[Any], Any] | None = None
) -> tuple[list, int, int]:
    """Сортировка выбором.

    Идея: находит минимум в неотсортированном суффиксе и меняет с началом суффикса.
    Время: Theta(n^2) во всех случаях (всегда ровно n*(n-1)/2 сравнений).
    Память: O(1). Число обменов <= n - 1. НЕ стабильна (дальние перестановки).
    """
    res = list(a)
    n = len(res)
    comparisons = 0
    swaps = 0
    kfn = key if key is not None else (lambda x: x)

    # Ищем минимум для каждой позиции i от 0 до n-2
    for i in range(n - 1):
        min_idx = i  # предполагаем, что минимум на позиции i

        # Безусловный просмотр всего суффикса (нет досрочного выхода, всегда n(n-1)/2 сравнений)
        for j in range(i + 1, n):
            comparisons += 1
            if kfn(res[j]) < kfn(res[min_idx]):
                min_idx = j

        # Если минимум не на позиции i — выполняем ровно один обмен
        if min_idx != i:
            res[i], res[min_idx] = res[min_idx], res[i]  # дальний обмен ломает стабильность
            swaps += 1

    return res, comparisons, swaps


# ---------------------------------------------------------------------------
# 2. QuickSort с рандомизированным опорным элементом и 3-way partition
# ---------------------------------------------------------------------------


def quick_sort(
    a: list,
    rng: random.Random | None = None,
    key: Callable[[Any], Any] | None = None,
) -> list:
    """QuickSort с рандомизацией и 3-частным разбиением Дейкстры.

    Идея: делит массив относительно случайного пивота на 3 зоны (<, ==, >).
    Время: O(n log n) среднее, O(n) на массиве равных ключей, O(n^2) худший (крайне редок).
    Память: O(log n) для стека подзадач. НЕ стабильна.
    """
    if rng is None:
        rng = random.Random()

    res = list(a)
    n = len(res)
    if n <= 1:
        return res

    kfn = key if key is not None else (lambda x: x)

    # Итеративный стек отрезков [lo, hi) вместо рекурсии (защита от RecursionError)
    stack: list[tuple[int, int]] = [(0, n)]

    while stack:
        lo, hi = stack.pop()
        if hi - lo <= 1:
            continue

        # Рандомизация: случайный пивот исключает худший случай на отсортированных входах
        pivot_idx = rng.randrange(lo, hi)
        pivot_key = kfn(res[pivot_idx])

        # 3-way partition (голландский флаг):
        # res[lo..lt-1] < pivot, res[lt..gt] == pivot, res[gt+1..hi-1] > pivot
        lt = lo        # граница зоны элементов < pivot
        i = lo         # текущий элемент
        gt = hi - 1    # граница зоны элементов > pivot

        while i <= gt:
            cur_key = kfn(res[i])
            if cur_key < pivot_key:
                res[lt], res[i] = res[i], res[lt]  # меньше пивота: меняем с res[lt]
                lt += 1
                i += 1
            elif cur_key > pivot_key:
                res[i], res[gt] = res[gt], res[i]  # больше пивота: меняем с res[gt]
                gt -= 1                            # i не сдвигаем — проверяем пришедший элемент
            else:
                i += 1  # равен пивоту: оставляем в центре, равные элементы исключаются из сортировки

        # Ограничение глубины стека: сначала кладём больший отрезок, меньший обрабатываем
        # в следующей итерации (размер меньшего <= len/2, глубина стека гарантированно <= log2 n)
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
    """Проверка стабильности на парах (ключ, метка).

    Стабильная сортировка сохраняет исходный порядок меток для равных ключей:
    для ключа 1: ["b", "d"], для ключа 2: ["a", "c"].
    """
    sample_pairs = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
    expected_order = [(1, "b"), (1, "d"), (2, "a"), (2, "c")]

    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ СТАБИЛЬНОСТИ АЛГОРИТМОВ СОРТИРОВКИ (ЛР 3)")
    print("=" * 60)
    print(f"Исходный массив: {sample_pairs}")
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

    print("\nПояснение:")
    print("  - Bubble Sort и Insertion Sort перемещают только смежные элементы (СТАБИЛЬНЫ).")
    print("  - Selection Sort и QuickSort совершают дальние перестановки через другие элементы (НЕ СТАБИЛЬНЫ).")
    print("=" * 60 + "\n")
    return results


# ---------------------------------------------------------------------------
# 4. Генерация классов входов по варианту (детерминированно по seed)
# ---------------------------------------------------------------------------


def make_inputs(n: int, seed: int) -> dict[str, list[int]]:
    """Генерация трёх классов входов размера n: упорядоченный, случайный, обратный."""
    rng = random.Random(seed + n)
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
    """Граничные случаи, инварианты сортировки и сверка с sorted()."""
    boundary = [
        [],                    # Пустой массив
        [7],                   # Один элемент
        [5, 5, 5, 5],          # Одинаковые элементы
        [1, 2, 3, 4, 5],       # Уже отсортирован
        [5, 4, 3, 2, 1],       # Обратный порядок
    ]
    for name, fn in ALGORITHMS.items():
        for a in boundary:
            res = fn(list(a))
            assert is_sorted(res), f"{name}: нарушен порядок неубывания на {a}"
            assert sorted(res) == sorted(a), f"{name}: не является перестановкой входа {a}"

    # Сверка с эталоном sorted() на случайных входах
    rng = random.Random(0)
    for _ in range(300):
        a = [rng.randint(-100, 100) for _ in range(rng.randint(0, 80))]
        expected = sorted(a)
        for name, fn in ALGORITHMS.items():
            assert fn(list(a)) == expected, f"{name}: расходится с sorted() на {a}"

    # Проверка числа сравнений Selection Sort: всегда ровно n*(n-1)/2
    _, comparisons, _ = selection_sort([3, 1, 2, 5, 4])
    assert comparisons == 10, "selection_sort: неверный счётчик сравнений"

    # Инвариант сохранения мультимножества
    for _ in range(50):
        a = [rng.randint(-50, 50) for _ in range(60)]
        for name, fn in ALGORITHMS.items():
            res = fn(list(a))
            assert collections.Counter(res) == collections.Counter(a), (
                f"{name}: нарушен инвариант мультимножества"
            )

    # Проверка лучшего случая Bubble и Insertion на отсортированном входе: ровно n-1 сравнений
    for n_test in (2, 5, 10, 30):
        sorted_arr = list(range(n_test))
        _, b_cmp, b_swp = bubble_sort(sorted_arr)
        assert b_cmp == n_test - 1 and b_swp == 0, "bubble_sort: ошибка в лучшем случае"

        _, i_cmp, i_mov = insertion_sort(sorted_arr)
        assert i_cmp == n_test - 1 and i_mov == 0, "insertion_sort: ошибка в лучшем случае"

    # Проверка худшего случая Bubble и Insertion: ровно n*(n-1)/2
    for n_test in (2, 5, 10, 20):
        rev_arr = list(range(n_test, 0, -1))
        expected_worst = n_test * (n_test - 1) // 2
        _, b_cmp, b_swp = bubble_sort(rev_arr)
        assert b_cmp == expected_worst and b_swp == expected_worst, "bubble_sort: ошибка худшего случая"

        _, i_cmp, i_mov = insertion_sort(rev_arr)
        assert i_cmp == expected_worst and i_mov == expected_worst, "insertion_sort: ошибка худшего случая"

    print("self_check: OK (все инварианты, граничные случаи и сверка с sorted() пройдены)")


# ---------------------------------------------------------------------------
# 6. Бенчмарк (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES_QUADRATIC = [500, 1_000, 2_000, 4_000, 8_000]
SIZES_QUICK = [1_000, 3_000, 10_000, 30_000, 100_000]
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

    # 2. График QuickSort на всех классах входов
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    qs_colors = {"упорядоченный": "#377eb8", "случайный": "#4daf4a", "обратный": "#e41a1c"}
    qs_markers = {"упорядоченный": "s", "случайный": "o", "обратный": "^"}

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

    print(f"\nГрафики сохранены:\n  1. {plot_path1}\n  2. {plot_path2}")


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
    print("ОЦЕНКА НАКЛОНА В ОСЯХ LOG-LOG (ПОРЯДОК РОСТА k)")
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
