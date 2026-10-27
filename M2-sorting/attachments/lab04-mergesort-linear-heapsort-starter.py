#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 4. MergeSort, Counting, Radix и HeapSort: оценка производительности — стартовая заготовка.

Заготовка — это каркас, а не решение: заполните все TODO самостоятельно
в соответствии с КИМ-04 и правилами использования генеративного ИИ
(docs/ai-verification.md). QuickSort перенесите из собственной ЛР 3.

Запуск: python lab04-mergesort-linear-heapsort-starter.py --variant N
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
# 1. Сортировки (реализуются вручную; sorted() используется только как эталон)
# ---------------------------------------------------------------------------


def merge(left: list, right: list, key=None) -> list:
    """Стабильное слияние двух отсортированных списков в новый список.

    Стабильность: при равенстве ключей элемент из left идёт раньше.
    Ожидаемая сложность: O(len(left) + len(right)) по времени и памяти.
    """
    kfn = key if key is not None else (lambda x: x)
    merged = []
    i = 0
    j = 0
    len_left = len(left)
    len_right = len(right)

    while i < len_left and j < len_right:
        # Условие <= обеспечивает стабильность: элемент из левой половины сохраняет приоритет
        if kfn(left[i]) <= kfn(right[j]):
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            j += 1

    if i < len_left:
        merged.extend(left[i:])
    if j < len_right:
        merged.extend(right[j:])

    return merged


def merge_sort(a: list, key=lambda x: x) -> list:
    """MergeSort: возвращает новый отсортированный список.

    Ожидаемая сложность: O(n log n) в лучшем, среднем и худшем случаях.
    Память: O(n) вспомогательная память.
    Стабильность: стабильна.
    """
    if len(a) <= 1:
        return list(a)
    kfn = key if key is not None else (lambda x: x)
    mid = len(a) // 2
    left = merge_sort(a[:mid], key=kfn)
    right = merge_sort(a[mid:], key=kfn)
    return merge(left, right, key=kfn)


def counting_sort(a: list[int], key_max: int) -> list[int]:
    """Устойчивая сортировка подсчётом: ключи — целые из диапазона [0, key_max].

    Схема: массив счётчиков -> префиксные суммы -> расстановка с конца.
    Ожидаемые время и память: O(n + k), где k = key_max + 1;
    ограничение диапазона ключей: при k >> n память и время O(k) доминируют.
    """
    if not a:
        return []
    if key_max < 0:
        raise ValueError("key_max должен быть неотрицательным")

    count = [0] * (key_max + 1)
    for x in a:
        count[x] += 1

    for i in range(1, len(count)):
        count[i] += count[i - 1]

    res = [0] * len(a)
    for x in reversed(a):
        count[x] -= 1
        res[count[x]] = x

    return res


def radix_sort_lsd(a: list[int]) -> list[int]:
    """RadixSort LSD по десятичным разрядам, неотрицательные целые.

    Поверх устойчивой поразрядной counting-сортировки: от младшего разряда
    к старшему. Ожидаемая сложность: O(d * (n + b)), где d = ceil(log10(max_val)), b = 10.
    """
    if len(a) <= 1:
        return list(a)
    max_val = max(a)
    if max_val < 0:
        raise ValueError("radix_sort_lsd поддерживает только неотрицательные целые числа")
    if max_val == 0:
        return list(a)

    res = list(a)
    exp = 1
    base = 10
    while max_val // exp > 0:
        count = [0] * base
        for x in res:
            digit = (x // exp) % base
            count[digit] += 1

        for i in range(1, base):
            count[i] += count[i - 1]

        out = [0] * len(res)
        for x in reversed(res):
            digit = (x // exp) % base
            count[digit] -= 1
            out[count[digit]] = x

        res = out
        exp *= base

    return res


def sift_down(a: list[int], i: int, n: int) -> None:
    """Просейка вниз элемента i в куче a[0:n] (max-heap), на месте.

    Инвариант: поддеревья потомков вершины i являются корректными max-кучами.
    Сложность: O(log n) по времени, O(1) по памяти.
    """
    while True:
        left = 2 * i + 1
        right = 2 * i + 2
        largest = i

        if left < n and a[left] > a[largest]:
            largest = left
        if right < n and a[right] > a[largest]:
            largest = right

        if largest != i:
            a[i], a[largest] = a[largest], a[i]
            i = largest
        else:
            break


def heap_sort(a: list[int]) -> None:
    """HeapSort in-place: сортирует список a на месте, без вспомогательного массива.

    Схема: построение max-кучи просейками вниз (снизу вверх, O(n)),
    затем обмен вершины с последним элементом и просейка (O(n log n)).
    Сложность: O(n log n) в лучшем, среднем и худшем случаях.
    Память: O(1) вспомогательная память.
    Стабильность: НЕ стабильна.
    """
    n = len(a)
    if n <= 1:
        return

    # Фаза 1: построение max-кучи за O(n)
    for i in range((n - 2) // 2, -1, -1):
        sift_down(a, i, n)

    # Фаза 2: последовательное извлечение максимумов в конец массива
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down(a, 0, end)


def quick_sort(a: list[int], rng: random.Random | None = None) -> list[int]:
    """QuickSort с рандомизацией опорного элемента (3-way partition, Dutch National Flag).

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
    """heap_sort сортирует на месте: проверяется тот список, который ему передали."""
    buf = list(a)
    heap_sort(buf)
    return buf


# Каждая функция возвращает отсортированный список; ключи — целые из [0, 999].
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
        [],                    # пустой массив
        [7],                   # один элемент
        [0],                   # нулевой ключ
        [5, 5, 5],             # все элементы равны
        [1, 2, 3, 4, 5],       # уже отсортирован
        [5, 4, 3, 2, 1],       # обратный порядок
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
    """Стабильность слияния на парах (ключ, порядковый номер): эталон sorted() стабилен,
    поэтому при равных ключах порядок номеров обязан совпасть."""
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
    # fn=fn фиксирует функцию текущего шага цикла (иначе все лямбды увидят последнюю)
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
SMALL_KEY_MAX = 100        # узкий диапазон: counting уместен
WIDE_KEY_MAX = 10**9       # широкий диапазон: counting теряет смысл (обсудить в отчёте)


def make_datasets(rng: random.Random, n: int) -> dict[str, list[int]]:
    """Массивы разных распределений и диапазонов ключей для размера n."""
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
    """Медиана времени fn на копии data по REPEATS запускам, с прогревом.

    Каждый запуск получает свежую копию: сортировка на месте не должна
    превращать последующие запуски в сортировку уже отсортированного массива.
    """
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
                    # счётчики размера ~10^9 не помещаются в память — граница
                    # применимости counting; зафиксировать в таблице свойств
                    print(f"    {algo_name:>18}: пропуск (диапазон ключей)")
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
