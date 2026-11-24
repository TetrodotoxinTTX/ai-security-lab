#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""分段下载 GGUF 模型（串行、每段独立、支持续传，零依赖）

关键改进（解决之前 curl 覆盖文件的问题）：
- 文件分成多段，每段存成独立的 .partN 文件
- 每段下载失败只重试该段，不影响其他段
- 脚本重跑时会跳过已完成的段（断点续传）
- 每段是新连接，避免 CDN 对长连接的限速
"""
import urllib.request
import os
import time
import sys

URL = "https://modelscope.cn/models/Qwen/Qwen1.5-7B-Chat-GGUF/resolve/master/qwen1_5-7b-chat-q4_k_m.gguf"
OUT_DIR = "/Users/lisaiyang/ai-security-lab/models"
OUT = os.path.join(OUT_DIR, "qwen1_5-7b-chat-q4_k_m.gguf")
SEGMENTS = 20          # 分成 20 段，每段约 240MB
MAX_RETRY = 5

os.makedirs(OUT_DIR, exist_ok=True)


def get_size():
    req = urllib.request.Request(URL, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        cr = r.headers.get("Content-Range", "")
        return int(cr.split("/")[-1])


def seg_path(i):
    return f"{OUT}.part{i:02d}"


def download_segment(i, start, end):
    """下载第 i 段，返回 True 表示该段完整"""
    expect = end - start + 1
    pf = seg_path(i)
    # 已完成的段直接跳过
    if os.path.exists(pf) and os.path.getsize(pf) == expect:
        return True
    # 不完整的段删掉重下
    if os.path.exists(pf):
        os.remove(pf)

    for attempt in range(MAX_RETRY):
        try:
            t0 = time.time()
            req = urllib.request.Request(URL, headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(req, timeout=300) as r:
                data = r.read()
            with open(pf, "wb") as f:
                f.write(data)
            got = os.path.getsize(pf)
            speed = got / (time.time() - t0) / 1e6
            if got == expect:
                print(f"  段 {i+1}/{SEGMENTS} 完成 ({got/1e6:.0f}MB, {speed:.1f}MB/s)", flush=True)
                return True
            else:
                print(f"  段 {i+1}/{SEGMENTS} 大小不符(期望{expect} 实得{got})，重试", flush=True)
                os.remove(pf)
        except Exception as e:
            print(f"  段 {i+1}/{SEGMENTS} 第{attempt+1}次失败: {e}", flush=True)
            time.sleep(3)
    return False


def main():
    total = get_size()
    print(f"文件总大小 {total/1e9:.2f} GB，分 {SEGMENTS} 段下载", flush=True)
    chunk = total // SEGMENTS
    failed = []
    for i in range(SEGMENTS):
        start = i * chunk
        end = (total - 1) if i == SEGMENTS - 1 else (i + 1) * chunk - 1
        if not download_segment(i, start, end):
            failed.append(i)
    if failed:
        print(f"以下段下载失败: {failed}，请重新运行本脚本续传", flush=True)
        sys.exit(1)
    # 合并
    print("所有段完成，合并中...", flush=True)
    with open(OUT, "wb") as out:
        for i in range(SEGMENTS):
            with open(seg_path(i), "rb") as f:
                out.write(f.read())
            os.remove(seg_path(i))
    print(f"完成! {OUT} ({os.path.getsize(OUT)/1e9:.2f} GB)", flush=True)


if __name__ == "__main__":
    main()
