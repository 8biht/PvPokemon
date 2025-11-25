"""Benchmark read/write latency for single DB vs read/write split.

This script performs N write operations (add_entry) followed by N read
operations (get_box) and reports timings. It constructs a repository using
environment variables for WRITE_DATABASE_URL and READ_DATABASE_URL so you can
compare behaviour with and without a replica.

Usage:
  # Single DB mode (default - uses sqlite file):
  python backend/bench/db_rw_benchmark.py

  # Read/write split mode (point to MySQL primary and replica):
  $env:WRITE_DATABASE_URL='mysql+pymysql://user:pass@primary:3306/db'
  $env:READ_DATABASE_URL='mysql+pymysql://user:pass@replica:3306/db'
  python backend/bench/db_rw_benchmark.py

Note: Ensure the schema is created on the write DB before benchmarking.
"""
import os
import time
import uuid
from statistics import mean

from backend.repo_factory import get_repository
from backend.dto import BoxEntry


N = int(os.environ.get('BENCH_ITER', '50'))
USER = os.environ.get('BENCH_USER', 'bench_user')


def time_ops(repo):
    write_times = []
    read_times = []

    # Clean initial box
    try:
        # remove all existing entries by repeatedly deleting index 0
        box = repo.get_box(USER)
        for i in range(len(box)-1, -1, -1):
            repo.remove_entry(USER, i)
    except Exception:
        pass

    # Writes
    for i in range(N):
        entry = BoxEntry(name=f'bench-{i}-{uuid.uuid4().hex[:6]}', sprite='bench.png', cp=100+i)
        t0 = time.time()
        repo.add_entry(USER, entry)
        t1 = time.time()
        write_times.append(t1 - t0)

    # Reads
    for i in range(N):
        t0 = time.time()
        box = repo.get_box(USER)
        t1 = time.time()
        read_times.append(t1 - t0)

    return write_times, read_times


def main():
    print('Creating repository (read/write URLs from env)')
    repo = get_repository(os.path.join(os.path.dirname(__file__), '..', '..'))
    print(f'Running benchmark: N={N} user={USER}')
    w, r = time_ops(repo)
    print('Write ops: count', len(w), 'avg', mean(w), 'min', min(w), 'max', max(w))
    print('Read ops: count', len(r), 'avg', mean(r), 'min', min(r), 'max', max(r))


if __name__ == '__main__':
    main()
