import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys
import os

os.environ["PYTHONIOENCODING"] = "utf-8"

import time
time.sleep = lambda x: None

sys.path.append(os.getcwd())

try:
    from scipy.stats import gaussian_kde
except ImportError:
    print("ERROR: scipy not installed. Run: pip install scipy")
    sys.exit(1)

try:
    from anomaly_integration_iot import AnomalyHoneypot
except ImportError:
    print("Error: Could not import AnomalyHoneypot.")
    sys.exit(1)


# ─────────────────────────────────────────────
# 1. GENERATE GENUINELY VARIED FEATURE VECTORS
#    instead of 8 paths × 20 noisy copies
# ─────────────────────────────────────────────

def build_varied_features(detector, n_samples=300, traffic_type="benign"):
    """
    Build varied feature vectors directly in feature space.
    Rather than repeating the same paths, we sample a base vector and
    add structured variance that reflects real traffic diversity.
    """

    if traffic_type == "benign":
        base_paths = [
            "/", "/index.html", "/api/v1/status", "/static/css/main.css",
            "/images/logo.png", "/about", "/help", "/favicon.ico",
            "/api/v2/devices", "/dashboard", "/login", "/logout",
            "/api/v1/health", "/docs", "/metrics"
        ]
    else:
        base_paths = [
            "/etc/passwd", "/cgi-bin/config.sh", "/admin/login",
            "/shell?cmd=id", "/.env", "/onvif/device", "/snapshot.cgi",
            "/device.rsp", "/../../../etc/shadow", "/wp-admin",
            "/phpMyAdmin", "/admin.php", "/config.xml",
            "/api/../../etc/passwd", "/cmd.php?exec=whoami"
        ]

    scores = []
    for _ in range(n_samples):
        path = np.random.choice(base_paths)
        features = detector.map_http_to_network_features({"path": path})

        # ── FIX 1: Add noise AFTER scaling, not before ──────────────────
        # Scale first so the scaler's statistics are respected
        if detector.scaler:
            features_scaled = detector.scaler.transform(features)
        else:
            features_scaled = features

        # Structured noise: benign traffic has smaller variance than attacks
        noise_std = 0.08 if traffic_type == "benign" else 0.12
        noise = np.random.normal(0, noise_std, features_scaled.shape)
        features_noisy = features_scaled + noise

        score = detector.model.decision_function(features_noisy)[0]
        scores.append(score)

    return np.array(scores)


def generate_kde_plot():
    print("Loading model...")
    detector = AnomalyHoneypot()

    if not detector.model:
        print("Error: Isolation Forest model not found.")
        return

    # ── FIX 2: Extract the REAL threshold from sklearn ──────────────────
    # model.offset_ is the actual decision boundary, not 0.0
    threshold = detector.model.offset_
    print(f"Real model threshold (offset_): {threshold:.4f}")

    print("Generating benign traffic scores (n=300)...")
    benign_scores = build_varied_features(detector, n_samples=300, traffic_type="benign")

    print("Generating attack traffic scores (n=300)...")
    attack_scores = build_varied_features(detector, n_samples=300, traffic_type="attack")

    print(f"\nBenign  — mean: {benign_scores.mean():.4f}, std: {benign_scores.std():.4f}, "
          f"range: [{benign_scores.min():.3f}, {benign_scores.max():.3f}]")
    print(f"Attack  — mean: {attack_scores.mean():.4f}, std: {attack_scores.std():.4f}, "
          f"range: [{attack_scores.min():.3f}, {attack_scores.max():.3f}]")

    separation = abs(benign_scores.mean() - attack_scores.mean())
    print(f"Peak separation: {separation:.4f}")

    if separation < 0.05:
        print("\n⚠ WARNING: Peak separation < 0.05 — your features are not discriminative enough.")
        print("  Consider adding: request rate, payload entropy, port scan count, UA string features.")

    # ── FIX 3: Use REAL scipy gaussian_kde, not histogram dot-connect ───
    x_min = min(benign_scores.min(), attack_scores.min()) - 0.05
    x_max = max(benign_scores.max(), attack_scores.max()) + 0.05
    x_range = np.linspace(x_min, x_max, 500)

    kde_benign = gaussian_kde(benign_scores, bw_method=0.3)   # bw_method controls smoothness
    kde_attack = gaussian_kde(attack_scores, bw_method=0.3)

    density_benign = kde_benign(x_range)
    density_attack = kde_attack(x_range)

    # Normalise to 0–1 for clean comparison
    density_benign /= density_benign.max()
    density_attack /= density_attack.max()

    # ── PLOTTING ────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 7))

    # Filled area
    ax.fill_between(x_range, density_benign, alpha=0.15, color='#27ae60')
    ax.fill_between(x_range, density_attack, alpha=0.15, color='#c0392b')

    # Smooth KDE lines
    ax.plot(x_range, density_benign, color='#27ae60', linewidth=2.5, label='Normal (benign)')
    ax.plot(x_range, density_attack, color='#c0392b', linewidth=2.5, label='Attack / anomaly')

    # Overlap region shading
    overlap = np.minimum(density_benign, density_attack)
    ax.fill_between(x_range, overlap, alpha=0.35, color='#f39c12', label='Overlap zone (FP/FN)')

    # ── FIX 4: Threshold from model, not hardcoded 0.0 ──────────────────
    ax.axvline(x=threshold, color='#34495e', linestyle='--', linewidth=2,
               label=f'Decision threshold ({threshold:.3f})')

    # Peak annotations
    b_peak_x = x_range[np.argmax(density_benign)]
    a_peak_x = x_range[np.argmax(density_attack)]
    ax.annotate(f'Normal peak\n{b_peak_x:.3f}',
                xy=(b_peak_x, 1.0), xytext=(b_peak_x + 0.06, 1.05),
                arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.2),
                color='#27ae60', fontsize=9)
    ax.annotate(f'Attack peak\n{a_peak_x:.3f}',
                xy=(a_peak_x, 1.0), xytext=(a_peak_x - 0.14, 1.05),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2),
                color='#c0392b', fontsize=9)

    # Separation bracket
    ax.annotate('', xy=(b_peak_x, 0.5), xytext=(a_peak_x, 0.5),
                arrowprops=dict(arrowstyle='<->', color='#7f8c8d', lw=1.2))
    ax.text((a_peak_x + b_peak_x) / 2, 0.52,
            f'separation = {separation:.3f}', ha='center', va='bottom',
            fontsize=9, color='#7f8c8d')

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(0, 1.25)
    ax.set_xlabel('Isolation Forest anomaly score  (← more anomalous | more benign →)', fontsize=12)
    ax.set_ylabel('Density (normalised)', fontsize=12)
    ax.set_title(
        'Isolation Forest: anomaly score distribution (KDE)\n'
        'Separation of benign vs attack traffic — IoT honeypot',
        fontsize=14, fontweight='bold', pad=14
    )
    ax.legend(loc='upper left', fontsize=10, frameon=True, framealpha=0.9)
    ax.grid(alpha=0.15, linestyle=':')

    # Stats box
    stats_text = (
        f"Benign:  μ={benign_scores.mean():.3f}, σ={benign_scores.std():.3f}  n=300\n"
        f"Attack:  μ={attack_scores.mean():.3f}, σ={attack_scores.std():.3f}  n=300\n"
        f"Peak separation: {separation:.3f}\n"
        f"Threshold (offset_): {threshold:.4f}"
    )
    ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
            fontsize=8.5, va='top', ha='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.85, edgecolor='#bdc3c7'),
            family='monospace')

    fig.text(0.5, 0.01,
             "Methodology: scipy gaussian_kde (bw=0.3) on Isolation Forest decision_function scores. "
             "Threshold = model.offset_",
             ha='center', fontsize=9, style='italic', color='#7f8c8d')

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    save_path = "ul_anomaly_distribution_kde.png"
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"\n[SUCCESS] Saved as '{save_path}'")
    plt.show()


if __name__ == "__main__":
    generate_kde_plot()