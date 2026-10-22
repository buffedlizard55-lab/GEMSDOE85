# H85 hypothesis slate and preregistration

**Preregistered lane:** `H85-scale-space-detrended-slope-persistence`
**Preregistration date:** 2026-10-22 UTC
**Experiment cap:** 3
**Decision rule:** run the fixed three arms on the same buffered whole-segment holdout; only the top arm can create the local download artifact. A live submission slot is a separate decision and is not taken by this repository.

The rankings below are hypotheses, not scores. A score is written only with the
label `HOLDOUT-DTI` and its evaluator, number of withheld positives, and CI.
Any public leaderboard number copied from the user brief is marked
`ORGANIZER-CONFIRMED` only when a submission-page receipt is present; none is
present in this checkout.

## Ranked candidates before implementation

| Rank | ID | Layers and signature | Why it can find a catalogue-missing fault | Difference from this repo and prior registry lanes | New data / cost |
|---:|---|---|---|---|---|
| **1** | **H85-1: scale-space detrended-slope persistence** | Official feature band 19 `det_elev_slope`; Gaussian gradient magnitude at σ = 0.5, 1, 2, 3 pixels; cellwise maximum persistence envelope; local peak packing at 2.8 pixels | A fault scarp can remain an edge after regional relief is removed. A fault absent from the catalogue is not removed from the label mask, so the transform can score it without copying a known trace. | The implementation uses one official band, no catalogue-derived surface, no learned classifier, no Radon bank, no external geothermal point layer, and no submodular optimizer. The scale envelope is the lane's single method paragraph. | No new data; CPU minutes to tens of minutes depending on the 419 MB stack. |
| **2** | **H85-2: cross-property edge-normal agreement** | Bands 5, 11, 18 (`gravity slope/VG/HG`) plus band 19; compare local gradient-normal directors and retain co-located, orientation-consistent edges | A buried basement step should perturb gravity and topographic slope in a related direction even where the mapped surface trace is absent. | Not implemented in H85; differs from H85-1 by multi-band orientation coherence rather than a one-band scale envelope. | Existing stack; moderate implementation cost. |
| **3** | **H85-3: bilateral scarp-break residual** | Bands 12 and 19; contrast the two sides of a candidate edge against a local plateau/valley baseline, then suppress one-sided terrace rims | A true throw can produce a paired change in detrended elevation and slope, whereas an isolated road cut or erosional bench often has asymmetric support. | Not implemented in H85; unlike earlier binary ridge fields it would use a signed, two-sided residual and no catalogue tip prior. | Existing stack; moderate cost; must test sign stability. |
| **4** | **H85-4: blind relay negative-space graph** | `existing_faults.tif` only for visible nodes; component endpoints, gap distance, tangent agreement and graph-geodesic bridge residual | A missing segment between two mapped fragments may be a relay/step-over; a graph gap is a structural prediction rather than a copy of the catalogue. | Not implemented in H85; unlike H85-1 it is catalogue-derived and must be cross-fitted fold by fold. It is deliberately not mixed into the promoted lane. | Existing catalogue; high leakage risk and higher cost. |
| **5** | **H85-5: post-seismic/InSAR deformation edge** | Multi-temporal Sentinel-1 interferometric displacement gradient and coherence from NASA ASF/NASA OPERA, optionally USGS ComCat event timing | A young rupture or creeping blind fault may not appear in a static catalogue but can leave a deformation discontinuity. | Not implemented because the current egress policy permits only GitHub, codeload, GitHub API, PyPI and npm; a free official ASF/OPERA download was not obtainable in this environment. | Specific free official sources: [NASA ASF Search](https://search.asf.alaska.edu/) and [USGS ComCat FDSN](https://earthquake.usgs.gov/fdsnws/event/1/). **Not viable in this run; availability must be rechecked on an unrestricted runner.** |

## Top-candidate falsifier and implementation

H85-1 is falsified if either (a) the four-scale envelope fails to beat the
single-scale control on the fixed holdout, or (b) any individual scale has an
AUC above the 0.90 leakage canary threshold. The final surface is exactly the
maximum of the four normalized edge fields; no post-hoc band or weight search
is allowed after the three arms.

The named non-fault mimic is a Pleistocene paleoshoreline bench or fluvial/road
cut riser. H85 does not claim to identify geothermal vents directly: it tests a
structural proxy, and the absence of a radiometric/heat-flow layer in H85 is an
explicit limitation.
