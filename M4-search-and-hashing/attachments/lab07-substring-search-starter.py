#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 7. Сравнительный анализ КМП, Рабина–Карпа и Бойера–Мура.

Реализация четырёх алгоритмов точного поиска подстроки в тексте:
1. Наивный поиск со сдвигом на 1 символ (эталонная модель);
2. Алгоритм Кнута–Морриса–Пратта (КМП) с явным построением префикс-функции;
3. Алгоритм Рабина–Карпа с полиномиальным кольцевым хешем и посимвольной проверкой при коллизиях;
4. Алгоритм Бойера–Мура с эвристиками плохого символа и хорошего суффикса (уровень 10).

Все алгоритмы возвращают все вхождения шаблона (включая перекрывающиеся)
и точное число выполненных посимвольных сравнений.

Запуск:
    python lab07-substring-search-starter.py --variant 21
    python lab07-substring-search-starter.py --variant 21 --out ../../reports/images
"""
from __future__ import annotations

import argparse
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
# 1. Алгоритмы поиска подстрок
# ---------------------------------------------------------------------------


def naive_search(text: str, pattern: str) -> tuple[list[int], int]:
    """Наивный поиск подстроки со сдвигом на одну позицию.

    Сложность:
        - Худший случай: O(n * m) — возникает, например, на text = "a"*n, pattern = "a"*(m-1) + "b",
          когда почти весь шаблон совпадает до последнего символа перед сдвигом.
        - Средний случай: O(n) на алфавитах достаточного размера (быстрый отсев на 1-2 символах).
        - Память: O(k) для хранения индексов вхождений.
    """
    n, m = len(text), len(pattern)
    if m == 0 or n < m:
        return [], 0

    occurrences: list[int] = []
    comparisons = 0

    for i in range(n - m + 1):
        match = True
        for j in range(m):
            comparisons += 1
            if text[i + j] != pattern[j]:
                match = False
                break
        if match:
            occurrences.append(i)

    return occurrences, comparisons


def prefix_function(pattern: str) -> list[int]:
    """Префикс-функция шаблона (массив pi).

    pi[i] — длина наибольшего собственного префикса подстроки pattern[:i+1],
    который одновременно является её суффиксом.

    Сложность построения:
        - Временная сложность: O(m) — на каждой итерации i значение j может возрасти
          максимум на 1, поэтому суммарное число уменьшений j во внутреннем цикле не превышает m.
        - Пространственная сложность: O(m) для хранения массива pi.
    """
    m = len(pattern)
    if m == 0:
        return []

    pi = [0] * m
    for i in range(1, m):
        j = pi[i - 1]
        while j > 0 and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j

    return pi


def kmp_search(text: str, pattern: str) -> tuple[list[int], int]:
    """Алгоритм Кнута–Морриса–Пратта (КМП).

    Использует префикс-функцию шаблона для предотвращения отката указателя в тексте.
    После нахождения полного вхождения сдвиг продолжается по pi[m-1],
    что гарантирует обнаружение всех перекрывающихся вхождений.

    Сложность:
        - Временная сложность: O(n + m) в худшем и среднем случаях (O(m) на префикс-функцию + O(n) на поиск).
        - Пространственная сложность: O(m) для массива префикс-функции.
    """
    n, m = len(text), len(pattern)
    if m == 0 or n < m:
        return [], 0

    pi = prefix_function(pattern)
    occurrences: list[int] = []
    comparisons = 0
    j = 0  # число совпавших символов шаблона

    for i in range(n):
        while j > 0:
            comparisons += 1
            if text[i] == pattern[j]:
                break
            j = pi[j - 1]

        if j == 0:
            comparisons += 1
            if text[i] == pattern[0]:
                j = 1
        else:
            j += 1

        if j == m:
            occurrences.append(i - m + 1)
            j = pi[m - 1]

    return occurrences, comparisons


def rabin_karp_search(
    text: str, pattern: str, base: int = 256, mod: int = 1_000_000_007
) -> tuple[list[int], int]:
    """Поиск Рабина–Карпа с полиномиальным кольцевым хешем по модулю mod.

    Хеш окна пересчитывается за O(1) с помощью скользящего окна.
    При равенстве хешей выполняется обязательная посимвольная проверка окна
    для устранения ложных срабатываний, вызванных коллизиями хеш-функции.

    Сложность:
        - Средний случай: O(n + m) при редких коллизиях.
        - Худший случай: O(n * m), если все окна дают коллизию с хешем шаблона.
        - Память: O(1) дополнительной памяти.
    """
    n, m = len(text), len(pattern)
    if m == 0 or n < m:
        return [], 0

    occurrences: list[int] = []
    comparisons = 0

    # Старший весовой коэффициент base^(m-1) mod mod
    high_power = pow(base, m - 1, mod)

    pattern_hash = 0
    window_hash = 0
    for i in range(m):
        pattern_hash = (pattern_hash * base + ord(pattern[i])) % mod
        window_hash = (window_hash * base + ord(text[i])) % mod

    for i in range(n - m + 1):
        if window_hash == pattern_hash:
            match = True
            for j in range(m):
                comparisons += 1
                if text[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                occurrences.append(i)

        if i < n - m:
            window_hash = ((window_hash - ord(text[i]) * high_power) * base + ord(text[i + m])) % mod
            window_hash = (window_hash + mod) % mod

    return occurrences, comparisons


def bad_char_table(pattern: str) -> dict[str, int]:
    """Таблица плохого символа: индекс последнего вхождения каждого символа в шаблоне.

    Используется словарь dict[str, int] для универсальной поддержки Юникода.
    """
    return {ch: i for i, ch in enumerate(pattern)}


def suffixes(pattern: str) -> list[int]:
    """Вспомогательный массив суффиксов для эвристики хорошего суффикса.

    suff[i] — длина наибольшего общего суффикса подстроки pattern[:i+1] и pattern.
    Вычисляется за O(m) времени с использованием Z-подобного алгоритма с конца.
    """
    m = len(pattern)
    suff = [0] * m
    suff[m - 1] = m
    g = m - 1
    f = m - 1

    for i in range(m - 2, -1, -1):
        if i > g and suff[i + m - 1 - f] < i - g:
            suff[i] = suff[i + m - 1 - f]
        else:
            if i < g:
                g = i
            f = i
            while g >= 0 and pattern[g] == pattern[g + m - 1 - f]:
                g -= 1
            suff[i] = f - g

    return suff


def good_suffix_table(pattern: str) -> list[int]:
    """Таблица хорошего суффикса для алгоритма Бойера–Мура.

    bm_gs[j] — сдвиг при несовпадении на позиции j шаблона (где суффикс pattern[j+1:] совпал).
    bm_gs[0] — сдвиг после полного совпадения всего шаблона (для перекрывающихся вхождений).
    Время построения: O(m), память: O(m).
    """
    m = len(pattern)
    bm_gs = [m] * m
    suff = suffixes(pattern)

    # Случай 2: префикс шаблона совпадает с суффиксом совпавшего суффикса
    j = 0
    for i in range(m - 1, -1, -1):
        if suff[i] == i + 1:
            while j < m - 1 - i:
                if bm_gs[j] == m:
                    bm_gs[j] = m - 1 - i
                j += 1

    # Случай 1: совпавший суффикс встречается левее в шаблоне
    for i in range(m - 1):
        bm_gs[m - 1 - suff[i]] = m - 1 - i

    return bm_gs


def boyer_moore_search(text: str, pattern: str) -> tuple[list[int], int]:
    """Алгоритм Бойера–Мура с обеими эвристиками: плохого символа и хорошего суффикса.

    Сравнение символов выполняется справа налево (от конца шаблона к началу).
    Сдвиг окна равен максимуму из сдвига по плохому символу и сдвига по хорошему суффиксу.
    При полном совпадении шаблона сдвиг производится по bm_gs[0].

    Сложность:
        - Лучший/средний случай: O(n / m) на больших алфавитах (сублинейная скорость).
        - Худший случай: O(n + m) благодаря эвристике хорошего суффикса (без неё худший O(n*m)).
        - Память: O(m + |Sigma|) для таблиц сдвигов.
    """
    n, m = len(text), len(pattern)
    if m == 0 or n < m:
        return [], 0

    bm_bc = bad_char_table(pattern)
    bm_gs = good_suffix_table(pattern)
    occurrences: list[int] = []
    comparisons = 0

    i = 0  # позиция выравнивания шаблона относительно текста
    while i <= n - m:
        j = m - 1
        while j >= 0:
            comparisons += 1
            if pattern[j] != text[i + j]:
                break
            j -= 1

        if j < 0:
            occurrences.append(i)
            i += bm_gs[0]
        else:
            bad_char = text[i + j]
            bc_shift = j - bm_bc.get(bad_char, -1)
            gs_shift = bm_gs[j]
            i += max(bc_shift, gs_shift)

    return occurrences, comparisons


# ---------------------------------------------------------------------------
# 2. Репрезентативные тесты и инварианты (методика docs/ai-verification.md)
# ---------------------------------------------------------------------------


def reference_occurrences(text: str, pattern: str) -> list[int]:
    """Эталон из стандартной библиотеки Python: str.find со сдвигом на 1."""
    if not pattern:
        return []
    result: list[int] = []
    pos = text.find(pattern)
    while pos != -1:
        result.append(pos)
        pos = text.find(pattern, pos + 1)
    return result


def self_check() -> None:
    """Граничные и типовые случаи + сверка всех алгоритмов с эталоном."""
    # 1. Проверка эталона
    assert reference_occurrences("aaaa", "aa") == [0, 1, 2]
    assert reference_occurrences("abc", "abcd") == []

    # 2. Проверка префикс-функции на классических примерах
    assert prefix_function("abcabcd") == [0, 0, 0, 1, 2, 3, 0]
    assert prefix_function("aabaaab") == [0, 1, 0, 1, 2, 2, 3]

    algorithms = [naive_search, kmp_search, rabin_karp_search, boyer_moore_search]

    # 3. Граничные сценарии для каждого алгоритма
    for search in algorithms:
        name = search.__name__
        occ, _ = search("aaaa", "aa")
        assert occ == [0, 1, 2], f"{name}: перекрывающиеся вхождения теряются"
        occ, _ = search("abc", "abc")
        assert occ == [0], f"{name}: шаблон, равный тексту"
        occ, _ = search("abc", "abcd")
        assert occ == [], f"{name}: шаблон длиннее текста"
        occ, _ = search("", "a")
        assert occ == [], f"{name}: пустой текст"
        occ, _ = search("abc", "")
        assert occ == [], f"{name}: пустой шаблон"
        occ, _ = search("mississippi", "issi")
        assert occ == [1, 4], f"{name}: частичные совпадения mississippi"

    # 4. Проверка устойчивости Рабина–Карпа к коллизиям хешей
    # Искусственно вызываем коллизию через mod = 1 (все хеши совпадают)
    occ_coll, cmps_coll = rabin_karp_search("abacaba", "aba", mod=1)
    assert occ_coll == [0, 4], f"Rabin-Karp collision failure: {occ_coll}"
    assert cmps_coll > 0, "Rabin-Karp must do char comparisons on collisions"

    # 5. Property-based тестирование на случайных строках (малый и средний алфавиты)
    rng = random.Random(0)
    for alphabet in ("ab", "abc", "abcdefghij"):
        for _ in range(150):
            t_len = rng.randint(1, 80)
            p_len = rng.randint(1, 6)
            text = "".join(rng.choice(alphabet) for _ in range(t_len))
            pattern = "".join(rng.choice(alphabet) for _ in range(p_len))
            expected = reference_occurrences(text, pattern)
            for search in algorithms:
                occ, comparisons = search(text, pattern)
                assert occ == expected, (
                    f"{search.__name__}: text={text!r}, pattern={pattern!r}, "
                    f"получено {occ}, ожидалось {expected}"
                )
                assert comparisons >= 0

    print("self_check: OK (все тесты и инварианты пройдены)")


# ---------------------------------------------------------------------------
# 3. Данные по варианту и бенчмарк (методика docs/reproducibility.md)
# ---------------------------------------------------------------------------

TEXT_SIZE = 100_000
PATTERN_LENGTHS = [4, 8, 16, 32, 64]
REPEATS = 5

LEXICON = [
    "data", "search", "pattern", "index", "hash", "log", "event", "system",
    "error", "server", "signal", "buffer", "stream", "packet", "record",
]


def make_small_alphabet_text(rng: random.Random, length: int) -> str:
    """Текст над малым алфавитом {a, b}."""
    return "".join(rng.choice("ab") for _ in range(length))


def make_natural_text(rng: random.Random, length: int) -> str:
    """Естественно-подобный текст: псевдослова лексикона через пробел."""
    words: list[str] = []
    total = 0
    while total < length:
        word = rng.choice(LEXICON)
        words.append(word)
        total += len(word) + 1
    return " ".join(words)[:length]


def plant_pattern(rng: random.Random, text: str, pattern: str, count: int) -> str:
    """Вставить count гарантированных вхождений шаблона в текст."""
    chars = list(text)
    for _ in range(count):
        pos = rng.randrange(0, len(chars) - len(pattern) + 1)
        chars[pos:pos + len(pattern)] = pattern
    return "".join(chars)


def bench(search, text: str, pattern: str) -> float:
    """Медиана времени выполнения search(text, pattern) по REPEATS запускам с прогревом."""
    search(text, pattern)  # прогрев
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        search(text, pattern)
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def plot_results(results: dict, out_dir: Path) -> None:
    """Построение графиков числа сравнений и времени выполнения."""
    if not MATPLOTLIB_AVAILABLE:
        print("Предупреждение: matplotlib недоступен, графики не построены.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    colors = {
        "наивный": "#d62728",      # красный
        "КМП": "#1f77b4",          # синий
        "Рабин–Карп": "#ff7f0e",   # оранжевый
        "Бойер–Мур": "#2ca02c",    # зелёный
    }
    markers = {
        "наивный": "s",
        "КМП": "o",
        "Рабин–Карп": "^",
        "Бойер–Мур": "D",
    }

    # -----------------------------------------------------------------------
    # График 1: Число сравнений символов от длины шаблона m (2 панели)
    # -----------------------------------------------------------------------
    fig1, axes1 = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, text_type in zip(axes1, ("малый алфавит (ab)", "естественно-подобный")):
        for name in ("наивный", "КМП", "Рабин–Карп", "Бойер–Мур"):
            m_vals = results[text_type][name]["lengths"]
            cmps = results[text_type][name]["cmps"]
            ax.plot(
                m_vals, cmps,
                marker=markers[name], color=colors[name],
                linewidth=2.2, label=name
            )
        ax.set_yscale("log")
        ax.set_xlabel("Длина шаблона m", fontsize=11)
        ax.set_ylabel("Число сравнений символов (log)", fontsize=11)
        title_prefix = "Малый алфавит {a, b}" if "малый" in text_type else "Естественно-подобный текст"
        ax.set_title(f"{title_prefix}\n(|T| = 100 000)", fontsize=12, fontweight="bold")
        ax.grid(True, which="both", ls="--", alpha=0.5)
        ax.legend(fontsize=9, loc="upper right")

    fig1.tight_layout()
    p1 = out_dir / "lab07_comparisons.png"
    fig1.savefig(p1, dpi=160)
    plt.close(fig1)
    print(f"График сравнений сохранён: {p1}")

    # -----------------------------------------------------------------------
    # График 2: Время выполнения от длины шаблона m (2 панели)
    # -----------------------------------------------------------------------
    fig2, axes2 = plt.subplots(1, 2, figsize=(14, 5.5))

    for ax, text_type in zip(axes2, ("малый алфавит (ab)", "естественно-подобный")):
        for name in ("наивный", "КМП", "Рабин–Карп", "Бойер–Мур"):
            m_vals = results[text_type][name]["lengths"]
            times = results[text_type][name]["times"]
            ax.plot(
                m_vals, times,
                marker=markers[name], color=colors[name],
                linewidth=2.2, label=name
            )
        ax.set_yscale("log")
        ax.set_xlabel("Длина шаблона m", fontsize=11)
        ax.set_ylabel("Медиана времени выполнения (с, log)", fontsize=11)
        title_prefix = "Малый алфавит {a, b}" if "малый" in text_type else "Естественно-подобный текст"
        ax.set_title(f"{title_prefix}\n(|T| = 100 000)", fontsize=12, fontweight="bold")
        ax.grid(True, which="both", ls="--", alpha=0.5)
        ax.legend(fontsize=9, loc="upper right")

    fig2.tight_layout()
    p2 = out_dir / "lab07_execution_time.png"
    fig2.savefig(p2, dpi=160)
    plt.close(fig2)
    print(f"График времени сохранён: {p2}")


def run_benchmarks(seed: int, out_dir: Path | None = None) -> dict:
    """Выполнение вычислительного эксперимента, вывод таблиц и построение графиков."""
    rng = random.Random(seed)
    texts = {
        "малый алфавит (ab)": make_small_alphabet_text(rng, TEXT_SIZE),
        "естественно-подобный": make_natural_text(rng, TEXT_SIZE),
    }
    algorithms = [
        ("наивный", naive_search),
        ("КМП", kmp_search),
        ("Рабин–Карп", rabin_karp_search),
        ("Бойер–Мур", boyer_moore_search),
    ]

    results: dict = {
        text_type: {
            name: {"lengths": [], "cmps": [], "times": [], "occ": []}
            for name, _ in algorithms
        }
        for text_type in texts
    }

    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ СРАВНИТЕЛЬНОГО БЕНЧМАРКИНГА (seed = {})".format(seed))
    print("=" * 80)

    for text_name, text in texts.items():
        print(f"\n--- Текст: {text_name.upper()} (|T| = {len(text)}) ---")
        print(f"{'m':>4} | {'алгоритм':<13} | {'вхождений':>10} | {'сравнений':>11} | {'время, с':>12} | {'отн. сравнений (cmps/|T|)':>26}")
        print("-" * 84)

        for m in PATTERN_LENGTHS:
            start = rng.randrange(0, len(text) - m + 1)
            pattern = text[start:start + m]
            sample = plant_pattern(rng, text, pattern, 5)

            for name, search in algorithms:
                occurrences, comparisons = search(sample, pattern)
                t = bench(search, sample, pattern)

                results[text_name][name]["lengths"].append(m)
                results[text_name][name]["cmps"].append(comparisons)
                results[text_name][name]["times"].append(t)
                results[text_name][name]["occ"].append(len(occurrences))

                ratio = comparisons / len(sample)
                print(f"{m:>4} | {name:<13} | {len(occurrences):>10} | {comparisons:>11} | {t:>12.6f} | {ratio:>26.4f}")

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
