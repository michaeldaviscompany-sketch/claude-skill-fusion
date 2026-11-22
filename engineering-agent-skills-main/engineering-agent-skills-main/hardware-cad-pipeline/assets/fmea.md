# FMEA (lightweight) — <part / system name>

<!-- For each way it can fail: how likely, how bad, what detects it, what mitigates it.
     Severity/likelihood 1-5 is plenty at prototype stage. Anything scoring high on
     severity with human contact gets a design change, not a warning label. -->

| # | Failure mode | Cause | Effect | Sev (1-5) | Lik (1-5) | Detection | Mitigation (design change first, procedure last) |
|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |

## Fail-safe review
- What happens on loss of power?
- What happens if the moving part jams?
- What happens if a sensor reads wrong (and how would you know)?
- Is the default/unpowered state the safe state? If not, why is that acceptable?
