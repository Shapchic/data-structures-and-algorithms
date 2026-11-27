#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 8. Хеш-таблица с отдельным цепочечным хешированием.

Реализация ассоциативного массива на базе отдельных цепочек:
- полиномиальная хеш-функция poly_hash по схеме Горнера (основание P = 31);
- заведомо плохая хеш-функция bad_hash (по первому символу) для эксперимента;
- класс HashTable с операциями put, get, delete, __len__ и автоматическим
  rehash (удвоение числа бакетов) при load_factor > 0.75;
- верификация инвариантов и сверка с эталоном dict;
- сравнительные эксперименты: гистограммы длин цепочек и время от α.

Запуск:
    python lab08-hash-table-starter.py --variant 21
    python lab08-hash-table-starter.py --variant 21 --out ../../reports/images
"""
from __future__ import annotations

import argparse
from pathlib import Path
import random
import statistics
import string
import sys
import time

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# ---------------------------------------------------------------------------
# 1. Хеш-функции для строковых ключей
# ---------------------------------------------------------------------------

P = 31  # основание полинома (простое число, близкое к размеру латинского алфавита)


def poly_hash(key: str, mod: int) -> int:
    """Полиномиальный хеш строки по модулю mod (схема Горнера).

    h(s) = (s[0]·P^(k-1) + s[1]·P^(k-2) + … + s[k-1]) mod mod,
    где s[i] — код символа ord(ch). Взятие остатка на каждом шаге
    предотвращает рост промежуточных чисел и обеспечивает время O(k),
    где k = len(key), и равномерное распределение по бакетам.
    """
    h = 0
    for ch in key:
        h = (h * P + ord(ch)) % mod
    return h


def bad_hash(key: str, mod: int) -> int:
    """Заведомо плохая хеш-функция: только первый символ ключа.

    Все ключи с общим первым символом попадают в один бакет — используется
    в эксперименте с гистограммой длин цепочек как контрпример.
    """
    return (ord(key[0]) if key else 0) % mod


# ---------------------------------------------------------------------------
# 2. Хеш-таблица с отдельными цепочками
# ---------------------------------------------------------------------------


class HashTable:
    """Хеш-таблица: бакеты — списки пар (ключ, значение) (отдельные цепочки).

    Инварианты (проверяются в check_invariants):
      1) каждая пара лежит в бакете с индексом hash_fn(ключ, число бакетов);
      2) сумма длин всех цепочек равна len(таблицы);
      3) ключи внутри таблицы не повторяются.
    """

    INITIAL_CAPACITY = 8

    def __init__(
        self,
        capacity: int = INITIAL_CAPACITY,
        hash_fn=poly_hash,
        max_load_factor: float = 0.75,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity должен быть положительным")
        self._buckets: list[list[tuple[str, object]]] = [[] for _ in range(capacity)]
        self._size = 0
        self._hash_fn = hash_fn
        # max_load_factor=float("inf") отключает rehash — нужно в эксперименте,
        # где коэффициент загрузки задаётся вручную
        self._max_load_factor = max_load_factor

    def _bucket_index(self, key: str) -> int:
        """Индекс бакета для ключа при текущем числе бакетов."""
        return self._hash_fn(key, len(self._buckets))

    @property
    def load_factor(self) -> float:
        """Коэффициент загрузки α = размер / число бакетов."""
        return self._size / len(self._buckets)

    def put(self, key: str, value: object) -> None:
        """Вставить пару или обновить значение существующего ключа.

        После вставки нового ключа при load_factor > max_load_factor
        выполняется _rehash().
        Сложность:
            - Средняя: O(1 + α) — при α <= 0.75 и хорошей хеш-функции O(1) амортизированно.
            - Худшая: O(n) — все ключи попали в одну цепочку (или момент rehash).
        """
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        for i, (existing_key, _existing_val) in enumerate(bucket):
            if existing_key == key:
                bucket[i] = (key, value)
                return

        bucket.append((key, value))
        self._size += 1
        if self.load_factor > self._max_load_factor:
            self._rehash()

    def get(self, key: str, default: object = None) -> object:
        """Вернуть значение по ключу или default, если ключа нет.

        Сложность: O(1 + α) в среднем, O(n) в худшем случае.
        """
        idx = self._bucket_index(key)
        for existing_key, value in self._buckets[idx]:
            if existing_key == key:
                return value
        return default

    def delete(self, key: str) -> None:
        """Удалить ключ; если ключа нет — возбудить KeyError.

        Сложность: O(1 + α) в среднем, O(n) в худшем случае.
        """
        idx = self._bucket_index(key)
        bucket = self._buckets[idx]
        for i, (existing_key, _value) in enumerate(bucket):
            if existing_key == key:
                bucket.pop(i)
                self._size -= 1
                return
        raise KeyError(key)

    def __len__(self) -> int:
        return self._size

    def _rehash(self) -> None:
        """Удвоить число бакетов и заново распределить все пары.

        Время: O(n + M), где M — текущее число бакетов.
        """
        new_capacity = len(self._buckets) * 2
        new_buckets: list[list[tuple[str, object]]] = [[] for _ in range(new_capacity)]
        for bucket in self._buckets:
            for key, value in bucket:
                new_idx = self._hash_fn(key, new_capacity)
                new_buckets[new_idx].append((key, value))
        self._buckets = new_buckets

    def chain_lengths(self) -> list[int]:
        """Длины всех цепочек — сырьё для гистограммы."""
        return [len(bucket) for bucket in self._buckets]


# ---------------------------------------------------------------------------
# 3. Верификация: инварианты, граничные случаи, сверка с dict
# ---------------------------------------------------------------------------


def check_invariants(table: HashTable) -> None:
    """Программная проверка инвариантов таблицы (см. docstring HashTable)."""
    n_buckets = len(table._buckets)
    seen: set[str] = set()
    for i, bucket in enumerate(table._buckets):
        for key, _value in bucket:
            assert table._hash_fn(key, n_buckets) == i, (
                f"ключ {key!r} лежит не в своём бакете"
            )
            assert key not in seen, f"ключ {key!r} встречается дважды"
            seen.add(key)
    assert sum(table.chain_lengths()) == len(table), (
        "сумма длин цепочек не равна размеру таблицы"
    )


def random_keys(rng: random.Random, n: int, length: int = 8) -> list[str]:
    """n различных случайных строковых ключей фиксированной длины."""
    keys: set[str] = set()
    while len(keys) < n:
        keys.add("".join(rng.choice(string.ascii_lowercase) for _ in range(length)))
    return list(keys)


def self_check() -> None:
    """Граничные и типовые случаи + сверка поведения с эталоном dict."""
    # 1. Базовые операции и граничные случаи
    t = HashTable()
    assert len(t) == 0
    assert t.get("нет") is None
    assert t.get("нет", -1) == -1

    # Пустой строковый ключ, Юникод и хранение None как значения
    t.put("", "empty")
    t.put("ключ_юникод", 42)
    t.put("none_val", None)
    assert t.get("") == "empty"
    assert t.get("ключ_юникод") == 42
    assert t.get("none_val", "MISSING") is None

    # Обновление существующего ключа не создаёт дубликат
    t.put("a", 1)
    t.put("a", 2)
    assert t.get("a") == 2
    assert len(t) == 4
    check_invariants(t)

    # Удаление существующего и несуществующего ключа
    t.delete("a")
    assert t.get("a") is None
    assert len(t) == 3
    try:
        t.delete("a")
        raise AssertionError("delete отсутствующего ключа обязан дать KeyError")
    except KeyError:
        pass

    # 2. Проверка удаления из начала, середины и конца длинной коллизионной цепочки
    coll_table = HashTable(capacity=1, max_load_factor=float("inf"))
    for ch in ("k1", "k2", "k3", "k4"):
        coll_table.put(ch, ch)
    coll_table.delete("k2")  # середина
    coll_table.delete("k1")  # начало
    coll_table.delete("k4")  # конец
    assert len(coll_table) == 1 and coll_table.get("k3") == "k3"
    check_invariants(coll_table)

    # 3. rehash: после массовой вставки α не превышает порога, ключи не теряются
    t = HashTable()
    rng = random.Random(0)
    inserted = random_keys(rng, 200)
    for idx, key in enumerate(inserted):
        t.put(key, idx)
    assert len(t) == 200
    assert t.load_factor <= t._max_load_factor
    for idx, key in enumerate(inserted):
        assert t.get(key) == idx
    check_invariants(t)

    # 4. Сверка с dict на последовательности случайных операций
    t, etalon = HashTable(), {}
    keys = random_keys(rng, 40)
    for _ in range(2500):
        key, op = rng.choice(keys), rng.random()
        if op < 0.5:
            value = rng.randint(0, 999)
            t.put(key, value)
            etalon[key] = value
        elif op < 0.8:
            assert t.get(key, -1) == etalon.get(key, -1)
        elif key in etalon:
            t.delete(key)
            del etalon[key]
        else:
            try:
                t.delete(key)
                raise AssertionError("ожидался KeyError при удалении отсутствующего ключа")
            except KeyError:
                pass
        assert len(t) == len(etalon)
    check_invariants(t)
    print("self_check: OK (все инварианты и сверка с dict пройдены)")


# ---------------------------------------------------------------------------
# 4. Эксперимент: гистограмма длин цепочек для двух хеш-функций
# ---------------------------------------------------------------------------


def plot_chain_histograms(
    poly_lengths: list[int],
    bad_lengths: list[int],
    capacity: int,
    n_keys: int,
    out_dir: Path,
) -> None:
    """Построение гистограмм длин цепочек для poly_hash и bad_hash."""
    if not MATPLOTLIB_AVAILABLE:
        print("Предупреждение: matplotlib недоступен, гистограмма не построена.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Левая панель: poly_hash
    ax0 = axes[0]
    max_poly = max(poly_lengths)
    bins_poly = range(0, max_poly + 2)
    ax0.hist(
        poly_lengths,
        bins=bins_poly,
        align="left",
        rwidth=0.82,
        color="#1f77b4",
        edgecolor="#0f3c5c",
        alpha=0.88,
    )
    mean_len = n_keys / capacity
    ax0.axvline(
        mean_len,
        color="#d62728",
        linestyle="--",
        linewidth=2,
        label=f"Среднее λ = {mean_len:.2f}",
    )
    ax0.set_title(
        f"Хорошая хеш-функция (poly_hash)\n"
        f"max = {max_poly}, пустых = {poly_lengths.count(0)} из {capacity}, "
        f"σ = {statistics.stdev(poly_lengths):.2f}",
        fontsize=11.5,
        fontweight="bold",
    )
    ax0.set_xlabel("Длина цепочки (элементов в бакете)", fontsize=10.5)
    ax0.set_ylabel("Число бакетов", fontsize=10.5)
    ax0.set_xticks(range(0, max_poly + 1))
    ax0.grid(True, axis="y", linestyle="--", alpha=0.5)
    ax0.legend(fontsize=9.5)

    # Правая панель: bad_hash
    ax1 = axes[1]
    max_bad = max(bad_lengths)
    ax1.hist(
        bad_lengths,
        bins=25,
        color="#d62728",
        edgecolor="#6e1010",
        alpha=0.85,
    )
    ax1.set_yscale("log")
    ax1.set_title(
        f"Плохая хеш-функция (bad_hash, по 1-му символу)\n"
        f"max = {max_bad}, пустых = {bad_lengths.count(0)} из {capacity}, "
        f"σ = {statistics.stdev(bad_lengths):.2f}",
        fontsize=11.5,
        fontweight="bold",
    )
    ax1.set_xlabel("Длина цепочки (элементов в бакете)", fontsize=10.5)
    ax1.set_ylabel("Число бакетов (лог. шкала)", fontsize=10.5)
    ax1.grid(True, which="both", linestyle="--", alpha=0.5)

    fig.suptitle(
        f"Распределение длин цепочек (N = {n_keys} ключей, бакетов = {capacity})",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    out_path = out_dir / "lab08_chain_lengths.png"
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"Гистограмма длин цепочек сохранена: {out_path}")


def chain_length_experiment(
    seed: int,
    n_keys: int = 2000,
    capacity: int = 512,
    out_dir: Path | None = None,
) -> dict[str, list[int]]:
    """Распределение длин цепочек: poly_hash против bad_hash на одном наборе ключей."""
    rng = random.Random(seed)
    keys = random_keys(rng, n_keys)
    collected: dict[str, list[int]] = {}

    print("\n" + "=" * 78)
    print(f"ЭКСПЕРИМЕНТ 1: РАСПРЕДЕЛЕНИЕ ДЛИН ЦЕПОЧЕК (seed={seed}, keys={n_keys}, buckets={capacity})")
    print("=" * 78)

    for name, fn in [("poly_hash", poly_hash), ("bad_hash", bad_hash)]:
        # ёмкость фиксирована (rehash отключён), чтобы гистограммы были сравнимы
        table = HashTable(capacity=capacity, hash_fn=fn, max_load_factor=float("inf"))
        for key in keys:
            table.put(key, 0)
        check_invariants(table)
        lengths = table.chain_lengths()
        collected[name] = lengths
        print(
            f"  {name:<10} | max = {max(lengths):>3} | min = {min(lengths):>2} | "
            f"пустых = {lengths.count(0):>3}/{capacity} | "
            f"mean = {statistics.mean(lengths):.3f} | stdev = {statistics.stdev(lengths):.3f}"
        )

    if out_dir is not None:
        plot_chain_histograms(
            collected["poly_hash"],
            collected["bad_hash"],
            capacity,
            n_keys,
            out_dir,
        )

    return collected


# ---------------------------------------------------------------------------
# 5. Бенчмарк: среднее время операций от α (методика — docs/reproducibility.md)
# ---------------------------------------------------------------------------

ALPHAS = [0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 4.0, 8.0]
CAPACITY = 4096  # фиксированная ёмкость: α регулируется числом ключей
N_PROBES = 10000  # число операций в одном замере
REPEATS = 9


def bench(fn) -> float:
    """Медиана времени выполнения fn() по REPEATS запускам, с прогревом."""
    fn()  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def plot_time_vs_alpha(results: dict, out_dir: Path) -> None:
    """Построение графиков зависимости времени операций от коэффициента загрузки α."""
    if not MATPLOTLIB_AVAILABLE:
        print("Предупреждение: matplotlib недоступен, график времени не построен.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    alphas = results["alphas"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Левая панель: HashTable get_hit, get_miss, put от α (линейный масштаб)
    ax0 = axes[0]
    ax0.plot(alphas, results["ht_get_hit"], marker="o", linewidth=2.2, color="#1f77b4", label="HashTable.get (есть)")
    ax0.plot(alphas, results["ht_get_miss"], marker="s", linewidth=2.2, color="#ff7f0e", label="HashTable.get (нет)")
    ax0.plot(alphas, results["ht_put"], marker="^", linewidth=2.2, color="#2ca02c", label="HashTable.put (обновление)")
    ax0.axvline(0.75, color="#d62728", linestyle="--", linewidth=1.8, label="Порог rehash α = 0.75")
    ax0.set_title("HashTable: влияние α на время операций\n(rehash отключён, capacity = 4096)", fontsize=11.5, fontweight="bold")
    ax0.set_xlabel("Коэффициент загрузки α = n / capacity", fontsize=10.5)
    ax0.set_ylabel("Время 1 операции (мкс)", fontsize=10.5)
    ax0.grid(True, linestyle="--", alpha=0.5)
    ax0.legend(fontsize=9, loc="upper left")

    # Правая панель: HashTable против dict (лог. шкала по Y)
    ax1 = axes[1]
    ax1.plot(alphas, results["ht_get_hit"], marker="o", linewidth=2.2, color="#1f77b4", label="HashTable.get")
    ax1.plot(alphas, results["ht_put"], marker="^", linewidth=2.2, color="#2ca02c", label="HashTable.put")
    ax1.plot(alphas, results["dict_get"], marker="o", linestyle="--", linewidth=2.0, color="#d62728", label="Python dict.get")
    ax1.plot(alphas, results["dict_put"], marker="^", linestyle="--", linewidth=2.0, color="#9467bd", label="Python dict[k] = v")
    ax1.set_yscale("log")
    ax1.set_title("HashTable (Python) против встроенного dict (C)\n(логарифмическая шкала времени)", fontsize=11.5, fontweight="bold")
    ax1.set_xlabel("Коэффициент загрузки α", fontsize=10.5)
    ax1.set_ylabel("Время 1 операции (мкс, log)", fontsize=10.5)
    ax1.grid(True, which="both", linestyle="--", alpha=0.5)
    ax1.legend(fontsize=9, loc="center right")

    fig.tight_layout()
    out_path = out_dir / "lab08_time_vs_alpha.png"
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"График времени от α сохранён: {out_path}")


def run_benchmarks(seed: int, out_dir: Path | None = None) -> dict:
    """Среднее время get/put при разных α + сравнение со встроенным dict."""
    rng = random.Random(seed)
    results: dict = {
        "alphas": [],
        "ht_get_hit": [],
        "ht_get_miss": [],
        "ht_put": [],
        "dict_get": [],
        "dict_put": [],
    }

    print("\n" + "=" * 86)
    print(f"ЭКСПЕРИМЕНТ 2: ВРЕМЯ ОПЕРАЦИЙ ОТ α (мкс/оп., capacity={CAPACITY}, probes={N_PROBES})")
    print("=" * 86)
    print(f"{'α':>5} | {'n':>6} | {'HT get(hit)':>11} | {'HT get(miss)':>12} | {'dict get':>9} | {'HT put':>9} | {'dict put':>9}")
    print("-" * 86)

    for alpha in ALPHAS:
        n = int(CAPACITY * alpha)
        keys = random_keys(rng, n)
        miss_keys = [f"MISS{i:04d}" for i in range(N_PROBES)]
        table = HashTable(capacity=CAPACITY, max_load_factor=float("inf"))
        etalon: dict[str, int] = {}
        for key in keys:
            table.put(key, 0)
            etalon[key] = 0
        probes = [rng.choice(keys) for _ in range(N_PROBES)]

        def probe_ht_get_hit() -> None:
            for key in probes:
                table.get(key)

        def probe_ht_get_miss() -> None:
            for key in miss_keys:
                table.get(key)

        def probe_ht_put() -> None:
            for key in probes:
                table.put(key, 1)

        def probe_dict_get() -> None:
            for key in probes:
                etalon.get(key)

        def probe_dict_put() -> None:
            for key in probes:
                etalon[key] = 1

        t_ht_hit = bench(probe_ht_get_hit) / N_PROBES * 1e6
        t_ht_miss = bench(probe_ht_get_miss) / N_PROBES * 1e6
        t_ht_put = bench(probe_ht_put) / N_PROBES * 1e6
        t_dict_get = bench(probe_dict_get) / N_PROBES * 1e6
        t_dict_put = bench(probe_dict_put) / N_PROBES * 1e6

        results["alphas"].append(alpha)
        results["ht_get_hit"].append(t_ht_hit)
        results["ht_get_miss"].append(t_ht_miss)
        results["ht_put"].append(t_ht_put)
        results["dict_get"].append(t_dict_get)
        results["dict_put"].append(t_dict_put)

        print(
            f"{alpha:>5.2f} | {n:>6} | {t_ht_hit:>11.3f} | {t_ht_miss:>12.3f} | "
            f"{t_dict_get:>9.3f} | {t_ht_put:>9.3f} | {t_dict_put:>9.3f}"
        )

    if out_dir is not None:
        plot_time_vs_alpha(results, out_dir)

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

    chain_length_experiment(seed, out_dir=out_dir)
    run_benchmarks(seed, out_dir=out_dir)


if __name__ == "__main__":
    main()
