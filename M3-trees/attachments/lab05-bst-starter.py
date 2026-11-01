#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ЛР 5. Бинарное дерево поиска: обходы, вставка и удаление.

Реализация бинарного дерева поиска (BST) с операциями вставки, поиска и удаления
(включая случай узла с двумя детьми через симметричного преемника), рекурсивными
и итеративными обходами, вычислением высоты и размера, верификацией инварианта
и бенчмаркингом поиска в сравнении со списком.

Запуск:
    python lab05-bst-starter.py --variant 21
    python lab05-bst-starter.py --variant 21 --out ../../reports/images
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import random
import statistics
import sys
import time
from collections import deque

import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 1. Бинарное дерево поиска (реализуется вручную, без сторонних библиотек)
# ---------------------------------------------------------------------------


class Node:
    """Узел BST: ключ и ссылки на левое и правое поддеревья."""

    __slots__ = ("key", "left", "right")

    def __init__(self, key: int) -> None:
        self.key = key
        self.left: Node | None = None
        self.right: Node | None = None


class BST:
    """Бинарное дерево поиска без дубликатов ключей.

    Инвариант: для каждого узла все ключи левого поддерева строго меньше key,
    все ключи правого — строго больше.
    Временная сложность операций insert, search, delete составляет O(h),
    где h — высота дерева: в сбалансированном дереве h = O(log n),
    в вырожденном дереве (списке) h = O(n).
    """

    def __init__(self) -> None:
        self.root: Node | None = None
        self._size: int = 0

    def insert(self, key: int) -> None:
        """Вставка ключа; повторная вставка существующего ключа игнорируется."""
        if self.root is None:
            self.root = Node(key)
            self._size = 1
            return

        curr = self.root
        while True:
            if key == curr.key:
                return  # Повторная вставка игнорируется
            elif key < curr.key:
                if curr.left is None:
                    curr.left = Node(key)
                    self._size += 1
                    return
                curr = curr.left
            else:
                if curr.right is None:
                    curr.right = Node(key)
                    self._size += 1
                    return
                curr = curr.right

    def search(self, key: int) -> bool:
        """Возвращает True, если ключ есть в дереве."""
        curr = self.root
        while curr is not None:
            if key == curr.key:
                return True
            elif key < curr.key:
                curr = curr.left
            else:
                curr = curr.right
        return False

    def delete(self, key: int) -> None:
        """Удаление ключа. Обработать три случая:

        1) лист — просто отцепить от родителя;
        2) один ребёнок — заменить узел его ребёнком;
        3) два ребёнка — заменить ключ преемником (минимум правого
           поддерева) и удалить преемника из правого поддерева.
        Отсутствующий ключ игнорируется.
        """
        deleted = False

        def _delete(node: Node | None, k: int) -> Node | None:
            nonlocal deleted
            if node is None:
                return None
            if k < node.key:
                node.left = _delete(node.left, k)
            elif k > node.key:
                node.right = _delete(node.right, k)
            else:
                deleted = True
                # Случай 1: Лист (нет потомков)
                if node.left is None and node.right is None:
                    return None
                # Случай 2: Ровно один потомок
                if node.left is None:
                    return node.right
                if node.right is None:
                    return node.left
                # Случай 3: Два потомка — замена преемником (минимум правого поддерева)
                successor = node.right
                while successor.left is not None:
                    successor = successor.left
                node.key = successor.key
                node.right = _delete(node.right, successor.key)
            return node

        self.root = _delete(self.root, key)
        if deleted:
            self._size -= 1

    # -- Обходы --------------------------------------------------------------

    def in_order(self) -> list[int]:
        """Симметричный обход (лево — узел — право): рекурсивно."""
        res: list[int] = []

        def _traverse(node: Node | None) -> None:
            if node is not None:
                _traverse(node.left)
                res.append(node.key)
                _traverse(node.right)

        _traverse(self.root)
        return res

    def pre_order(self) -> list[int]:
        """Прямой обход (узел — лево — право): рекурсивно."""
        res: list[int] = []

        def _traverse(node: Node | None) -> None:
            if node is not None:
                res.append(node.key)
                _traverse(node.left)
                _traverse(node.right)

        _traverse(self.root)
        return res

    def post_order(self) -> list[int]:
        """Обратный обход (лево — право — узел): рекурсивно."""
        res: list[int] = []

        def _traverse(node: Node | None) -> None:
            if node is not None:
                _traverse(node.left)
                _traverse(node.right)
                res.append(node.key)

        _traverse(self.root)
        return res

    def level_order(self) -> list[int]:
        """Обход в ширину по уровням: итеративно через очередь (deque)."""
        if self.root is None:
            return []
        res: list[int] = []
        queue: deque[Node] = deque([self.root])
        while queue:
            node = queue.popleft()
            res.append(node.key)
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)
        return res

    # -- Характеристики дерева ----------------------------------------------

    def height(self) -> int:
        """Высота дерева: число рёбер на самом длинном пути от корня.

        Пустое дерево имеет высоту -1, дерево из одного узла — 0.
        Итеративная реализация исключает переполнение стека (RecursionError)
        даже на предельно вырожденных деревьях глубиной до 10^5.
        """
        if self.root is None:
            return -1
        max_depth = 0
        stack: list[tuple[Node, int]] = [(self.root, 0)]
        while stack:
            curr, depth = stack.pop()
            if depth > max_depth:
                max_depth = depth
            if curr.right is not None:
                stack.append((curr.right, depth + 1))
            if curr.left is not None:
                stack.append((curr.left, depth + 1))
        return max_depth

    def size(self) -> int:
        """Число узлов в дереве."""
        return self._size


# ---------------------------------------------------------------------------
# 2. Верификация: инвариант BST и сверка с эталоном (docs/ai-verification.md)
# ---------------------------------------------------------------------------


def self_check() -> None:
    """Граничные случаи + сверка операций с эталоном set/sorted."""
    # Пустое дерево
    t = BST()
    assert t.search(1) is False
    assert t.in_order() == []
    assert t.height() == -1 and t.size() == 0
    t.delete(1)  # удаление из пустого дерева не должно падать

    # Один узел
    t.insert(5)
    assert t.search(5) and not t.search(4)
    assert t.height() == 0 and t.size() == 1

    # Три случая удаления на маленьком дереве: 5, 2, 8, 1, 3
    for k in (2, 8, 1, 3):
        t.insert(k)
    t.delete(1)                       # лист
    assert t.in_order() == [2, 3, 5, 8]
    t.delete(2)                       # узел с одним ребёнком
    assert t.in_order() == [3, 5, 8]
    t.delete(5)                       # корень с двумя детьми (через преемника)
    assert t.in_order() == [3, 8]

    # Обходы на известном дереве 4-2-6-1-3-5-7 (вставка по уровням)
    t2 = BST()
    for k in (4, 2, 6, 1, 3, 5, 7):
        t2.insert(k)
    assert t2.in_order() == [1, 2, 3, 4, 5, 6, 7]
    assert t2.pre_order() == [4, 2, 1, 3, 6, 5, 7]
    assert t2.post_order() == [1, 3, 2, 5, 7, 6, 4]
    assert t2.level_order() == [4, 2, 6, 1, 3, 5, 7]
    assert t2.height() == 2 and t2.size() == 7

    # Случайные последовательности команд: сверка с эталоном из stdlib
    rng = random.Random(0)
    for _ in range(100):
        t3 = BST()
        etalon: set[int] = set()
        for _ in range(rng.randint(1, 80)):
            k = rng.randint(-30, 30)
            if rng.random() < 0.6:
                t3.insert(k)
                etalon.add(k)
            else:
                t3.delete(k)
                etalon.discard(k)
            # Инвариант BST: in-order даёт отсортированную последовательность
            assert t3.in_order() == sorted(etalon)
        for k in range(-30, 31):
            assert t3.search(k) == (k in etalon)
        assert t3.size() == len(etalon)
    print("self_check: OK")


# ---------------------------------------------------------------------------
# 3. Бенчмарк: поиск в BST против поиска в списке (docs/reproducibility.md)
# ---------------------------------------------------------------------------

SIZES = [1_000, 3_000, 10_000, 30_000, 100_000]
REPEATS = 5
QUERIES = 1_000  # число поисков на один замер


def bench(fn) -> float:
    """Медиана времени выполнения fn() по REPEATS запускам, с прогревом."""
    fn()  # прогрев — не учитывается
    times = []
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times)


def plot_results(
    sizes: list[int],
    h_bst_list: list[int],
    t_bst_list: list[float],
    t_list_list: list[float],
    out_dir: Path,
) -> None:
    """Построение графиков для отчёта."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Сравнение времени поиска
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.plot(sizes, t_bst_list, "o-", color="#1f77b4", linewidth=2, markersize=7, label="BST search (1000 запросов)")
    ax1.plot(sizes, t_list_list, "s-", color="#d62728", linewidth=2, markersize=7, label="List search (in, 1000 запросов)")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Размер структуры $n$", fontsize=12)
    ax1.set_ylabel("Медианное время выполнения, с (log)", fontsize=12)
    ax1.set_title("Время поиска в BST и Списке (Log-Log шкала)\nВариант 21, seed = 51", fontsize=13, fontweight="bold")
    ax1.grid(True, which="both", ls="--", alpha=0.5)
    ax1.legend(fontsize=11)

    log_x = [math.log10(x) for x in sizes]
    log_y_list = [math.log10(y) for y in t_list_list]
    k_list, _ = statistics.linear_regression(log_x, log_y_list)
    log_y_bst = [math.log10(y) for y in t_bst_list]
    k_bst, _ = statistics.linear_regression(log_x, log_y_bst)

    ax1.text(
        0.05,
        0.85,
        f"Наклон Списка $k = {k_list:.2f} \\approx 1.0$ ($O(n)$)\nНаклон BST $k = {k_bst:.2f}$ ($O(\\log n)$)",
        transform=ax1.transAxes,
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.8),
    )

    speedups = [tl / tb if tb > 0 else 0 for tb, tl in zip(t_bst_list, t_list_list)]
    ax2.plot(sizes, t_bst_list, "o-", color="#1f77b4", linewidth=2, label="BST search, с")
    ax2.plot(sizes, t_list_list, "s-", color="#d62728", linewidth=2, label="List search, с")
    ax2.set_xlabel("Размер структуры $n$", fontsize=12)
    ax2.set_ylabel("Время выполнения, с", fontsize=12)
    ax2.set_title("Время поиска и ускорение BST относительно списка", fontsize=13, fontweight="bold")
    ax2.grid(True, ls="--", alpha=0.5)

    ax2_twin = ax2.twinx()
    ax2_twin.plot(sizes, speedups, "^--", color="#2ca02c", linewidth=2, markersize=8, label="Ускорение (List / BST)")
    ax2_twin.set_ylabel("Кратность ускорения ($x$ раз)", color="#2ca02c", fontsize=12)
    ax2_twin.tick_params(axis="y", labelcolor="#2ca02c")

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="center left", fontsize=10)

    fig.tight_layout()
    p1 = out_dir / "lab05_search_comparison.png"
    fig.savefig(p1, dpi=150)
    plt.close(fig)
    print(f"График сохранён: {p1}")

    # 2. Высота случайного дерева и теоретические оценки
    fig2, ax3 = plt.subplots(figsize=(8, 6))
    avl_bound = [1.4404 * math.log2(n) for n in sizes]
    perfect_bound = [math.ceil(math.log2(n + 1)) - 1 for n in sizes]
    random_theory = [2.9882 * math.log(n) for n in sizes]

    ax3.plot(sizes, h_bst_list, "o-", color="#1f77b4", linewidth=2, markersize=7, label="Фактическая высота $h(BST)$ (рандом)")
    ax3.plot(sizes, avl_bound, "--", color="#ff7f0e", linewidth=1.8, label="Граница AVL: $1.44 \\cdot \\log_2(n)$")
    ax3.plot(sizes, random_theory, ":", color="#2ca02c", linewidth=1.8, label="Теория случайного BST: $\\approx 2.99 \\ln(n)$")
    ax3.plot(sizes, perfect_bound, "-.", color="#7f7f7f", linewidth=1.5, label="Идеально сбалансированное: $\\lceil\\log_2(n+1)\\rceil - 1$")
    ax3.set_xscale("log")
    ax3.set_xlabel("Число элементов $n$ (log)", fontsize=12)
    ax3.set_ylabel("Высота дерева $h$ (число рёбер)", fontsize=12)
    ax3.set_title("Высота случайного BST и теоретические границы\n(дерево глубиной $O(\\log n)$)", fontsize=13, fontweight="bold")
    ax3.grid(True, which="both", ls="--", alpha=0.5)
    ax3.legend(fontsize=10)

    fig2.tight_layout()
    p2 = out_dir / "lab05_height_and_degradation.png"
    fig2.savefig(p2, dpi=150)
    plt.close(fig2)
    print(f"График сохранён: {p2}")


def run_benchmarks(seed: int, out_dir: Path | None = None) -> None:
    """Сравнение времени QUERIES поисков в BST и в списке (оператор in)."""
    rng = random.Random(seed)
    h_bst_list: list[int] = []
    t_bst_list: list[float] = []
    t_list_list: list[float] = []

    print(f"{'n':>8} {'h(BST)':>7} {'t_bst, c':>10} {'t_list, c':>10} {'speedup':>10}")
    for n in SIZES:
        keys = rng.sample(range(10 * n), n)   # случайные ключи без повторов
        queries = [rng.randint(0, 10 * n) for _ in range(QUERIES)]
        tree = BST()
        for k in keys:
            tree.insert(k)

        def search_bst() -> None:
            for q in queries:
                tree.search(q)

        def search_list() -> None:
            for q in queries:
                q in keys  # линейный поиск для сравнения

        t_bst = bench(search_bst)
        t_list = bench(search_list)
        h = tree.height()
        speedup = t_list / t_bst if t_bst > 0 else 0

        h_bst_list.append(h)
        t_bst_list.append(t_bst)
        t_list_list.append(t_list)

        print(f"{n:>8} {h:>7} {t_bst:>10.6f} {t_list:>10.6f} {speedup:>9.1f}x")

    if out_dir is not None:
        plot_results(SIZES, h_bst_list, t_bst_list, t_list_list, out_dir)


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
    seed = 30 + args.variant  # seed по варианту — см. docs/reproducibility.md
    random.seed(seed)
    self_check()

    out_dir = args.out
    if out_dir is None:
        out_dir = Path(__file__).resolve().parent.parent.parent / "reports" / "images"

    run_benchmarks(seed, out_dir)


if __name__ == "__main__":
    main()
