#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 6. Линейный, бинарный и интерполяционный поиск: сравнение.

Реализация трёх алгоритмов поиска ключа в отсортированном массиве:
- линейного (linear_search) со счётчиком сравнений;
- бинарного (binary_search) с поддержкой инварианта границ lo/hi;
- интерполяционного (interpolation_search) с защитой от деления на ноль
  и выхода ключа за границы диапазона [a[lo], a[hi]].

Каждая функция поиска работает с отсортированным по неубыванию массивом
и возвращает пару: (индекс найденного элемента или -1, число сравнений ключей).

Запуск:
    python lab06-search-starter.py --variant 21
    python lab06-search-starter.py --variant 21 --out ../../reports/images
"""
from __future__ import annotations

import argparse
import bisect
import math
from pathlib import Path
import random
import statistics
import sys
import time

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ---------------------------------------------------------------------------
# 1. Алгоритмы поиска (ручная реализация без in/index/bisect в основной части)
# ---------------------------------------------------------------------------


def linear_search(a: list[int], key: int) -> tuple[int, int]:
    """Линейный поиск первого вхождения key.

    Возвращает (индекс первого вхождения или -1, число сравнений ключей).
    Временная сложность:
        - Худший случай: O(n) — ключ отсутствует или расположен в конце массива;
        - Средний случай: O(n) (в среднем n / 2 сравнений при равномерном поиске);
        - Лучший случай: O(1) — искомый ключ находится на первой позиции a[0].
    Пространственная сложность: O(1) вспомогательной памяти.
    """
    cmp_count = 0
    for i, x in enumerate(a):
        cmp_count += 1
        if x == key:
            return i, cmp_count
    return -1, cmp_count


def binary_search(a: list[int], key: int) -> tuple[int, int]:
    """Бинарный поиск key в отсортированном массиве.

    Возвращает (индекс любого вхождения или -1, число сравнений ключей).
    Инвариант цикла:
        Если искомый ключ key содержится в массиве a, то он гарантированно
        находится в текущем диапазоне индексов a[lo..hi].
        При каждом шаге длина отрезка строго уменьшается: новый диапазон
        составляет либо [lo, mid - 1], либо [mid + 1, hi], где mid лежит строго
        внутри [lo, hi]. Это строго гарантирует завершение цикла за не более чем
        ceil(log2(n + 1)) шагов без зацикливания.
    Временная сложность:
        - Худший случай: O(log n);
        - Средний случай: O(log n);
        - Лучший случай: O(1) — ключ совпал с центральным элементом на первом шаге.
    Пространственная сложность: O(1) вспомогательной памяти.
    """
    lo = 0
    hi = len(a) - 1
    cmp_count = 0
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        cmp_count += 1
        if a[mid] == key:
            return mid, cmp_count
        elif a[mid] < key:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1, cmp_count


def interpolation_search(a: list[int], key: int) -> tuple[int, int]:
    """Интерполяционный поиск key в отсортированном массиве.

    Возвращает (индекс любого вхождения или -1, число сравнений ключей).
    Позиция зонда: mid = lo + (key - a[lo]) * (hi - lo) // (a[hi] - a[lo]).
    Инвариант и защита от деления на ноль / выхода за границы:
        1. Если key < a[lo] или key > a[hi], ключ заведомо отсутствует
           в отсортированном подотрезке [a[lo], a[hi]], завершение за O(1).
        2. Если a[lo] == a[hi], знаменатель интерполяционной формулы равен 0.
           Так как массив отсортирован, все элементы на отрезке [lo, hi] равны a[lo].
           Следовательно, ключ найден, если key == a[lo], иначе отсутствует.
        3. Так как a[lo] <= key <= a[hi] и a[lo] < a[hi], вычисленный индекс mid
           гарантированно попадает в диапазон [lo, hi]. При каждом шаге границы
           строго смещаются (lo = mid + 1 либо hi = mid - 1), обеспечивая сходимость.
    Временная сложность:
        - Средний случай на равномерных данных: O(log log n);
        - Худший случай: O(n) — на неравномерных (например, экспоненциальных) данных,
          где сгущение значений приводит к медленному продвижению зонда;
        - Лучший случай: O(1) — попадание в целевой ключ на первом шаге.
    Пространственная сложность: O(1) вспомогательной памяти.
    """
    if not a:
        return -1, 0

    lo = 0
    hi = len(a) - 1
    cmp_count = 0

    while lo <= hi:
        cmp_count += 1
        if key < a[lo]:
            return -1, cmp_count

        cmp_count += 1
        if key > a[hi]:
            return -1, cmp_count

        if a[lo] == a[hi]:
            cmp_count += 1
            if a[lo] == key:
                return lo, cmp_count
            return -1, cmp_count

        mid = lo + (key - a[lo]) * (hi - lo) // (a[hi] - a[lo])

        cmp_count += 1
        if a[mid] == key:
            return mid, cmp_count
        elif a[mid] < key:
            lo = mid + 1
        else:
            hi = mid - 1

    return -1, cmp_count


# ---------------------------------------------------------------------------
# 2. Данные по варианту: два распределения, присутствующие/отсутствующие ключи
# ---------------------------------------------------------------------------


def make_dataset(n: int, distribution: str, rng: random.Random) -> list[int]:
    """Отсортированный массив n ключей: 'uniform' — равномерное распределение,
    'exponential' — неравномерное (экспоненциальное, значения сгущаются у нуля)."""
    if distribution == "uniform":
        return sorted(rng.randint(0, 10 * n) for _ in range(n))
    if distribution == "exponential":
        return sorted(int(rng.expovariate(1.0 / 1000.0)) for _ in range(n))
    raise ValueError(f"неизвестное распределение: {distribution!r}")


def pick_keys(a: list[int], rng: random.Random, count: int,
              present: bool) -> list[int]:
    """count ключей для серии поисков: присутствующие берутся из массива,
    отсутствующие подбираются вне множества его значений."""
    if present:
        return [a[rng.randrange(len(a))] for _ in range(count)]
    have = set(a)
    hi = (a[-1] if a else 0) + 2
    keys: list[int] = []
    while len(keys) < count:
        k = rng.randint(-hi, hi)
        if k not in have:
            keys.append(k)
    return keys


# ---------------------------------------------------------------------------
# 3. Репрезентативные тесты и инварианты (шаги 1–3 методики верификации)
# ---------------------------------------------------------------------------

ALGORITHMS = [
    ("linear", linear_search),
    ("binary", binary_search),
    ("interpolation", interpolation_search),
]


def self_check() -> None:
    """Граничные случаи + сверка с эталоном (оператор in, list.index, bisect)."""
    for name, fn in ALGORITHMS:
        # Пустой массив: элемент не найден, сравнений нет.
        assert fn([], 1) == (-1, 0), f"{name}: пустой массив"
        # Один элемент: найден / не найден.
        assert fn([7], 7)[0] == 0, f"{name}: один элемент, ключ найден"
        assert fn([7], 3)[0] == -1, f"{name}: один элемент, ключ отсутствует"
        # Первый, последний и отсутствующие ключи (внутри и вне диапазона).
        a = [1, 3, 3, 5, 8, 13, 21]
        assert fn(a, 1)[0] == 0, f"{name}: первый элемент"
        assert fn(a, 21)[0] == len(a) - 1, f"{name}: последний элемент"
        assert fn(a, 4)[0] == -1, f"{name}: отсутствующий ключ внутри диапазона"
        assert fn(a, 100)[0] == -1, f"{name}: ключ вне диапазона"

    # Сверка с эталоном стандартной библиотеки на случайных массивах.
    rng = random.Random(0)
    for _ in range(300):
        a = sorted(rng.randint(0, 60) for _ in range(rng.randint(1, 40)))
        key = rng.randint(-5, 65)
        # Эталон присутствия ключа — bisect_left (и, эквивалентно, оператор in).
        j = bisect.bisect_left(a, key)
        present = j < len(a) and a[j] == key
        assert present == (key in a)
        for name, fn in ALGORITHMS:
            idx, cmp_count = fn(a, key)
            assert cmp_count >= 1, f"{name}: счётчик сравнений не ведётся"
            if present:
                # При дубликатах бинарный/интерполяционный могут вернуть
                # любое вхождение — проверяем значение по индексу.
                assert idx != -1 and a[idx] == key, f"{name}: ключ не найден"
            else:
                assert idx == -1, f"{name}: найден отсутствующий ключ"
        # Линейный поиск обязан возвращать первое вхождение — эталон list.index.
        if present:
            assert linear_search(a, key)[0] == a.index(key)
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 4. Бенчмарк: сравнения и время от n (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES = [1_000, 3_000, 10_000, 30_000, 100_000]
REPEATS = 5      # число повторов серии замеров (берётся медиана)
N_KEYS = 200     # число ключей в одной серии поисков


def bench(fn, a: list[int], keys: list[int]) -> float:
    """Медиана времени одной серии поисков по REPEATS запускам, с прогревом."""
    for k in keys:  # прогрев — не учитывается
        fn(a, k)
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        for k in keys:
            fn(a, k)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def mean_comparisons(fn, a: list[int], keys: list[int]) -> float:
    """Среднее число сравнений ключей на один поиск."""
    return statistics.mean(fn(a, k)[1] for k in keys)


def plot_results(data: dict, out_dir: Path) -> None:
    """Построение графиков 'сравнения от n' и 'время от n'."""
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib не установлен, пропуск построения графиков.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "figure.autolayout": True})

    # Цветовая гамма и стили линий
    colors = {
        "linear": "#d62728",         # красный
        "binary": "#1f77b4",         # синий
        "interpolation": "#2ca02c",  # зелёный
    }
    markers = {
        "linear": "s",
        "binary": "o",
        "interpolation": "^",
    }

    # -----------------------------------------------------------------------
    # График 1: Число сравнений от n (4 панели)
    # -----------------------------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # (0, 0): Равномерное распределение — все алгоритмы (лог по x и y)
    ax = axes[0, 0]
    for name in ("linear", "binary", "interpolation"):
        sizes_p = data["uniform"][name][True]["sizes"]
        cmps_p = data["uniform"][name][True]["cmps"]
        ax.plot(sizes_p, cmps_p, marker=markers[name], color=colors[name],
                linewidth=2, label=f"{name} (есть)")
        sizes_m = data["uniform"][name][False]["sizes"]
        cmps_m = data["uniform"][name][False]["cmps"]
        ax.plot(sizes_m, cmps_m, marker=markers[name], color=colors[name],
                linestyle="--", linewidth=1.5, alpha=0.7, label=f"{name} (нет)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Размер массива n (log)", fontsize=11)
    ax.set_ylabel("Среднее число сравнений (log)", fontsize=11)
    ax.set_title("Равномерное распределение: все алгоритмы", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")

    # (0, 1): Равномерное распределение — зум Binary vs Interpolation
    ax = axes[0, 1]
    for name in ("binary", "interpolation"):
        sizes_p = data["uniform"][name][True]["sizes"]
        cmps_p = data["uniform"][name][True]["cmps"]
        ax.plot(sizes_p, cmps_p, marker=markers[name], color=colors[name],
                linewidth=2.2, label=f"{name} (есть)")
        sizes_m = data["uniform"][name][False]["sizes"]
        cmps_m = data["uniform"][name][False]["cmps"]
        ax.plot(sizes_m, cmps_m, marker=markers[name], color=colors[name],
                linestyle="--", linewidth=1.8, alpha=0.8, label=f"{name} (нет)")
    # Теоретические кривые для справки
    ref_n = SIZES
    theory_bin = [math.log2(n) for n in ref_n]
    theory_interp = [math.log2(max(1.0, math.log2(n))) * 3.0 for n in ref_n]
    ax.plot(ref_n, theory_bin, ":", color="navy", alpha=0.5, label="Теория $O(\\log n)$")
    ax.plot(ref_n, theory_interp, ":", color="darkgreen", alpha=0.5, label="Теория $O(\\log \\log n)$")
    ax.set_xscale("log")
    ax.set_xlabel("Размер массива n (log)", fontsize=11)
    ax.set_ylabel("Среднее число сравнений", fontsize=11)
    ax.set_title("Равномерное распределение: Binary vs Interpolation\n($O(\\log n)$ против $O(\\log\\log n)$)",
                 fontsize=12, fontweight="bold")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")

    # (1, 0): Экспоненциальное распределение — все алгоритмы
    ax = axes[1, 0]
    for name in ("linear", "binary", "interpolation"):
        sizes_p = data["exponential"][name][True]["sizes"]
        cmps_p = data["exponential"][name][True]["cmps"]
        ax.plot(sizes_p, cmps_p, marker=markers[name], color=colors[name],
                linewidth=2, label=f"{name} (есть)")
        sizes_m = data["exponential"][name][False]["sizes"]
        cmps_m = data["exponential"][name][False]["cmps"]
        ax.plot(sizes_m, cmps_m, marker=markers[name], color=colors[name],
                linestyle="--", linewidth=1.5, alpha=0.7, label=f"{name} (нет)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Размер массива n (log)", fontsize=11)
    ax.set_ylabel("Среднее число сравнений (log)", fontsize=11)
    ax.set_title("Экспоненциальное распределение: все алгоритмы", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")

    # (1, 1): Экспоненциальное распределение — деградация Interpolation vs Binary
    ax = axes[1, 1]
    for name in ("binary", "interpolation"):
        sizes_p = data["exponential"][name][True]["sizes"]
        cmps_p = data["exponential"][name][True]["cmps"]
        ax.plot(sizes_p, cmps_p, marker=markers[name], color=colors[name],
                linewidth=2.2, label=f"{name} (есть)")
        sizes_m = data["exponential"][name][False]["sizes"]
        cmps_m = data["exponential"][name][False]["cmps"]
        ax.plot(sizes_m, cmps_m, marker=markers[name], color=colors[name],
                linestyle="--", linewidth=1.8, alpha=0.8, label=f"{name} (нет)")
    ax.set_xscale("log")
    ax.set_xlabel("Размер массива n (log)", fontsize=11)
    ax.set_ylabel("Среднее число сравнений", fontsize=11)
    ax.set_title("Деградация интерполяционного поиска при экспоненциальном сгущении\n(рост сравнений до >200)",
                 fontsize=12, fontweight="bold")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")

    p1 = out_dir / "lab06_comparisons.png"
    fig.savefig(p1, dpi=160)
    plt.close(fig)
    print(f"График сравнений сохранён: {p1}")

    # -----------------------------------------------------------------------
    # График 2: Время выполнения серии поисков от n (2 панели)
    # -----------------------------------------------------------------------
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5.5))

    # (0): Время на равномерном распределении (log-log)
    ax = axes2[0]
    for name in ("linear", "binary", "interpolation"):
        sizes_p = data["uniform"][name][True]["sizes"]
        times_p = data["uniform"][name][True]["times"]
        ax.plot(sizes_p, times_p, marker=markers[name], color=colors[name],
                linewidth=2, label=f"{name} (есть)")
        sizes_m = data["uniform"][name][False]["sizes"]
        times_m = data["uniform"][name][False]["times"]
        ax.plot(sizes_m, times_m, marker=markers[name], color=colors[name],
                linestyle="--", linewidth=1.5, alpha=0.7, label=f"{name} (нет)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Размер массива n (log)", fontsize=11)
    ax.set_ylabel("Медиана времени серии (с, log)", fontsize=11)
    ax.set_title("Время серии поисков (200 ключей): Равномерное распределение",
                 fontsize=12, fontweight="bold")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")

    # (1): Время на экспоненциальном распределении (log-log)
    ax = axes2[1]
    for name in ("linear", "binary", "interpolation"):
        sizes_p = data["exponential"][name][True]["sizes"]
        times_p = data["exponential"][name][True]["times"]
        ax.plot(sizes_p, times_p, marker=markers[name], color=colors[name],
                linewidth=2, label=f"{name} (есть)")
        sizes_m = data["exponential"][name][False]["sizes"]
        times_m = data["exponential"][name][False]["times"]
        ax.plot(sizes_m, times_m, marker=markers[name], color=colors[name],
                linestyle="--", linewidth=1.5, alpha=0.7, label=f"{name} (нет)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Размер массива n (log)", fontsize=11)
    ax.set_ylabel("Медиана времени серии (с, log)", fontsize=11)
    ax.set_title("Время серии поисков (200 ключей): Экспоненциальное распределение\n(замедление Interpolation)",
                 fontsize=12, fontweight="bold")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")

    p2 = out_dir / "lab06_execution_time.png"
    fig2.savefig(p2, dpi=160)
    plt.close(fig2)
    print(f"График времени сохранён: {p2}")


def run_benchmarks(seed: int, out_dir: Path | None = None) -> dict:
    """Выполнение замеров сравнений и времени, форматированный вывод и построение графиков."""
    rng = random.Random(seed)

    # Структура для сбора данных
    results: dict = {
        dist: {
            name: {
                present: {"sizes": [], "cmps": [], "times": []}
                for present in (True, False)
            }
            for name, _ in ALGORITHMS
        }
        for dist in ("uniform", "exponential")
    }

    for distribution in ("uniform", "exponential"):
        print(f"\n{'='*75}")
        print(f"Распределение данных: {distribution.upper()}")
        print(f"{'='*75}")
        print(f"{'n':>7} | {'ключ':<5} | {'алгоритм':<13} | {'сравнений':>11} | {'время серии, с':>14} | {'время 1 поиска, мкс':>19}")
        print("-" * 75)

        for n in SIZES:
            a = make_dataset(n, distribution, rng)
            for present in (True, False):
                keys = pick_keys(a, rng, N_KEYS, present)
                label = "есть" if present else "нет"
                for name, fn in ALGORITHMS:
                    if name == "linear" and n > 30_000:
                        continue  # линейный поиск: большие n занимают ощутимое время

                    cmps = mean_comparisons(fn, a, keys)
                    t_series = bench(fn, a, keys)
                    t_single_us = (t_series / N_KEYS) * 1e6

                    results[distribution][name][present]["sizes"].append(n)
                    results[distribution][name][present]["cmps"].append(cmps)
                    results[distribution][name][present]["times"].append(t_series)

                    print(f"{n:>7} | {label:<5} | {name:<13} | {cmps:>11.2f} | {t_series:>14.6f} | {t_single_us:>19.2f}")

    if out_dir is not None:
        plot_results(results, out_dir)

    return results


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

    out_dir = args.out
    if out_dir is None:
        out_dir = Path(__file__).resolve().parent.parent.parent / "reports" / "images"

    run_benchmarks(seed, out_dir)


if __name__ == "__main__":
    main()
