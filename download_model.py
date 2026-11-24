#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多线程分片下载 GGUF 模型（零依赖，只用标准库）"""
import urllib.request
import threading
import os
import sys
import time

URL = "https://modelscope.cn/models/Qwen/Qwen1.5-7B-Chat-GGUF/resolve/master/qwen1_5-7b-chat-q4_k_m.gguf"
OUT_DIR = "/Users/lisaiyang/ai-security-lab/models"
OUT = os.path.join(OUT_DIR, "qwen1_5-7b-chat-q4_k_m.gguf")
THREADS = 8

os.makedirs(OUT_DIR, exist_ok=True)


def get_size(url):
    req = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        cr = r.headers.get("Content-Range", "")
        return int(cr.split("/")[-1])


def download_part(url, start, end, part, results):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"Range": f"bytes={start}-{end}"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            tmp = f"{OUT}.part{part}"
            with open(tmp, "wb") as f:
                f.write(data)
            results[part] = end - start + 1
            return
        except Exception as e:
            if attempt == 2:
                results[part] = -1
                print(f"[片段 {part}] 下载失败: {e}", flush=True)
            time.sleep(2)


def progress_monitor(total, stop):
    while not stop.is_set():
        done = 0
        for i in range(THREADS):
            p = f"{OUT}.part{i}"
            if os.path.exists(p):
                done += os.path.getsize(p)
        pct = done / total * 100
        print(f"\r已下载 {done/1e9:.2f}/{total/1e9:.2f} GB ({pct:.1f}%)", end="", flush=True)
        time.sleep(5)
    print()


def main():
    total = get_size(URL)
    print(f"文件总大小: {total/1e9:.2f} GB，{THREADS} 线程下载", flush=True)

    results = {}
    stop = threading.Event()
    monitor = threading.Thread(target=progress_monitor, args=(total, stop), daemon=True)
    monitor.start()

    threads = []
    chunk = total // THREADS
    for i in range(THREADS):
        start = i * chunk
        end = (total - 1) if i == THREADS - 1 else (i + 1) * chunk - 1
        t = threading.Thread(target=download_part, args=(URL, start, end, i, results))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    stop.set()
    monitor.join(timeout=1)

    if any(v == -1 for v in results.values()):
        print("有片段下载失败，请重新运行")
        sys.exit(1)

    print("合并文件中...", flush=True)
    with open(OUT, "wb") as out:
        for i in range(THREADS):
            with open(f"{OUT}.part{i}", "rb") as f:
                out.write(f.read())
            os.remove(f"{OUT}.part{i}")

    size = os.path.getsize(OUT)
    print(f"完成! {OUT} ({size/1e9:.2f} GB)", flush=True)


if __name__ == "__main__":
    main()
