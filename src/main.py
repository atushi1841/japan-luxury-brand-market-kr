import asyncio
import datetime
import json
import sys
import unicodedata

import httpx

try:
    from apify import Actor
except Exception:
    Actor = None


def _norm_key(text):
    return unicodedata.normalize("NFC", str(text or "")).casefold()


async def run(actor_input, actor=None):
    search_keyword = actor_input.get("searchKeyword") or ""
    max_items = int(actor_input.get("maxItems", 100))
    max_pages = int(actor_input.get("maxPages", 2))
    sources = [s.strip() for s in actor_input.get("sources", "komehyo,jackroad").split(",") if s.strip()]

    stats_mode = actor_input.get("statsMode", False)
    collected_items = []

    proxy_url = None
    if actor is not None:
        proxy_config = await actor.create_proxy_configuration(actor_proxy_input=actor_input.get("proxyConfiguration"))
        if proxy_config:
            proxy_url = await proxy_config.new_url()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "ja-JP,ja;q=0.9",
    }

    async with httpx.AsyncClient(proxy=proxy_url, headers=headers, timeout=30.0, follow_redirects=True) as client:
        collected = 0
        for src in sources:
            if collected >= max_items:
                break
            remaining = max_items - collected
            items = []
            if src == "komehyo":
                from sources.komehyo import fetch_komehyo_categories
                items = await fetch_komehyo_categories(client, headers, keyword=search_keyword,
                                                       max_pages=max_pages, max_items=remaining)
            elif src == "jackroad":
                if not search_keyword:
                    continue  # ジャックロードはキーワード必須
                from sources.jackroad import fetch_jackroad
                items = await fetch_jackroad(client, keyword=search_keyword, max_pages=max_pages, max_items=remaining)

            for item in items:
                if stats_mode:
                    collected_items.append(item)
                else:
                    if actor is not None:
                        await actor.push_data(item)
                    else:
                        print(json.dumps(item, ensure_ascii=False))
                collected += 1
                if collected >= max_items:
                    break

    if stats_mode:
        stats_keyword = actor_input.get("statsKeyword") or ""
        if stats_keyword:
            nk = _norm_key(stats_keyword)
            filtered_items = []
            for item in collected_items:
                title = str(item.get("title", ""))
                if nk in _norm_key(title):
                    filtered_items.append(item)
        else:
            filtered_items = collected_items

        prices = []
        for item in filtered_items:
            price = item.get("price")
            if price is None:
                continue
            try:
                price = int(price)
            except (ValueError, TypeError):
                try:
                    price = int(str(price).replace(",", "").replace("円", "").strip())
                except Exception:
                    continue
            if price > 0:
                prices.append(price)

        count = len(filtered_items)
        if prices:
            price_min = min(prices)
            price_max = max(prices)
            price_avg = sum(prices) // len(prices)
            sorted_prices = sorted(prices)
            n = len(sorted_prices)
            if n % 2 == 1:
                price_median = sorted_prices[n // 2]
            else:
                price_median = (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) // 2
        else:
            price_min = price_max = price_avg = price_median = 0

        sample_items = []
        for item in filtered_items[:3]:
            sample_items.append({
                "title": item.get("title", ""),
                "price": item.get("price"),
                "detailUrl": item.get("detailUrl") or item.get("url", ""),
                "shop": item.get("shop", ""),
            })

        stats_result = {
            "statsType": "japan-luxury-brand-price-kr",
            "keyword": stats_keyword or search_keyword,
            "count": count,
            "priceMin": price_min,
            "priceMax": price_max,
            "priceAvg": price_avg,
            "priceMedian": price_median,
            "sampleItems": sample_items,
            "collectedAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if actor is not None:
            await actor.push_data(stats_result)
        else:
            print(json.dumps(stats_result, ensure_ascii=False))
        return


async def main():
    if Actor is not None:
        async with Actor:
            actor_input = await Actor.get_input() or {}
            await run(actor_input, actor=Actor)
    else:
        raw = sys.stdin.read() or ""
        try:
            actor_input = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            actor_input = {}
        await run(actor_input, actor=None)


if __name__ == "__main__":
    asyncio.run(main())
