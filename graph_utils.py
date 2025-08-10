import matplotlib


matplotlib.use('Agg')

import matplotlib.pyplot as plt
import io
import base64

def create_plot(dates, data, title, label, color):
    """Creates a plot and returns it as a base64 encoded image string."""
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.plot(dates, data, color=color, marker='o', linestyle='-')

    # Formatting
    ax.set_title(title, color='white', fontsize=16)
    ax.set_ylabel(label, color='white', fontsize=12)
    ax.tick_params(axis='x', colors='white', rotation=45, labelsize=10)
    ax.tick_params(axis='y', colors='white')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='#555555')
    fig.patch.set_facecolor('#1f2937')
    ax.set_facecolor('#1f2937')

    for spine in ax.spines.values():
        spine.set_edgecolor('#555555')

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{image_base64}"