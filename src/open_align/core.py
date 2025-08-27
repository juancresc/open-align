from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import typer
from rich import print as rprint
import cv2 as cv
import numpy as np

@dataclass
class PairMatches:
    ref_path: Path
    img_path: Path
    n_ref_kp: int
    n_img_kp: int
    n_good: int
    good_matches: List[cv.DMatch]
    ref_pts: np.ndarray  # shape: (N, 1, 2), float32
    img_pts: np.ndarray  # shape: (N, 1, 2), float32

def _read_bgr(path: Path) -> np.ndarray | None:
    return cv.imread(str(path), cv.IMREAD_COLOR)

def _to_gray(bgr: np.ndarray) -> np.ndarray:
    return cv.cvtColor(bgr, cv.COLOR_BGR2GRAY)

def _detect_orb(gray: np.ndarray, nfeatures :int):
    orb = cv.ORB_create(nfeatures=nfeatures)
    kps, desc = orb.detectAndCompute(gray, None)
    return kps, desc

def _match_orb(d1: np.ndarray, d2: np.ndarray, ratio: float = 0.75) -> List[cv.DMatch]:
    # Hamming distance for ORB; KNN + Lowe's ratio test
    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=False)
    knn = bf.knnMatch(d1, d2, k=2)
    good = []
    for m, n in knn:
        if m.distance < ratio * n.distance:
            good.append(m)
    return good

def _estimate_similarity(img_pts: np.ndarray, ref_pts: np.ndarray):
    """
    Estimate a similarity transform (2x3) mapping img_pts -> ref_pts using RANSAC.
    Returns (M2x3, H3x3, ninliers).
    """
    M, inliers = cv.estimateAffinePartial2D(
        img_pts, ref_pts,
        method=cv.RANSAC,
        ransacReprojThreshold=3.0,
        maxIters=2000,
        confidence=0.995,
    )
    if M is None:
        raise RuntimeError("Failed to estimate similarity transform.")
    ninl = int(inliers.sum()) if inliers is not None else 0
    H = np.eye(3, dtype=np.float32)
    H[:2, :3] = M.astype(np.float32)  # promote to 3x3 for uniform handling later
    return M, H, ninl

# --- ADD (near your helpers): compute common-overlap rect from masks ---
def _common_overlap_rect(masks: list[np.ndarray], erode: int = 4) -> tuple[int, int, int, int]:
    """
    Returns (x, y, w, h) of an axis-aligned rectangle guaranteed to be valid in all masks.
    `erode` shrinks the overlap a bit to avoid boundary artifacts.
    """
    import cv2 as cv
    import numpy as np

    if not masks:
        raise ValueError("No masks provided.")

    common = masks[0].copy()
    for m in masks[1:]:
        common = cv.bitwise_and(common, m)

    # optional: make the overlap conservative
    if erode > 0:
        k = cv.getStructuringElement(cv.MORPH_RECT, (erode, erode))
        common = cv.erode(common, k, iterations=1)

    # find largest connected component to ignore tiny specks
    num, labels = cv.connectedComponents((common > 0).astype(np.uint8))
    if num <= 1:  # no foreground
        raise RuntimeError("No common overlap found across images.")
    # skip label 0 (background)
    best_label, best_count = 1, 0
    for lbl in range(1, num):
        cnt = int((labels == lbl).sum())
        if cnt > best_count:
            best_label, best_count = lbl, cnt
    mask_largest = (labels == best_label).astype(np.uint8) * 255

    # bounding rectangle of that component
    ys, xs = np.where(mask_largest > 0)
    if xs.size == 0:
        raise RuntimeError("Common overlap empty after processing.")
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    w, h = x1 - x0, y1 - y0
    return x0, y0, w, h


def align(files: List[Path], nfeatures: int = 4000, ):
    """
    Load images, detect ORB features, and report good matches to the reference image.
    (Alignment transform estimation comes next.)
    """
    # ---- 1) Validate paths
    paths: List[Path] = []
    for f in files:
        p = Path(f).expanduser().resolve()
        if not p.is_file():
            rprint(f"[bold red]ERROR:[/] File not found: {p}")
            raise typer.Exit(code=1)
        paths.append(p)

    if len(paths) < 2:
        rprint("[yellow]Provide at least two images (first will be the reference).[/]")
        raise typer.Exit(code=1)

    # ---- 2) Load images
    imgs = []
    for p in paths:
        img = _read_bgr(p)
        if img is None:
            rprint(f"[bold red]ERROR:[/] Could not read image: {p}")
            raise typer.Exit(code=1)
        imgs.append(img)

    # ---- 3) Detect ORB on reference
    ref_bgr = imgs[0]
    ref_gray = _to_gray(ref_bgr)
    ref_kp, ref_desc = _detect_orb(ref_gray, nfeatures)
    if ref_desc is None or len(ref_kp) < 8:
        rprint("[bold red]ERROR:[/] Not enough features in reference image.")
        raise typer.Exit(code=1)

    rprint(f"[bold]Reference:[/] {paths[0]}")
    rprint(f"  keypoints: {len(ref_kp)}")

    # --- ADD: containers for transforms, aligned images, and masks ---
    sim_transforms_2x3: list[np.ndarray] = [np.float32([[1,0,0],[0,1,0]])]  # identity for ref
    aligned_bgr: list[np.ndarray] = [ref_bgr.copy()]
    aligned_masks: list[np.ndarray] = []

    # build a validity mask for the reference (all ones)
    h_ref, w_ref = ref_bgr.shape[:2]
    ref_mask = np.full((h_ref, w_ref), 255, np.uint8)
    aligned_masks.append(ref_mask)


    # ---- 4) For each other image: detect + match to reference
    results: List[PairMatches] = []
    for idx in range(1, len(imgs)):
        bgr = imgs[idx]
        gray = _to_gray(bgr)
        kp, desc = _detect_orb(gray, nfeatures)

        if desc is None or len(kp) < 8:
            rprint(f"[red]Skipping[/] {paths[idx]}: not enough features (kp={len(kp) if kp else 0}).")
            continue

        good = _match_orb(ref_desc, desc, ratio=0.75)

        # Gather matched point coordinates (ref -> img)
        ref_pts = np.float32([ref_kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        img_pts = np.float32([kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

        # --- ADD: estimate similarity transform (img -> ref) ---
        try:
            # TODO other algorithms
            M_sim, H_sim, ninl = _estimate_similarity(img_pts, ref_pts)
        except RuntimeError as e:
            rprint(f"  [red]Similarity estimation failed:[/] {e}")
            continue

        rprint(f"  similarity inliers: {ninl}/{len(good)}")

        # (Optional) preview-warp this image into the reference frame
        h_ref, w_ref = ref_bgr.shape[:2]
        aligned_preview = cv.warpAffine(bgr, M_sim, (w_ref, h_ref), flags=cv.INTER_LINEAR)
        # You can keep H_sim around for a later uniform pipeline (e.g., warpPerspective)

        # --- ADD: warp this image into the reference frame ---
        aligned = cv.warpAffine(
            bgr, M_sim, (w_ref, h_ref),
            flags=cv.INTER_LINEAR,
            borderMode=cv.BORDER_CONSTANT,
            borderValue=(0, 0, 0),
        )

        # validity mask (which pixels came from real data vs borders)
        src_mask = np.full((bgr.shape[0], bgr.shape[1]), 255, np.uint8)
        warped_mask = cv.warpAffine(
            src_mask, M_sim, (w_ref, h_ref),
            flags=cv.INTER_NEAREST,
            borderMode=cv.BORDER_CONSTANT,
            borderValue=0,
        )

        aligned_bgr.append(aligned)
        aligned_masks.append(warped_mask)
        sim_transforms_2x3.append(M_sim)


        results.append(PairMatches(
            ref_path=paths[0],
            img_path=paths[idx],
            n_ref_kp=len(ref_kp),
            n_img_kp=len(kp),
            n_good=len(good),
            good_matches=good,
            ref_pts=ref_pts,
            img_pts=img_pts
        ))

        all_ref_indices = set()
        for res in results:
            for m in res.good_matches:
                all_ref_indices.add(m.queryIdx)

    if all_ref_indices:
        ref_vis_all = ref_bgr.copy()
        ref_kps_all = [ref_kp[i] for i in sorted(all_ref_indices)]
        cv.drawKeypoints(
            ref_vis_all,
            ref_kps_all,
            ref_vis_all,
            color=(255, 0, 0),  # red for "all"
            flags=cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
        )
        out_all = Path.cwd() / "ref_matches_all.png"
        if cv.imwrite(str(out_all), ref_vis_all):
            rprint(f"[green]Saved[/] cumulative matched ref keypoints → {out_all}")
        else:
            rprint("[red]Failed to save cumulative matched image")

        rprint(f"[green]OK[/] {paths[idx]}")
        rprint(f"  keypoints: {len(kp)}")
        rprint(f"  good matches to reference (ratio=0.75): {len(good)}")

        # --- ADD: save aligned outputs for a quick check ---
        out_dir = Path.cwd()
        for i, img in enumerate(aligned_bgr):
            out_path = out_dir / f"aligned_{i:03d}.png"
            if cv.imwrite(str(out_path), img):
                rprint(f"[green]Saved[/] {out_path}")
            else:
                rprint(f"[red]Failed to save {out_path}")
    
    # --- ADD: compute automatic common-overlap rect and crop all aligned images ---
    try:
        x, y, w, h = _common_overlap_rect(aligned_masks, erode=50)  # tweak erode as needed
        rprint(f"[cyan]Common overlap:[/] x={x}, y={y}, w={w}, h={h}")
    except Exception as e:
        rprint(f"[bold red]ERROR computing overlap:[/] {e}")
        raise typer.Exit(code=3)

    cropped = [img[y:y+h, x:x+w].copy() for img in aligned_bgr]

    # optional: save cropped results
    out_dir = Path.cwd()
    for i, img in enumerate(cropped):
        out_path = out_dir / f"aligned_cropped_{i:03d}.jpg"
        if cv.imwrite(str(out_path), img, [cv.IMWRITE_JPEG_QUALITY, 100]):
            rprint(f"[green]Saved[/] {out_path}")
        else:
            rprint(f"[red]Failed to save {out_path}")


    if not results:
        rprint("[bold red]ERROR:[/] No valid matches found against the reference.")
        raise typer.Exit(code=2)

    # (Optional) Return or store 'results' for the next step (transform estimation).
    # For now we just report counts; next step: estimate similarity/affine/homography with RANSAC.
