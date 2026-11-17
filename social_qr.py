"""
Generate LinkedIn, GitHub and Email QR codes with an icon in the middle.

Usage
-----
    python social_qr.py                       # uses the URLs configured below
    python social_qr.py --linkedin https://www.linkedin.com/in/your-name/ \
                        --github   https://github.com/your-username

Email QR (opens a pre-addressed new message when scanned):
    python social_qr.py --email you@example.com --email-provider gmail
    python social_qr.py --email you@example.com --email-provider outlook
    python social_qr.py --email you@example.com --email-provider all   # one QR per provider
    (providers: mailto = phone's default mail app [default], gmail, outlook, all)

Optional: use your own icon files (PNG with transparent background works best)
    python social_qr.py --linkedin-icon icons/linkedin.png --github-icon icons/github.png

Requires:  pip install segno pillow
"""

import argparse
import io
from pathlib import Path
from urllib.parse import quote

import segno
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# CONFIG: edit these
# --------------------------------------------------------------------------
LINKEDIN_URL = "https://www.linkedin.com/in/your-name/"
GITHUB_URL = "https://github.com/your-username"

EMAIL_ADDRESS = "khizer.zakir@plus.ac.at"
EMAIL_SUBJECT = ""     # optional pre-filled subject
EMAIL_BODY = ""        # optional pre-filled message

LINKEDIN_BLUE = "#0A66C2"
GITHUB_DARK = "#181717"
EMAIL_COLOURS = {"mailto": "#444444", "gmail": "#EA4335", "outlook": "#0078D4"}

MODULE_SIZE = 20       # pixels per QR module (bigger = sharper image)
BORDER = 4             # quiet zone in modules (keep >= 4 for reliable scanning)
LOGO_RATIO = 0.22      # logo width as a fraction of the QR width (keep <= 0.25)
LOGO_PADDING = 0.18    # white padding around the logo, as a fraction of logo size
# --------------------------------------------------------------------------


def _bold_font(size: int) -> ImageFont.FreeTypeFont:
    """Find a bold font on any OS; fall back to Pillow's built-in one."""
    candidates = [
        "arialbd.ttf",                                            # Windows
        "Arial Bold.ttf",                                         # macOS
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",      # macOS
        "DejaVuSans-Bold.ttf",                                    # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",   # Linux
        "LiberationSans-Bold.ttf",                                # Linux
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def linkedin_icon(size: int = 400) -> Image.Image:
    """Built-in LinkedIn-style badge: blue rounded square with a white 'in'."""
    ss = 4  # supersample for smooth edges
    big = size * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, big, big), radius=int(big * 0.18), fill=LINKEDIN_BLUE)

    font = _bold_font(int(big * 0.62))
    d.text((big / 2, big * 0.52), "in", font=font, fill="white", anchor="mm")
    return img.resize((size, size), Image.LANCZOS)


def github_icon(size: int = 400) -> Image.Image:
    """Built-in GitHub-style badge: dark circle with a white cat-head mark."""
    ss = 4
    big = size * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((0, 0, big, big), fill=GITHUB_DARK)

    cx, cy = big / 2, big * 0.54
    r = big * 0.27
    # ears
    d.polygon([(cx - r * 0.95, cy - r * 0.35), (cx - r * 0.85, cy - r * 1.35), (cx - r * 0.15, cy - r * 0.85)], fill="white")
    d.polygon([(cx + r * 0.95, cy - r * 0.35), (cx + r * 0.85, cy - r * 1.35), (cx + r * 0.15, cy - r * 0.85)], fill="white")
    # head
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="white")
    # eyes
    er = r * 0.11
    for ex in (-r * 0.38, r * 0.38):
        d.ellipse((cx + ex - er, cy - r * 0.1 - er, cx + ex + er, cy - r * 0.1 + er), fill=GITHUB_DARK)
    return img.resize((size, size), Image.LANCZOS)


def email_icon(colour: str):
    """Return a function that draws an envelope badge in the given colour."""
    def _draw(size: int = 400) -> Image.Image:
        ss = 4
        big = size * ss
        img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, big, big), radius=int(big * 0.18), fill=colour)

        # envelope body
        x0, y0, x1, y1 = big * 0.20, big * 0.29, big * 0.80, big * 0.71
        d.rounded_rectangle((x0, y0, x1, y1), radius=int(big * 0.04), fill="white")
        # flap
        lw = int(big * 0.035)
        d.line([(x0 + big * 0.02, y0 + big * 0.03), (big / 2, big * 0.53), (x1 - big * 0.02, y0 + big * 0.03)],
               fill=colour, width=lw, joint="curve")
        return img.resize((size, size), Image.LANCZOS)
    return _draw


def email_url(address: str, provider: str, subject: str = "", body: str = "") -> str:
    """Build the link the QR code will open."""
    to, su, bo = quote(address), quote(subject), quote(body)
    if provider == "gmail":
        return f"https://mail.google.com/mail/?view=cm&fs=1&to={to}&su={su}&body={bo}"
    if provider == "outlook":
        return f"https://outlook.live.com/mail/0/deeplink/compose?to={to}&subject={su}&body={bo}"
    # plain mailto: opens whatever mail app the phone uses (Gmail, Outlook, Apple Mail...)
    parts = []
    if subject:
        parts.append(f"subject={su}")
    if body:
        parts.append(f"body={bo}")
    return f"mailto:{address}" + ("?" + "&".join(parts) if parts else "")


def load_icon(path: str | None, fallback) -> Image.Image:
    """Load a user-supplied icon, or use the built-in fallback."""
    if path:
        return Image.open(path).convert("RGBA")
    return fallback()


def add_logo(qr_img: Image.Image, logo: Image.Image) -> Image.Image:
    """Paste the logo centred on the QR code, on a white rounded backing."""
    qr_img = qr_img.convert("RGBA")
    w, h = qr_img.size

    logo_w = int(w * LOGO_RATIO)
    logo = logo.copy()
    logo.thumbnail((logo_w, logo_w), Image.LANCZOS)

    pad = int(max(logo.size) * LOGO_PADDING)
    box_w, box_h = logo.width + 2 * pad, logo.height + 2 * pad
    box_x, box_y = (w - box_w) // 2, (h - box_h) // 2

    backing = Image.new("RGBA", qr_img.size, (0, 0, 0, 0))
    ImageDraw.Draw(backing).rounded_rectangle(
        (box_x, box_y, box_x + box_w, box_y + box_h),
        radius=int(box_w * 0.2),
        fill="white",
    )
    qr_img = Image.alpha_composite(qr_img, backing)
    qr_img.alpha_composite(logo, (box_x + pad, box_y + pad))
    return qr_img


def make_qr_with_logo(url: str, logo: Image.Image, colour: str, out_path: Path) -> None:
    # error="h" -> ~30% of the code can be covered and it still scans
    qr = segno.make_qr(url, error="h")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=MODULE_SIZE, border=BORDER, dark=colour, light="white")
    buf.seek(0)
    img = Image.open(buf)
    add_logo(img, logo).convert("RGB").save(out_path)
    print(f"Saved {out_path}  ->  {url}")


def main() -> None:
    p = argparse.ArgumentParser(description="LinkedIn + GitHub QR codes with logos")
    p.add_argument("--linkedin", default=LINKEDIN_URL, help="LinkedIn profile URL")
    p.add_argument("--github", default=GITHUB_URL, help="GitHub profile URL")
    p.add_argument("--email", default=EMAIL_ADDRESS, help="Email address")
    p.add_argument("--email-provider", default="mailto",
                   choices=["mailto", "gmail", "outlook", "all"],
                   help="Where the email QR opens (default: mailto)")
    p.add_argument("--subject", default=EMAIL_SUBJECT, help="Pre-filled subject")
    p.add_argument("--body", default=EMAIL_BODY, help="Pre-filled message body")
    p.add_argument("--email-icon", help="Path to a custom email icon image")
    p.add_argument("--linkedin-icon", help="Path to a custom LinkedIn icon image")
    p.add_argument("--github-icon", help="Path to a custom GitHub icon image")
    p.add_argument("--out", default=".", help="Output folder (default: current)")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    make_qr_with_logo(
        args.linkedin,
        load_icon(args.linkedin_icon, linkedin_icon),
        LINKEDIN_BLUE,
        out / "linkedin_qr.png",
    )
    make_qr_with_logo(
        args.github,
        load_icon(args.github_icon, github_icon),
        GITHUB_DARK,
        out / "github_qr.png",
    )

    providers = ["mailto", "gmail", "outlook"] if args.email_provider == "all" else [args.email_provider]
    for prov in providers:
        colour = EMAIL_COLOURS[prov]
        name = "email_qr.png" if len(providers) == 1 else f"email_{prov}_qr.png"
        make_qr_with_logo(
            email_url(args.email, prov, args.subject, args.body),
            load_icon(args.email_icon, email_icon(colour)),
            colour,
            out / name,
        )


if __name__ == "__main__":
    main()