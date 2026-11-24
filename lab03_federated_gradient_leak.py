#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验 3：联邦学习「梯度泄露」最小复现 —— 训练期安全
用法：python3 lab03_federated_gradient_leak.py
仅需 numpy（数值计算）。零 torch。

为什么这个实验重要：
  lab01/02 打的是「推理期」LLM 提示注入；本实验打「训练期」——
  联邦学习里客户端只上传「梯度」，不传原始数据，看似安全，
  但梯度本身携带数据信息，恶意服务器可从梯度反演原始样本。
  这正是港大 Ka-Ho Chow 研究计划的核心（梯度反演泄露 + 加噪防御权衡）。

原理（线性回归 y = w·x + b，MSE loss，单样本）：
  r = g_b/2 = (w·x + b) - y          ← bias 梯度泄露残差
  g_w = 2·r·x  →  x = g_w / g_b      ← 权重梯度方向直接指向数据
  y = w·x + b - g_b/2                 ← 代回得标签
  结论：单样本时梯度可「精确」反演出原始数据，无需任何优化。
"""
import numpy as np

# 联邦学习公开信息：模型参数（服务器/攻击者已知）
w = np.array([0.6, -1.2, 0.9, 2.1, -0.4])   # 权重向量 d=5
b = 0.35

# 客户端私有数据：真实样本（攻击者不知道，要偷的）
x_true = np.array([1.5, -2.0, 0.8, 3.3, -0.7])
y_true = 3.5   # 真实标签（客户端私有观测值），与模型预测 w·x+b 存在残差

def grad_of(x, y):
    """手写 MSE 梯度：loss=(w·x+b-y)^2 → g_w, g_b"""
    r = float(w @ x + b - y)          # 残差
    g_w = 2 * r * x                   # 对 w 的梯度（向量）
    g_b = 2 * r                       # 对 b 的梯度（标量）
    return g_w, g_b

def attack_recover(g_w, g_b):
    """攻击者：只拿到梯度，反演私有样本"""
    r = g_b / 2.0
    x_rec = g_w / g_b if g_b != 0 else np.zeros_like(w)   # x = g_w / g_b
    y_rec = float(w @ x_rec + b - r)
    return x_rec, y_rec

def banner(t):
    print("\n" + "=" * 62)
    print(t)
    print("=" * 62)


if __name__ == "__main__":
    np.set_printoptions(precision=4, suppress=True)

    banner("Part 1 · 精确反演（单样本，无防御）")
    g_w, g_b = grad_of(x_true, y_true)
    x_rec, y_rec = attack_recover(g_w, g_b)
    print(f"真实样本 x_true = {x_true}")
    print(f"反演样本 x_rec  = {x_rec}")
    print(f"恢复误差 ||x_rec - x_true|| = {np.linalg.norm(x_rec - x_true):.2e}")
    print(f"真实标签 y={y_true:.4f}  反演标签 y={y_rec:.4f}")
    print("→ 结论：单样本时梯度泄露 = 数据泄露，攻击者零成本精确还原私有数据。")

    banner("Part 2 · 加噪防御（差分隐私）与效用权衡")
    # 防御：客户端上传前给梯度加高斯噪声（DP），σ 越大越私密但模型越差
    g_w, g_b = grad_of(x_true, y_true)
    print(f"{'噪声 σ':>8}  {'恢复误差(均值)':>14}  {'结论':>24}")
    print("-" * 62)
    for sigma in [0.0, 0.01, 0.1, 0.5, 1.0]:
        errs = []
        for _ in range(200):   # 多次采样取平均，避免单次噪声波动
            g_w_n = g_w + np.random.normal(0, sigma, size=w.shape)
            g_b_n = g_b + np.random.normal(0, sigma)
            x_rec, _ = attack_recover(g_w_n, g_b_n)
            errs.append(np.linalg.norm(x_rec - x_true))
        err = float(np.mean(errs))
        verdict = "完全泄露" if err < 1e-3 else ("可辨识" if err < 0.5 else "基本隐藏")
        print(f"{sigma:>8.2f}  {err:>14.4f}  {verdict:>20}")
    print("→ 结论：加噪能保护隐私，但噪声过大梯度失效、模型学不动 —— 隐私/效用不可兼得，")
    print("  正是研究计划里『加噪多了效用掉』的量化体现。")

    banner("Part 3 · 真实攻击与防御（多样本）")
    print("单样本可解析反演；多样本时 g_w = (2/n)Σ r_i·x_i 欠定，无法唯一还原，")
    print("需迭代优化『梯度匹配』(DLG)，再升级到生成式 GGL / 端到端 E2EGI。")
    print("对应防御：表示层可证明 Soteria / 细粒度 DPFL / 抗泄露 Fed-CDP。")
    print("\n参考 GitHub：zhuohangli/GGL · zhaohuali/E2EGI · jeremy313/Soteria · zlh-thu/DPFL")

    print("\n" + "=" * 62)
    print("实验 3 结束。")
