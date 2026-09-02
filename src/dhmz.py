"""Fetching DHMZ XML feeds."""
import requests


def fetch_xml(url):
    """Return a feed's body as bytes.

    Bytes, not resp.text: DHMZ sends no charset, so requests would decode the
    UTF-8 feed as ISO-8859-1 and mangle station names.

    ponytail: retries over http when the certificate does not verify. DHMZ
    serves its hostnames from one nginx and has answered vrijeme.hr with
    another vhost's certificate for days; the feeds are public read-only data
    and a missed day cannot be backfilled, so a plaintext fetch is the lesser
    loss. Verification itself is never disabled. Drop the fallback once DHMZ's
    certificates stay correct.
    """
    try:
        resp = requests.get(url, timeout=30)
    except requests.exceptions.SSLError:
        print(f"[warn] {url}: certificate did not verify, retrying over http")
        resp = requests.get(url.replace("https://", "http://", 1), timeout=30)
    resp.raise_for_status()
    return resp.content
