# Resource safety plan

No real inference approved or attempted. Configuration budgets alone enforce
nothing at OS level. Before every heavy run, inspect available memory, load,
PSI, disk, GPU/runtime support and model/cache sizes. Fail closed without a
working child cgroup; never run directly as a fallback.

Verified harmless probe command (not a model launch):

```bash
systemd-run --user --wait --pipe \
  -p MemoryHigh=3G -p MemoryMax=5G -p MemorySwapMax=0 \
  -p CPUQuota=150% -p TasksMax=192 -p RuntimeMaxSec=10 /usr/bin/true
```

A second child read its actual controller files and confirmed all five values.
No allocation/OOM stress was performed. Revalidate paths and interpreter from
inside the service before using an inference environment.

Future smoke: explicit approval for model/dependency download inventory;
authorized local reference at most 10 MiB/30 sec; one short sentence; one model,
one worker; zero retries; at most 120 sec total initialization plus generation;
OMP/MKL thread caps; output duration cap 30 sec; no parallel benchmark or browser
load. Named transient unit with RuntimeMaxSec, control-group kill behavior and
bounded stop timeout must handle timeouts, cancellation and descendants.
Check all child processes gone after failures. Never alter global settings.
Record model revision, runtime, exit status, cgroup MemoryPeak, swap peak and
memory.events, not just parent process RSS. Record failures and partial outputs.
Downloading weights needs explicit approval even though storage is available.
If the model does not fit, report measured failure and stop. Never raise budgets.
FFmpeg installation is separately gated as a system dependency. No remote uploads
or paid service access without explicit destination/payload/cost approval.
