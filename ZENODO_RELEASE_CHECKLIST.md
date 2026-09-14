# ZENODO RELEASE CHECKLIST

Target release: **v1.2.4** — GitHub Release + Zenodo archive of
`osteoporosis_transportability_zenodo_v1.2.4`.
This checklist is a preparation document. **Do not invent a DOI.** Mint the
real one through Zenodo and back-fill it everywhere listed in §6.

## 1. Pre-release gate (all must be YES)

- [ ] No superseded files in the package (verified: `EXCLUDED_FILES_LOG.md` §B)
- [ ] No patient-level or otherwise restricted data (verified: §A; dry-run
      inputs were deleted after verification)
- [ ] `README.md` complete (17 required sections present)
- [x] `LICENSE` present — dual license (code MIT / non-code CC BY 4.0), implemented in v1.1.1
- [ ] `CITATION.cff` present and valid YAML
- [ ] `environment/` complete; 待核 flags read and accepted
- [ ] All model specifications present (M1/M3/M4; M2 documented as
      reproducible-by-pipeline — see `REPRODUCIBILITY_AUDIT.md` §5)
- [ ] Aggregate result archives complete (`RELEASE_MANIFEST.md`)
- [ ] Git working tree clean; tag `v1.2.4` on the release commit
- [ ] Author decision recorded on the remaining HOLD items in
      `EXCLUDED_FILES_LOG.md` §D (checklists; manuscript files) — SAP
      resolved in v1.1.1 (archived verbatim in docs/historical/); LICENSE
      resolved in v1.1.1 (dual MIT / CC BY 4.0)

## 2. GitHub steps

1. Create the public repository (suggested name:
   `osteoporosis-transportability-nhanes-china-knhanes`).
2. Commit the package contents at the repository root.
3. Push; verify the tree renders (README, CITATION.cff recognised).
4. Create Release **v1.2.4**, title "Reproducibility archive v1.2.4";
   attach nothing extra (the tree is the release).

## 3. Zenodo metadata (suggested)

* **Title:** Transportability of routine laboratory–based osteoporosis
  prediction from the USA to China and South Korea: a three-cohort study of
  external validation and recalibration — reproducibility archive (v1.2.4)
* **Authors:** Ziyi Wu (Second Hospital of Harbin Medical University);
  Haichuan Zhang (Chengdu University of Technology); Linkang Du (Second
  Hospital of Harbin Medical University); Jiaze Yu (Second Hospital of
  Harbin Medical University); Faxin Wang (Second Hospital of Harbin Medical
  University); Feng Gao (Second Hospital of Harbin Medical University;
  corresponding)
* **Description:** Reproducibility archive for the three-cohort external
  validation and recalibration study of frozen routine-laboratory
  osteoporosis prediction models (NHANES 2005–2018 → Harbin hospital cohort
  2024; KNHANES 2009–2011). Contains analysis code, frozen model
  specifications (M1–M4; M2 serialized from a verified deterministic re-execution), aggregate results, final figures, environment
  pins, and full provenance documentation. Patient-level Chinese data and
  per-case KNHANES extracts are not included (see README data-access
  boundaries).
* **Keywords:** osteoporosis; prediction model; external validation;
  transportability; calibration; NHANES; KNHANES; logistic regression
* **License:** add BOTH `MIT` AND `CC-BY-4.0` to the Zenodo record (Zenodo supports multiple licenses per deposit), and state the boundary in the Description: "Code: MIT; figures, documentation, model specifications, and aggregate results: CC BY 4.0." The GitHub repository carries the dual LICENSE file; CITATION.cff deliberately declares no single license (CFF 1.2 multi-license arrays mean OR, not file-scoped dual licensing).
* **Version:** 1.2.4
* **Access rights:** Open Access
* **Related identifiers:** leave empty until the manuscript has a DOI;
  then add the manuscript DOI as "is supplement to" / "is referenced by".
* **Publication date:** the actual release date.

## 4. Zenodo steps

1. Link GitHub to Zenodo (zenodo.org → GitHub integration) and enable the
   repository, **or** upload `osteoporosis_transportability_zenodo_v1.2.4.zip`
   manually as a new deposit.
2. Fill metadata per §3.
3. **Reserve DOI** (Zenodo "Reserve DOI" button) → copy the reserved DOI.
4. Back-fill the DOI per §6 **before** publishing the deposit.
5. Publish the deposit (GitHub release flow: publish the GitHub release and
   Zenodo mints automatically; manual flow: click Publish).

## 5. GitHub release finalisation

After the DOI exists, add it to the GitHub release notes and confirm the
Zenodo record shows version 1.2.4 and the correct author order (must match
the manuscript exactly).

## 6. DOI back-fill locations (after minting — mandatory)

| Location | Field |
|---|---|
| Manuscript main text — "Protocol and code archive" statement | replace the data-availability placeholder with the DOI |
| Manuscript Supplement — eAppendix data/code availability statement | same DOI |
| `README.md` §2 and §16 | add DOI badge/line |
| `CITATION.cff` | add `doi:` field |
| GitHub repository description | add DOI |
| Journal submission system data-availability field | DOI + repository URL |

## 7. KNHANES governance reminder

Do not upload any per-case KNHANES extract or prediction CSV to GitHub or
Zenodo unless KDCA redistribution permission has been confirmed in writing.
"Publicly available from KDCA" does not itself grant redistribution rights.
