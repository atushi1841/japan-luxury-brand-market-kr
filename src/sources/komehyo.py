import asyncio
import random
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

import httpx

BASE_URL = "https://komehyo.jp/"

# カテゴリページ（横断対象）
CATEGORIES = {
    "バッグ": "/brandbag/",
    "財布・アクセサリー": "/brandwallet-accessories/",
    "ジュエリー": "/brandjewelry/",
    "時計": "/brandwatch/",
}

# 商品カードの <a> を抽出。商品IDはハイフン区切り(例: 260-008-023-3589)
CARD_RE = re.compile(
    r'<a\b(?=[^>]*\bclass=["\'][^\'"]*p-link--card[^\'"]*["\'])(?=[^>]*\bhref="/product/([\d-]+)/")[^>]*>'
)

FIELD_CLASSES = {
    "title": "p-link__txt--productsname",
    "brand": "p-link__txt--brand",
    "size": "p-link__txt--size",
    "rank": "p-link__txt--rank",
    "material": "p-link__txt--material",
    "store": "p-link__txt--store",
    "reference": "p-link__txt--reference",
    "price": "p-link__txt--price",
}


def extract_text(segment, class_name):
    pattern = (
        r'<span[^>]*class=["\'][^\'"]*\b'
        + re.escape(class_name)
        + r'\b[^\'"]*["\'][^>]*>(.*?)</span>'
    )
    match = re.search(pattern, segment, re.S)
    if not match:
        return None
    text = re.sub(r'<[^>]+>', '', match.group(1))
    text = (
        text.replace('&nbsp;', ' ')
        .replace('&yen;', '¥')
        .replace('&amp;', '&')
        .replace('&#39;', "'")
        .replace('&quot;', '"')
    )
    return re.sub(r'\s+', ' ', text).strip() or None


def extract_rating(segment, class_name):
    parent = extract_text(segment, class_name)
    if not parent:
        return None
    for prefix in ["ランク：", "サイズ：", "素材：", "在庫店舗：", "ランク:", "サイズ:", "素材:", "在庫店舗:"]:
        if parent.startswith(prefix):
            return parent[len(prefix):].strip()
    return parent


def extract_image_url(segment):
    match = re.search(r'<img[^>]+src="([^"]+)"', segment)
    if not match:
        match = re.search(r'<img[^>]+data-src="([^"]+)"', segment)
    if match:
        return urljoin(BASE_URL, match.group(1))
    return None


def parse_price(text):
    if not text:
        return None
    clean = (
        text.replace('￥', '').replace('¥', '').replace('円', '')
        .replace('税込', '').replace('参考上代', '').replace(':', '').replace('：', '')
    )
    match = re.search(r'\d[\d,]*', clean)
    if not match:
        return None
    return int(match.group(0).replace(',', ''))


def iter_product_cards(html):
    for match in CARD_RE.finditer(html):
        product_id = match.group(1)
        start = match.end()
        end = html.find('</a>', start)
        if end == -1:
            end = len(html)
        yield html[start:end], product_id


def make_item(segment, product_id, category_label):
    fields = {key: extract_text(segment, class_name) for key, class_name in FIELD_CLASSES.items()}
    item = {
        "productId": str(product_id),
        "title": fields["title"],
        "brand": fields["brand"],
        "price": parse_price(fields["price"]),
        "referencePrice": parse_price(fields["reference"]),
        "rank": extract_rating(segment, "p-link__txt--rank"),
        "size": extract_rating(segment, "p-link__txt--size"),
        "material": extract_rating(segment, "p-link__txt--material"),
        "store": extract_rating(segment, "p-link__txt--store"),
        "imageUrl": extract_image_url(segment),
        "productUrl": f"{BASE_URL}product/{product_id}/",
        "category": category_label,
        "source": "komehyo",
        "shop": "Komehyo",
        "condition": extract_rating(segment, "p-link__txt--rank"),
        "scrapedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if not item["title"]:
        return None
    return item


async def fetch_page(client, url, headers):
    for attempt in range(3):
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.text
        except httpx.HTTPError:
            pass
        await asyncio.sleep(min(2 ** attempt, 8) + random.uniform(0, 1))
    return None


async def fetch_komehyo_categories(client, headers, keyword="", max_pages=2, max_items=100):
    results = []
    for label, path in CATEGORIES.items():
        if len(results) >= max_items:
            break
        page = 1
        while page <= max_pages and len(results) < max_items:
            url = f"{BASE_URL.rstrip('/')}{path}?q=&page={page}"
            html = await fetch_page(client, url, headers)
            if not html:
                break
            cards = list(iter_product_cards(html))
            if not cards:
                break
            for segment, product_id in cards:
                item = make_item(segment, product_id, label)
                if not item:
                    continue
                if keyword and keyword.lower() not in (item["title"] or "").lower() and keyword.lower() not in (item["brand"] or "").lower():
                    continue
                results.append(item)
                if len(results) >= max_items:
                    break
            if len(cards) < 50:
                break
            page += 1
            await asyncio.sleep(random.uniform(1.0, 2.0))
    return results[:max_items]
