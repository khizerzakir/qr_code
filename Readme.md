## QR Code Script

This script is designed to generate qr code for your favorite link and/or your own profile. 

### How to?

Just run the following command.


Generate LinkedIn, GitHub and Email QR codes with an icon in the middle.

Usage
-----

    python social_qr.py                # uses the URLs configured below

    python social_qr.py --linkedin https://www.linkedin.com/in/your-name/ \
                     --github   https://github.com/your-username

-----

Email QR (opens a pre-addressed new message when scanned):
-----
    python social_qr.py --email you@example.com --email-provider gmail
    python social_qr.py --email you@example.com --email-provider outlook
    python social_qr.py --email you@example.com --email-provider all   # one QR per provider

    (providers: mailto = phone's default mail app [default], gmail, outlook, all)
-----

Optional: use your own icon files (PNG with transparent background works best)

-----
    python social_qr.py --linkedin-icon icons/linkedin.png --github-icon icons/github.png
-----
Requires:  pip install segno pillow
