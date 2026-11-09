# MW AI Solutions

Static, bilingual consultancy website. Polish is served at `/`, English at `/en/`.
Both pages share `assets/site.css` and `assets/site.js`. No build or production
JavaScript dependencies are required. GitHub Pages can serve the repository directly.
Privacy notices are served at `/polityka-prywatnosci/` and `/en/privacy/` with
links from the form and footer. They reuse the same navigation and styles.

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
JavaScript, the native HTML form remains usable. Enquiries and requests for a free
30-minute scoping call go through the form; LinkedIn links show the founder's
professional profile. Prototype scope and pricing are agreed after the call.

The privacy notices describe the published business identity and the current
Formspree, GitHub Pages and Google Fonts integrations. When these services or
actual retention practices change, update both notices. Provider privacy links
are included in the pages; account-specific processing agreements and transfer
arrangements are not inferred from public provider policies.

## Founder portrait

The `.portrait-placeholder` element in each homepage is a decorative HTML/CSS
monogram, not a photograph. To add a real portrait, replace this element with an
image of Michał, using a descriptive localized `alt`, a 4:5 aspect ratio,
`object-fit: cover`, and a maximum width of 280px. Use the same image on both
pages, include explicit dimensions, and optimize the supplied file for the web.

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
start and stop a temporary loopback HTTP server, validate all four HTML documents,
and cover 320, 360, 390, 768, 1024 and 1440px viewport widths. They check navigation
focus, reduced motion, minimum text sizes, mobile process columns, privacy links,
portrait proportions, native form fallback and mocked form responses. A separate
check simulates 200% desktop zoom reflow using a half-size CSS viewport and 2x
device scale. These checks never submit an enquiry. Screenshots are written to a temporary
directory printed by the script. These tools are not needed to serve the website.
