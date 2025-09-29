# python
import os
import json
import time
import argparse
from typing import Dict, List, Any, Optional
import requests

TMDB_BASE = "https://api.themoviedb.org/3"

def load_env_from_dotenv(dotenv_path: str = ".env") -> None:
    """
    Minimal .env loader so we don't need python-dotenv.
    Only parses KEY=VALUE lines, ignoring comments and blanks.
    """
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v

def session_with_api_key(api_key: str) -> requests.Session:
    s = requests.Session()
    s.params = {"api_key": api_key}
    s.headers.update({"User-Agent": "movie-recommender/0.1"})
    return s

def tmdb_get(sess: requests.Session, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{TMDB_BASE}{path}"
    for attempt in range(3):
        try:
            resp = sess.get(url, params=params, timeout=20)
            if resp.status_code == 429:
                # Rate-limited — back off
                time.sleep(1.5 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            time.sleep(0.75 * (attempt + 1))
    raise RuntimeError(f"Failed to GET {path} after retries")

def find_keyword_id(sess: requests.Session, query: str) -> Optional[int]:
    data = tmdb_get(sess, "/search/keyword", {"query": query})
    results = data.get("results", [])
    return results[0]["id"] if results else None

def discover_indie_movies(
    sess: requests.Session,
    keyword_id: Optional[int],
    pages: int,
    languages: List[str],
    since: str,
    max_vote_count: Optional[int],
    min_vote_count: int,
    include_adult: bool,
) -> List[Dict[str, Any]]:
    movies = []
    # We’ll loop languages to keep results varied and avoid page caps
    for lang in languages:
        for page in range(1, pages + 1):
            params = {
                "sort_by": "popularity.asc",
                "with_original_language": lang,
                "vote_count.gte": min_vote_count,
                "include_adult": str(include_adult).lower(),
                "page": page,
                "primary_release_date.gte": since,
            }
            if keyword_id:
                params["with_keywords"] = keyword_id
            if max_vote_count is not None:
                params["vote_count.lte"] = max_vote_count
            data = tmdb_get(sess, "/discover/movie", params)
            results = data.get("results", [])
            movies.extend(results)
            time.sleep(0.25)  # be polite
    return movies

def get_movie_details_and_credits(sess: requests.Session, tmdb_id: int) -> Dict[str, Any]:
    details = tmdb_get(sess, f"/movie/{tmdb_id}", {"append_to_response": "keywords"})
    credits = tmdb_get(sess, f"/movie/{tmdb_id}/credits", {})
    director = ""
    for crew in credits.get("crew", []):
        if crew.get("job") == "Director":
            director = crew.get("name", "")
            break
    genre_tags = [g["name"] for g in details.get("genres", [])]
    plot_summary = details.get("overview") or ""
    imdb_id = details.get("imdb_id")
    year = (details.get("release_date") or "0000-00-00")[:4]
    title = details.get("title", "")
    
    # Get poster URL
    poster_path = details.get("poster_path")
    poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    
    return {
        "title": title,
        "year": year,
        "director": director,
        "genre_tags": genre_tags,
        "plot_summary": plot_summary,
        "visual_style": "",
        "imdb_id": imdb_id,
        "tmdb_id": tmdb_id,
        "poster_url": poster_url,
    }

def _best(value: Optional[str]) -> Optional[str]:
    if not value or value == "N/A":
        return None
    return value.strip()

def enrich_with_omdb(core: Dict[str, Any], omdb_api_key: Optional[str]) -> Dict[str, Any]:
    if not omdb_api_key:
        return core
    params = {"apikey": omdb_api_key, "plot": "full"}
    if core.get("imdb_id"):
        params["i"] = core["imdb_id"]
    else:
        if core.get("title"):
            params["t"] = core["title"]
            if core.get("year"):
                params["y"] = core["year"]
        else:
            return core
    try:
        r = requests.get("https://www.omdbapi.com/", params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException:
        return core
    if not data or data.get("Response") != "True":
        return core

    plot = _best(data.get("Plot"))
    if plot and (len(plot) > len(core.get("plot_summary") or "")):
        core["plot_summary"] = plot

    director = _best(data.get("Director"))
    if director:
        core["director"] = director

    genre_csv = _best(data.get("Genre"))
    if genre_csv:
        existing = set(core.get("genre_tags") or [])
        for g in [g.strip() for g in genre_csv.split(",") if g.strip()]:
            existing.add(g)
        core["genre_tags"] = sorted(existing)

    omdb_imdb_id = _best(data.get("imdbID"))
    if omdb_imdb_id and not core.get("imdb_id"):
        core["imdb_id"] = omdb_imdb_id

    return core

def map_to_schema(core: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": core["title"],
        "year": core["year"],
        "director": core["director"],
        "genre_tags": core["genre_tags"],
        "plot_summary": core["plot_summary"],
        "visual_style": core.get("visual_style", ""),
        "critic_reviews": core.get("critic_reviews", []),
        "user_reviews": core.get("user_reviews", []),
        "imdb_id": core.get("imdb_id"),
        "tmdb_id": core.get("tmdb_id"),
        "poster_url": core.get("poster_url"),
    }

def fetch_top_rated(sess: requests.Session, count: int, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Pulls top-rated movies from TMDb (proxy for IMDb Top 250).
    Returns a list of result objects (from /movie/top_rated) up to 'count'.
    """
    movies: List[Dict[str, Any]] = []
    page = 1
    while len(movies) < count:
        params: Dict[str, Any] = {"page": page}
        if region:
            params["region"] = region
        data = tmdb_get(sess, "/movie/top_rated", params)
        results = data.get("results", []) or []
        if not results:
            break
        movies.extend(results)
        page += 1
        time.sleep(0.2)
    return movies[:count]

def fetch_tmdb_list(sess: requests.Session, list_id: str) -> List[Dict[str, Any]]:
    """
    Fetch items from a public TMDb list (user-curated). Returns 'results' array
    compatible with subsequent hydration (contains 'id' for each movie).
    """
    path = f"/list/{list_id}"
    page = 1
    items: List[Dict[str, Any]] = []
    while True:
        data = tmdb_get(sess, path, {"page": page})
        results = data.get("items", []) or []
        if not results:
            break
        # Only keep movies; items may include TV etc.
        for it in results:
            if it.get("media_type") == "movie" or "id" in it:
                items.append({"id": it["id"]})
        if page >= (data.get("total_pages") or 1):
            break
        page += 1
        time.sleep(0.2)
    return items

def tmdb_search_movie(sess: requests.Session, title: str, year: Optional[str]) -> Optional[int]:
    """
    Search TMDb by title (and optionally year) and return tmdb_id.
    """
    params: Dict[str, Any] = {"query": title, "include_adult": "false", "page": 1}
    if year and year.isdigit():
        params["year"] = int(year)
    data = tmdb_get(sess, "/search/movie", params)
    results = data.get("results", []) or []
    if not results:
        return None
    return results[0].get("id")

def tmdb_external_ids(sess: requests.Session, tmdb_id: int) -> Dict[str, Any]:
    return tmdb_get(sess, f"/movie/{tmdb_id}/external_ids", {})

def load_seeds_csv(csv_path: str) -> List[Dict[str, Optional[str]]]:
    """
    CSV columns supported: title,year,imdb_id,tmdb_id
    Header required. Extra columns ignored.
    """
    import csv
    rows: List[Dict[str, Optional[str]]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "title": (row.get("title") or "").strip(),
                "year": (row.get("year") or "").strip(),
                "imdb_id": (row.get("imdb_id") or "").strip(),
                "tmdb_id": (row.get("tmdb_id") or "").strip(),
            })
    return rows

# --- Wikipedia scraping helpers (no extra deps) ---
import re
import html as html_lib

def fetch_wikipedia_html(url: str) -> str:
    """
    Fetches the fully-rendered HTML of the Wikipedia page.
    Uses desktop HTML (not API) to keep it simple.
    """
    headers = {"User-Agent": "movie-recommender/0.1 (+https://example.com)"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def extract_first_wikitable(html: str) -> str:
    """
    Extract the first wikitable-style table that likely contains movies.
    Heuristics: class contains 'wikitable', and headers include 'Film' or 'Title'.
    """
    # Find all wikitable blocks quickly
    tables = re.findall(r'(<table[^>]*class="[^"]*wikitable[^"]*"[^>]*>.*?</table>)', html, flags=re.S | re.I)
    for tbl in tables:
        # Check header row for Film/Title
        header_txt = re.findall(r"<th[^>]*>(.*?)</th>", tbl, flags=re.S | re.I)
        header_plain = " ".join([re.sub("<.*?>", "", h) for h in header_txt])  # strip tags
        if re.search(r"\b(Film|Title)\b", header_plain, flags=re.I):
            return tbl
    return tables[0] if tables else ""

def parse_movies_from_wikitable(table_html: str) -> List[Dict[str, str]]:
    """
    Parse rows from the wikitable and extract (title, year).
    Tries to be resilient but intentionally simple.
    """
    if not table_html:
        return []
    rows = re.split(r"</tr>\s*<tr[^>]*>", re.sub(r"^.*?<tr[^>]*>|</tr>.*?$", "", table_html, flags=re.S | re.I, count=1), flags=re.S | re.I)
    movies: List[Dict[str, str]] = []
    for row in rows:
        # Extract a likely title from an italicized link first
        m = re.search(r"<i>\s*<a[^>]*>([^<]+)</a>\s*</i>", row, flags=re.S | re.I)
        title = m.group(1).strip() if m else None
        if not title:
            # Fallback: any anchor in the row (less precise)
            m2 = re.search(r"<a[^>]*>([^<]+)</a>", row, flags=re.S | re.I)
            title = m2.group(1).strip() if m2 else None
        if not title:
            continue
        title = html_lib.unescape(re.sub(r"\s+", " ", title))

        # Find a 4-digit year (1900–2029) in any cell
        y = re.search(r"\b(19\d{2}|20[0-2]\d)\b", re.sub("<.*?>", " ", row))
        year = y.group(1) if y else ""

        movies.append({"title": title, "year": year})
    return movies

def scrape_wikipedia_movies(url: str) -> List[Dict[str, str]]:
    """
    High-level: fetch page, locate the first wikitable listing films, extract title/year pairs.
    """
    html = fetch_wikipedia_html(url)
    table = extract_first_wikitable(html)
    return parse_movies_from_wikitable(table)

def hydrate_from_wikipedia(sess: requests.Session, url: str, omdb_api_key: Optional[str]) -> List[Dict[str, Any]]:
    """
    Scrape a Wikipedia list page (like AFI Top 100), then resolve via TMDb + enrich via OMDb.
    """
    seeds = scrape_wikipedia_movies(url)
    results: List[Dict[str, Any]] = []
    seen: set = set()

    for s in seeds:
        title = s.get("title") or ""
        year = s.get("year") or ""
        if not title:
            continue

        # Resolve to TMDb ID (title + year if possible)
        tmdb_id = tmdb_search_movie(sess, title, year)
        core: Dict[str, Any]

        if tmdb_id:
            core = get_movie_details_and_credits(sess, tmdb_id)
            # Ensure imdb_id if missing
            if not core.get("imdb_id"):
                ext = tmdb_external_ids(sess, tmdb_id)
                if ext.get("imdb_id"):
                    core["imdb_id"] = ext["imdb_id"]
        else:
            # Fallback shell in case TMDb search misses some classic/older titles
            core = {
                "title": title,
                "year": year,
                "director": "",
                "genre_tags": [],
                "plot_summary": "",
                "visual_style": "",
                "imdb_id": None,
                "tmdb_id": None,
            }

        core["critic_reviews"] = []
        core["user_reviews"] = []

        # OMDb enrichment (fills plot, director, genres; may also fix title/year if via imdbID)
        core = enrich_with_omdb(core, omdb_api_key)

        uniq = core.get("imdb_id") or (f"tmdb:{core.get('tmdb_id')}" if core.get("tmdb_id") else f"title:{title}|year:{year}")
        if uniq in seen:
            continue
        seen.add(uniq)

        # Only keep items with a title (OMDb may sometimes not return anything)
        if core.get("title"):
            results.append(map_to_schema(core))

        time.sleep(0.2)  # be polite

    return results
def build_dataset(
    pages: int,
    languages: List[str],
    since: str,
    max_vote_count: Optional[int],
    min_vote_count: int,
    include_adult: bool,
    source: str,
    count: int,
    region: Optional[str],
    list_id: Optional[str],
    csv_path: Optional[str],
    wiki_url: Optional[str],
    bfi_url: Optional[str] = None,
    letterboxd_url: Optional[str] = None,
) -> Dict[str, Any]:
    load_env_from_dotenv()
    tmdb_api_key = os.environ.get("TMDB_API_KEY")
    omdb_api_key = os.environ.get("OMDB_API_KEY")

    if not tmdb_api_key:
        raise SystemExit("TMDB_API_KEY is not set in environment or .env")

    sess = session_with_api_key(tmdb_api_key)

    if source == "top_rated":
        discovered = fetch_top_rated(sess, count=count, region=region)
        results = []
        seen: set = set()
        for m in discovered:
            tmdb_id = m["id"]
            core = get_movie_details_and_credits(sess, tmdb_id)
            uniq = core.get("imdb_id") or f"tmdb:{tmdb_id}"
            if uniq in seen:
                continue
            seen.add(uniq)
            core["critic_reviews"] = []
            core["user_reviews"] = []
            core = enrich_with_omdb(core, omdb_api_key)
            results.append(map_to_schema(core))
            time.sleep(0.25)
        return {"movies": results}

    if source == "tmdb_list":
        if not list_id:
            raise SystemExit("--list-id is required for source=tmdb_list")
        results = hydrate_from_tmdb_list(sess, list_id, omdb_api_key)
        return {"movies": results}

    if source == "csv":
        if not csv_path:
            raise SystemExit("--csv-path is required for source=csv")
        results = hydrate_from_csv(sess, csv_path, omdb_api_key)
        return {"movies": results}

    if source == "wikipedia":
        if not wiki_url:
            raise SystemExit("--wiki-url is required for source=wikipedia")
        results = hydrate_from_wikipedia(sess, wiki_url, omdb_api_key)
        return {"movies": results}

    if source == "bfi":
        # Prefer explicit --bfi-url, but allow repurposing --wiki-url for convenience
        url = bfi_url or wiki_url
        if not url:
            raise SystemExit("--bfi-url is required for source=bfi (or provide --wiki-url as the BFI URL)")
        results = hydrate_from_bfi(sess, url, omdb_api_key)
        return {"movies": results}

    if source == "letterboxd":
        url = letterboxd_url
        if not url:
            raise SystemExit("--letterboxd-url is required for source=letterboxd")
        results = hydrate_from_letterboxd(sess, url, omdb_api_key)
        return {"movies": results}

    # default: discover mode (indie-ish)
    indie_kw_id = find_keyword_id(sess, "independent film")
    discovered = discover_indie_movies(
        sess,
        indie_kw_id,
        pages=pages,
        languages=languages,
        since=since,
        max_vote_count=max_vote_count,
        min_vote_count=min_vote_count,
        include_adult=include_adult,
    )

    results = []
    seen: set = set()
    for m in discovered:
        tmdb_id = m["id"]
        core = get_movie_details_and_credits(sess, tmdb_id)
        uniq = core.get("imdb_id") or f"tmdb:{tmdb_id}"
        if uniq in seen:
            continue
        seen.add(uniq)
        core["critic_reviews"] = []
        core["user_reviews"] = []
        core = enrich_with_omdb(core, omdb_api_key)
        results.append(map_to_schema(core))
        time.sleep(0.25)

    return {"movies": results}

def main():
    parser = argparse.ArgumentParser(description="Build movie dataset via TMDb + optional OMDb enrichment.")
    parser.add_argument("--source", choices=["discover", "top_rated", "tmdb_list", "csv", "wikipedia", "bfi", "letterboxd"], default="discover",
                        help="Mode: 'discover', 'top_rated', 'tmdb_list', 'csv', 'wikipedia', 'bfi', or 'letterboxd'")
    parser.add_argument("--count", type=int, default=100,
                        help="Number of movies for 'top_rated' mode")
    parser.add_argument("--region", type=str, default=None,
                        help="Optional region code (e.g., US) for 'top_rated' mode")
    parser.add_argument("--list-id", type=str, default=None,
                        help="TMDb list ID for 'tmdb_list' mode")
    parser.add_argument("--csv-path", type=str, default=None,
                        help="CSV path for 'csv' mode (columns: title,year,imdb_id,tmdb_id)")
    parser.add_argument("--wiki-url", type=str, default=None,
                        help="Wikipedia list URL for 'wikipedia' mode")
    parser.add_argument("--bfi-url", type=str, default=None,
                        help="BFI Sight & Sound list URL for 'bfi' mode")
    parser.add_argument("--letterboxd-url", type=str, default=None,
                        help="Letterboxd list URL for 'letterboxd' mode" )
    parser.add_argument("--pages", type=int, default=2, help="Pages per language for 'discover' mode")
    parser.add_argument("--languages", type=str, default="en",
                        help="Comma-separated original languages for 'discover' mode")
    parser.add_argument("--since", type=str, default="2012-01-01", help="Release date lower bound for 'discover'")
    parser.add_argument("--max-vote-count", type=int, default=500,
                        help="Upper cap on vote_count (0 to disable) for 'discover'")
    parser.add_argument("--min-vote-count", type=int, default=5, help="Lower bound on vote_count for 'discover'")
    parser.add_argument("--include-adult", action="store_true", help="Include adult results for 'discover'")
    parser.add_argument("--out", type=str, default="scraped_movie_data.json", help="Output JSON path")
    args = parser.parse_args()

    max_vote = None if args.max_vote_count == 0 else args.max_vote_count
    languages = [x.strip() for x in args.languages.split(",") if x.strip()]

    dataset = build_dataset(
        pages=args.pages,
        languages=languages,
        since=args.since,
        max_vote_count=max_vote,
        min_vote_count=args.min_vote_count,
        include_adult=args.include_adult,
        source=args.source,
        count=args.count,
        region=args.region,
        list_id=args.list_id,
        csv_path=args.csv_path,
        wiki_url=args.wiki_url,
        bfi_url=args.bfi_url,
        letterboxd_url=args.letterboxd_url,
    )

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(dataset['movies'])} movies to {args.out}")

# --- BFI Sight & Sound scraping helpers (site-specific, no extra deps) ---
import re as _re
import json as _json

BFI_BASE = "https://www.bfi.org.uk"

def fetch_bfi_html(url: str) -> str:
    """Fetch HTML with multiple headers and simple retries to avoid 403/anti-bot.
    Minimal dependency approach: uses requests only.
    """
    ua_pool = [
        # Modern Chrome on Windows
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        # Safari on macOS
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
        ),
        # Firefox
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0"
        ),
    ]
    last_err: Optional[Exception] = None
    for i, ua in enumerate(ua_pool):
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Connection": "close",
        }
        try:
            r = requests.get(url, headers=headers, timeout=30)
            # Some CDNs return 403 with a JavaScript challenge page — surface as error to try next UA
            if r.status_code >= 400:
                r.raise_for_status()
            text = r.text
            # Basic sanity check: ensure we didn't get a bot-block page
            if "cf-chl-bypass" in text or "captcha" in text.lower():
                raise RuntimeError("Blocked by anti-bot")
            return text
        except Exception as e:
            last_err = e
            time.sleep(0.6)
            continue
    # Last resort try with a Referer hint
    try:
        headers = {
            "User-Agent": ua_pool[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "Referer": BFI_BASE + "/sight-and-sound",
            "Connection": "close",
        }
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        if last_err:
            raise last_err
        raise e

def _strip_tags(text: str) -> str:
    return _re.sub(r"<.*?>", " ", text or "", flags=_re.S | _re.I)

def parse_bfi_titles(html: str) -> List[Dict[str, str]]:
    """
    Parser for BFI Sight & Sound list pages with multiple fallbacks:
    - Pass 1: anchor scan under /sight-and-sound/ (prefer paths containing /film/ or slug-YYYY)
    - Pass 2: JSON-LD ItemList fallback (common on modern static pages)
    Returns unique dicts of {title, year} (year may be empty).
    """
    results: List[Dict[str, str]] = []
    if not html:
        return results

    # Relaxed anchor pattern: capture any link under /sight-and-sound/
    anchors = list(_re.finditer(r'<a[^>]+href="(/sight-and-sound/[^"#?]+)"[^>]*>(.*?)</a>', html, flags=_re.S | _re.I))
    seen_hrefs = set()
    for m in anchors:
        href = m.group(1)
        # keep film-like links only
        if not ("/film/" in href or _re.search(r"/[a-z0-9-]+-\d{4}(?:/|$)", href)):
            continue
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)
        title_html = m.group(2)
        title = _strip_tags(title_html)
        title = _re.sub(r"\s+", " ", title).strip()
        if not title:
            continue
        # Look ahead in nearby context for a year
        start = m.end()
        end = min(len(html), start + 800)
        ctx = _strip_tags(html[start:end])
        y = _re.search(r"\b(19\d{2}|20[0-2]\d)\b", ctx)
        year = y.group(1) if y else ""
        results.append({"title": title, "year": year})

    if results:
        # Deduplicate by (title, year)
        uniq: List[Dict[str, str]] = []
        seen = set()
        for r in results:
            key = (r.get("title") or "", r.get("year") or "")
            if key in seen:
                continue
            seen.add(key)
            uniq.append(r)
        return uniq

    # JSON-LD fallback: look for ItemList with names
    for sm in _re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, flags=_re.S | _re.I):
        blob = sm.group(1).strip()
        try:
            data = _json.loads(blob)
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        for obj in objs:
            if isinstance(obj, dict) and obj.get("@type") == "ItemList" and isinstance(obj.get("itemListElement"), list):
                for el in obj["itemListElement"]:
                    item = el.get("item") if isinstance(el, dict) else None
                    name = None
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("headline")
                    if not name and isinstance(el, dict):
                        name = el.get("name")
                    if not name:
                        continue
                    year = ""
                    m = _re.search(r"\((19\d{2}|20[0-2]\d)\)\s*$", name)
                    if m:
                        year = m.group(1)
                        name = name[:m.start()].strip()
                    results.append({"title": name.strip(), "year": year})
        if results:
            uniq: List[Dict[str, str]] = []
            seen = set()
            for r in results:
                key = (r.get("title") or "", r.get("year") or "")
                if key in seen:
                    continue
                seen.add(key)
                uniq.append(r)
            return uniq

    # Text-based fallback for numbered list patterns like "1. Title (Year)"
    text = _strip_tags(html)
    # Normalize whitespace
    text = _re.sub(r"[\t\r]+", " ", text)
    candidates: List[Dict[str, str]] = []
    for lm in _re.finditer(r"(?:^|\n)\s*\d{1,3}\s*[\.).:-]\s*([^\n]+)", text):
        line = lm.group(1).strip()
        # Extract title and optional year from the line
        m = _re.search(r"(.+?)\s*\((19\d{2}|20[0-2]\d)\)$", line)
        if m:
            title = m.group(1).strip()
            year = m.group(2)
        else:
            # If no year, take the whole line as title but skip overly short/noisy strings
            title = line
            year = ""
        # Basic cleanliness checks
        if len(title) < 2:
            continue
        if any(bad in title.lower() for bad in ["bfi", "sight and sound", "top 100", "rank", "vote", "poll", "director"]):
            continue
        candidates.append({"title": title, "year": year})

    if candidates:
        uniq: List[Dict[str, str]] = []
        seen = set()
        for r in candidates:
            key = (r.get("title") or "", r.get("year") or "")
            if key in seen:
                continue
            seen.add(key)
            uniq.append(r)
        return uniq

    return []

def scrape_bfi_sight_and_sound(url: str) -> List[Dict[str, str]]:
    """
    Fetch the BFI page and aggregate titles. If the main page yields nothing,
    try the AMP variant, and paginate both normal and AMP (?page=2,3,...).
    If still empty, auto-discover candidate subpages from the hub page (e.g.,
    '/sight-and-sound/polls/...-100') and aggregate titles from those pages too.
    """
    seeds: List[Dict[str, str]] = []
    try:
        html = fetch_bfi_html(url)
    except Exception:
        return []
    seeds.extend(parse_bfi_titles(html))

    # Fallback to AMP when nothing is found
    if not seeds:
        amp = url.rstrip("/") + "/amp"
        try:
            html_amp = fetch_bfi_html(amp)
            seeds.extend(parse_bfi_titles(html_amp))
        except Exception:
            pass

    # Paginate normal and AMP variants
    page = 2
    while True:
        more: List[Dict[str, str]] = []
        paged = url + ("&" if "?" in url else "?") + f"page={page}"
        try:
            more = parse_bfi_titles(fetch_bfi_html(paged))
        except Exception:
            more = []
        if not more:
            paged_amp = (url.rstrip("/") + "/amp") + ("&" if "?" in url else "?") + f"page={page}"
            try:
                more = parse_bfi_titles(fetch_bfi_html(paged_amp))
            except Exception:
                more = []
        if not more:
            break
        existing = {(s.get("title") or "", s.get("year") or "") for s in seeds}
        added = 0
        for m in more:
            k = (m.get("title") or "", m.get("year") or "")
            if k not in existing:
                seeds.append(m)
                added += 1
        if added == 0:
            break
        page += 1
        time.sleep(0.2)

    # If still empty, auto-discover likely subpages (hub page case)
    if not seeds and html:
        # Find candidate links to poll/list pages and top-100 variants
        sub_links = []
        for am in _re.finditer(r'<a[^>]+href="(/sight-and-sound/[^"]+)"', html, flags=_re.I):
            href = am.group(1)
            if any(x in href for x in ["/polls/", "greatest-films-all-time", "top-100", "100-greatest"]):
                # Avoid links to tags or non-article pages
                if "/tag/" in href or "/people/" in href:
                    continue
                # Normalize to absolute URL
                absolute = href if href.startswith("http") else (BFI_BASE + href)
                if absolute not in sub_links:
                    sub_links.append(absolute)
        # Try a small set of most promising links first
        for link in sub_links[:8]:
            try:
                sub_html = fetch_bfi_html(link)
            except Exception:
                continue
            got = parse_bfi_titles(sub_html)
            if not got:
                # try AMP of subpage too
                try:
                    sub_amp = link.rstrip("/") + "/amp"
                    got = parse_bfi_titles(fetch_bfi_html(sub_amp))
                except Exception:
                    got = []
            if got:
                existing = {(s.get("title") or "", s.get("year") or "") for s in seeds}
                for g in got:
                    k = (g.get("title") or "", g.get("year") or "")
                    if k not in existing:
                        seeds.append(g)
                # No need to paginate subpages aggressively; lists are usually complete
            time.sleep(0.15)

    # Deterministic fallbacks for common hub URL → specific poll list pages
    if not seeds and ("/sight-and-sound/greatest-films-all-time" in url):
        fallback_candidates = [
            BFI_BASE + "/sight-and-sound/polls/greatest-films-all-time-2022/top-100",
            BFI_BASE + "/sight-and-sound/polls/directors-100-greatest-films-all-time-2022",
        ]
        for link in fallback_candidates:
            try:
                sub_html = fetch_bfi_html(link)
            except Exception:
                sub_html = ""
            got = parse_bfi_titles(sub_html) if sub_html else []
            if not got:
                try:
                    sub_amp = link.rstrip("/") + "/amp"
                    got = parse_bfi_titles(fetch_bfi_html(sub_amp))
                except Exception:
                    got = []
            if got:
                existing = {(s.get("title") or "", s.get("year") or "") for s in seeds}
                for g in got:
                    k = (g.get("title") or "", g.get("year") or "")
                    if k not in existing:
                        seeds.append(g)
                break  # stop at first working fallback

    # Final notice if still nothing
    if not seeds:
        print("[WARN] BFI scraper: found 0 titles for:", url)
        try:
            snippet = (html or "")[:600]
            print("[WARN] First 600 chars of HTML:")
            print(snippet)
        except Exception:
            pass

    return seeds

def hydrate_from_bfi(sess: requests.Session, url: str, omdb_api_key: Optional[str]) -> List[Dict[str, Any]]:
    seeds = scrape_bfi_sight_and_sound(url)
    results: List[Dict[str, Any]] = []
    seen: set = set()

    for s in seeds:
        title = s.get("title") or ""
        year = s.get("year") or ""
        if not title:
            continue

        tmdb_id = tmdb_search_movie(sess, title, year)
        if tmdb_id:
            core = get_movie_details_and_credits(sess, tmdb_id)
            if not core.get("imdb_id"):
                ext = tmdb_external_ids(sess, tmdb_id)
                if ext.get("imdb_id"):
                    core["imdb_id"] = ext["imdb_id"]
        else:
            core = {
                "title": title,
                "year": year,
                "director": "",
                "genre_tags": [],
                "plot_summary": "",
                "visual_style": "",
                "imdb_id": None,
                "tmdb_id": None,
            }
        core["critic_reviews"], core["user_reviews"] = [], []
        core = enrich_with_omdb(core, omdb_api_key)
        uniq = core.get("imdb_id") or (f"tmdb:{core.get('tmdb_id')}" if core.get("tmdb_id") else f"title:{title}|year:{year}")
        if uniq in seen:
            continue
        seen.add(uniq)
        if core.get("title"):
            results.append(map_to_schema(core))
        time.sleep(0.2)
    return results


# --- Letterboxd list scraping helpers (no extra deps) ---
LBOX_BASE = "https://letterboxd.com"


def fetch_letterboxd_html(url: str) -> str:
    """Fetch HTML from Letterboxd with basic headers and retries."""
    ua_pool = [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
            "Gecko/20100101 Firefox/125.0"
        ),
    ]
    last_err: Optional[Exception] = None
    for ua in ua_pool:
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
            "Connection": "close",
            "Referer": LBOX_BASE,
        }
        try:
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code >= 400:
                r.raise_for_status()
            text = r.text
            if "captcha" in text.lower():
                raise RuntimeError("Blocked by anti-bot")
            return text
        except Exception as e:
            last_err = e
            time.sleep(0.6)
    if last_err:
        raise last_err
    raise RuntimeError("Unexpected fetch_letterboxd_html error")


def parse_letterboxd_titles(html: str) -> List[Dict[str, str]]:
    """Extract film titles and years from a Letterboxd list page."""
    results: List[Dict[str, str]] = []
    if not html:
        return results

    # Main pattern: <div class="film-poster" data-film-name="Vertigo" data-film-year="1958" ...>
    for m in _re.finditer(r'<div[^>]*class="[^\"]*film-poster[^\"]*"[^>]*>', html, flags=_re.I):
        tag = m.group(0)
        name_m = _re.search(r'data-film-name="([^"]+)"', tag)
        year_m = _re.search(r'data-film-year="(\d{4})"', tag)
        if name_m:
            title = name_m.group(1).strip()
            year = year_m.group(1) if year_m else ""
            if title:
                results.append({"title": title, "year": year})

    # Fallback: poster img alt="Title (Year)"
    if not results:
        for im in _re.finditer(r'<img[^>]+alt="([^"]+)"', html, flags=_re.I):
            alt = im.group(1)
            m = _re.match(r"(.+?)\s*\((19\d{2}|20[0-2]\d)\)$", alt)
            if m:
                title = m.group(1).strip()
                year = m.group(2)
                results.append({"title": title, "year": year})
            else:
                if 2 <= len(alt) <= 200 and not any(x in alt.lower() for x in ["letterboxd", "watchlist", "poster", "list"]):
                    results.append({"title": alt.strip(), "year": ""})

    # Deduplicate by (title, year)
    uniq: List[Dict[str, str]] = []
    seen = set()
    for r in results:
        key = (r.get("title") or "", r.get("year") or "")
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq


def scrape_letterboxd_list(url: str) -> List[Dict[str, str]]:
    """Fetch the Letterboxd list and follow pagination `/page/2/`, `/page/3/`, ... until empty."""
    if not url.endswith('/'):
        url = url + '/'

    seeds: List[Dict[str, str]] = []

    def fetch_and_parse(u: str) -> List[Dict[str, str]]:
        try:
            return parse_letterboxd_titles(fetch_letterboxd_html(u))
        except Exception:
            return []

    seeds.extend(fetch_and_parse(url))

    page = 2
    while True:
        paged = url.rstrip('/') + f"/page/{page}/"
        got = fetch_and_parse(paged)
        if not got:
            break
        existing = {(s.get("title") or "", s.get("year") or "") for s in seeds}
        added = 0
        for g in got:
            k = (g.get("title") or "", g.get("year") or "")
            if k not in existing:
                seeds.append(g)
                added += 1
        if added == 0:
            break
        page += 1
        time.sleep(0.2)

    if not seeds:
        print("[WARN] Letterboxd scraper: found 0 titles for:", url)
    return seeds


def hydrate_from_letterboxd(sess: requests.Session, url: str, omdb_api_key: Optional[str]) -> List[Dict[str, Any]]:
    seeds = scrape_letterboxd_list(url)
    results: List[Dict[str, Any]] = []
    seen: set = set()

    for s in seeds:
        title = s.get("title") or ""
        year = s.get("year") or ""
        if not title:
            continue
        tmdb_id = tmdb_search_movie(sess, title, year)
        uniq = f"tmdb:{tmdb_id}" if tmdb_id else f"title:{title.lower()}:{year}"
        if uniq in seen:
            continue
        seen.add(uniq)

        if tmdb_id:
            core = get_movie_details_and_credits(sess, tmdb_id)
            if not core.get("imdb_id"):
                ext = tmdb_external_ids(sess, tmdb_id)
                if ext.get("imdb_id"):
                    core["imdb_id"] = ext["imdb_id"]
        else:
            core = {
                "id": None,
                "title": title,
                "year": year,
                "release_date": f"{year}-01-01" if year else None,
                "imdb_id": None,
                "genres": [],
                "genre_tags": [],
                "credits": {"cast": [], "crew": []},
                "critic_reviews": [],
                "user_reviews": [],
                "tmdb_id": None,
                "plot_summary": "",
                "visual_style": "",
                "director": "",
            }
        core["critic_reviews"] = []
        core["user_reviews"] = []
        core = enrich_with_omdb(core, omdb_api_key)
        results.append(map_to_schema(core))
        time.sleep(0.2)

    return results


# Minimal implementations to avoid unresolved references for other modes

def hydrate_from_tmdb_list(sess: requests.Session, list_id: str, omdb_api_key: Optional[str]) -> List[Dict[str, Any]]:
    items = fetch_tmdb_list(sess, list_id)
    results: List[Dict[str, Any]] = []
    seen: set = set()
    for it in items:
        tmdb_id = it.get("id")
        if not tmdb_id:
            continue
        core = get_movie_details_and_credits(sess, tmdb_id)
        uniq = core.get("imdb_id") or f"tmdb:{tmdb_id}"
        if uniq in seen:
            continue
        seen.add(uniq)
        core["critic_reviews"] = []
        core["user_reviews"] = []
        core = enrich_with_omdb(core, omdb_api_key)
        results.append(map_to_schema(core))
        time.sleep(0.2)
    return results


def hydrate_from_csv(sess: requests.Session, csv_path: str, omdb_api_key: Optional[str]) -> List[Dict[str, Any]]:
    seeds = load_seeds_csv(csv_path)
    results: List[Dict[str, Any]] = []
    seen: set = set()
    for s in seeds:
        title = (s.get("title") or "").strip()
        year = (s.get("year") or "").strip()
        tmdb_id: Optional[int] = None
        if (s.get("tmdb_id") or "").strip().isdigit():
            tmdb_id = int(s.get("tmdb_id") or 0)
        if not tmdb_id and title:
            tmdb_id = tmdb_search_movie(sess, title, year)
        if tmdb_id:
            core = get_movie_details_and_credits(sess, tmdb_id)
            if not core.get("imdb_id"):
                ext = tmdb_external_ids(sess, tmdb_id)
                if ext.get("imdb_id"):
                    core["imdb_id"] = ext["imdb_id"]
        else:
            if not title:
                continue
            core = {
                "title": title,
                "year": year,
                "director": "",
                "genre_tags": [],
                "plot_summary": "",
                "visual_style": "",
                "imdb_id": s.get("imdb_id") or None,
                "tmdb_id": None,
            }
        core["critic_reviews"], core["user_reviews"] = [], []
        core = enrich_with_omdb(core, omdb_api_key)
        uniq = core.get("imdb_id") or (f"tmdb:{core.get('tmdb_id')}" if core.get("tmdb_id") else f"title:{title}|year:{year}")
        if uniq in seen:
            continue
        seen.add(uniq)
        if core.get("title"):
            results.append(map_to_schema(core))
        time.sleep(0.15)
    return results


if __name__ == "__main__":
    main()
