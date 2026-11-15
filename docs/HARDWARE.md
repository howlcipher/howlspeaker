# Hardware compatibility report

Observed 2026-11-15 UTC with read-only shell inspection, except two tiny bounded
systemd services. Ubuntu 26.04 userspace; host kernel 7.3.3-ogc1.1.fc45.x86_64.
Host distribution was not independently verified. CPU Ryzen 5 1600, 6 cores,
12 threads, AVX2. RAM 23 GiB reported, 17 GiB available; swap 11 GiB with 4 KiB
used. Load 2.09/0.80/0.29; memory PSI averages zero. Workspace had 192 GiB
available. These are point-in-time observations, not reservations.

GPU sysfs vendor 0x1002, device 0x67df, VRAM 8589934592 bytes.
User describes RX 580; device family ID alone does not uniquely prove board model.
/dev/kfd and renderD128 exist. rocminfo and rocm-smi were not on PATH.
GPU device visibility does not establish usable PyTorch/ROCm inference.
AMD's current compatibility matrix does not list RX 580:
https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html
Verified 2026-11-15. No driver installation or GPU execution attempted.

Python 3.14.4, pytest 9.0.3, flake8 7.3.0 available; FFmpeg absent on PATH.
Upstream Qwen recommends a separate Python 3.12 environment; inference dependency
compatibility on the current interpreter remains unverified.

Initial systemctl status returned offline and the visible container cgroup was
unlimited and not writable. Live systemd-run user services nevertheless succeeded.
The child service read its own cgroup and confirmed memory.high=3221225472,
memory.max=5368709120, memory.swap.max=0, cpu.max=150000 100000,
pids.max=192. RuntimeMaxSec=10 was applied. Do not assume the parent container's
cgroup view describes the launched host service. Child runtime paths and engine
visibility must be checked before inference. See RESOURCE_SAFETY.md.
CPU inference may be technically possible but practical latency and total memory
fit are unknown. No model can yet be certified to fit the 5 GiB budget.
