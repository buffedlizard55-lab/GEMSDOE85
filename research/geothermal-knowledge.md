# Geothermal-vent knowledge base (auditable, H85)

**Scope.** This is a starting knowledge store, not evidence that any emitted
pixel is a geothermal vent. H85 tests a structural proxy against a catalogue
holdout. Quantitative scores are labelled `HOLDOUT-DTI`; organizer results are
labelled `ORGANIZER-CONFIRMED` only when a portal receipt exists.

## Source ledger

| Source | Use | Verification status in this checkout |
|---|---|---|
| [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | official task, metric, grid and submission rules | Link supplied in brief; the current Arena egress policy did not allow a direct page fetch. Do not treat un-fetched wording as independently verified. |
| [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | official placement route | Link supplied in brief; requires account/enrollment. |
| [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution) | baseline pipeline context | **FETCHED FROM GITHUB**; repository cloned and README inspected. |
| [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | magnetic/radiometric/geothermal context | Link supplied in brief; not directly fetched in this egress-restricted run. |
| [INGENIOUS / GBCGE](https://gbcge.org/current-projects/ingenious/) | Great Basin geothermal research context | Link supplied in brief; not directly fetched in this egress-restricted run. |
| [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391) | well/spring chemistry and possible external hypotheses | Link supplied in brief; not used by H85 and not fetched here. |
| [EPSG:32611](https://epsg.io/32611) | CRS link for manual review | Link supplied in brief; local GeoTIFF metadata receipt reports EPSG:32611. |
| [DOE rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | rules and disclosure review | Link supplied in brief; not directly fetched here. |

## What the measured inputs can support

The local feature-stack inventory reports named bands for magnetic anomaly,
reduced-to-pole magnetic field, magnetic horizontal/vertical gradients, strain
invariants, isostatic gravity fields, detrended elevation, basement depth,
earthquake-distance/intensity proxies, conductivity, and detrended elevation
slope. The inventory is recorded in `evidence/data_receipt.json` when the
ignored feature stack is restored. Its provenance is a hash-pinned owner mirror,
not an organizer-authenticated replacement.

A fault can be geothermal-relevant because a fracture network may provide a
permeability pathway for hot fluid. The relevant observable is therefore not a
vent label alone: an edge in elevation/slope, a density or magnetic contact, a
strain discontinuity, or a conductive/thermal anomaly can be a structural
indicator. Each indicator has non-fault mimics. H85 uses only the detrended
slope band because it is a deliberately falsifiable, single-lane test; it does
not claim that slope is sufficient to establish fluid upflow.

## H85 mechanism

1. Regional topography is already removed in the supplied `det_elev_slope`
   layer according to its band description; H85 does not recompute or alter the
   label raster.
2. A Gaussian gradient magnitude measures edge strength without assigning a
   geologic sign. Four scale fields represent 50, 100, 200 and 300 m smoothing
   scales at the competition grid; these are method parameters, not leaderboard
   scores.
3. The maximum across scales is a persistence envelope. The final emitter keeps
   local maxima separated by 2.8 grid cells and zeroes known catalogue pixels.
4. The holdout withholds whole catalogue components and a three-cell buffer,
   then evaluates only the withheld components. This is a catalogue-recovery
   proxy and cannot prove performance on truly novel organizer labels.

## Mimics and falsifiers

* Paleolake shoreline benches can be long, sharp, and non-tectonic.
* Fluvial terraces, canyon walls, landslides, roads, and mine benches can create
  slope edges.
* Lithologic contacts can appear as topographic breaks without a fault.
* A high edge response can be a processing seam or an interpolation artifact.

The canary threshold is effective single-feature AUC greater than 0.90. A
feature crossing that threshold is quarantined as leakage until proven
otherwise. H85's independent registry gate also checks rank correlation and
three-pixel dot overlap; a failure stops the run rather than being rationalized.

## Research gaps and next sources

The most important missing evidence is a label-free distinction between a
tectonic edge and a shoreline/road/terrace edge. Candidate follow-ups are:

* official USGS 3DEP DEM derivatives for scarps and curvature;
* USGS GeoDAWN radiometric ratios for hydrothermal alteration;
* DOE GDR 1391 wells/springs and temperature probes;
* USGS Heat Flow data for conductive anomalies;
* NASA ASF/OPERA Sentinel-1 deformation and USGS ComCat for young activity.

Only sources that are free, official, obtainable, hash-recorded, and screened
for label-derived columns should enter a future lane. H85 intentionally does
not download or use any of them.
