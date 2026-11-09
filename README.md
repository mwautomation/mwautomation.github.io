# MW AI Solutions

Static, bilingual consultancy website. Polish is served at `/`, English at `/en/`.
Both pages share `assets/site.css` and `assets/site.js`. No build or production
JavaScript dependencies are required. GitHub Pages can serve the repository directly.

## Local preview

From this directory, run:

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Open <http://127.0.0.1:8000/> or <http://127.0.0.1:8000/en/>. Use an HTTP server
rather than opening the HTML files directly: asset paths are relative to the site root.

## Content and contact

Update both HTML pages together when changing copy. The workflow examples are
illustrative, not client case studies. Keep claims, business information and
professional links grounded in verified information.

The contact form posts `name`, `email` and `message` to the existing Formspree
endpoint. JavaScript provides localized validation, submission feedback and a
15-second timeout; unsuccessful submissions retain the entered values. Without
JavaScript, the native HTML form remains usable. LinkedIn offers another contact route.

Google Fonts provides DM Sans and Manrope, with local sans-serif fallbacks.
Logo and social preview artwork remain in `assets/`.

`assets/grok-logomark.svg` is an unchanged copy of the supplied
`Grok_Logomark_Dark.svg` from the official Grok asset pack. It identifies the
tool used in the agent integration service and links to the Grok Bot product
page. It does not indicate a partnership or endorsement. Preserve the original
mark and follow <https://x.ai/legal/brand-guidelines> when updating it.

## Browser checks

Install Python development dependencies `playwright` and `html5lib`, then run
`python tests/site_check.py`. The checks use an installed Microsoft Edge browser,
start and stop a temporary loopback HTTP server, validate both HTML documents,
and cover four viewport sizes, navigation focus, reduced motion and mocked form
responses. They never submit an enquiry. Screenshots are written to a temporary
directory printed by the script. These tools are not needed to serve the website.
