# 일본 중고 명품 마켓 — 크로스샵 비교（Komehyo+Jackroad）

**일본 최대 리유즈 백화점 코메효(루이비통/샤넬/에르메스/롤렉스 등)와 잭로드 명품 시계를 크로스샵 비교.**

> 🇯🇵 English/日本語版: [Japan Market](https://apify.com/fruitful_quintessence)

## Input

| Field | Type | Default | Description |
|---|---|---|---|
| `searchKeyword` | string | `ルイヴィトン` | 검색 키워드 |
| `maxItems` | integer | 100 | 최대 수집 개수 |
| `maxPages` | integer | 2 | 소스별 최대 페이지 수 |
| `sources` | string | `komehyo,jackroad` | 데이터 소스（쉼표 구분） |
| `proxyConfiguration` | object | — | Apify proxy |

## Output Sample

```json
{
  "productId": "230-000-742-0039",
  "title": "【未使用品】エルメス ガーデン パーティ 30cm 051568CK バッグ",
  "brand": "HERMES",
  "price": 1100000,
  "referencePrice": 694100,
  "rank": "未使用品",
  "store": "名古屋本館",
  "imageUrl": "https://img.komehyo.jp/contents/images/goods/9ff/2300007420039_1_icon.jpg",
  "productUrl": "https://komehyo.jp/product/230-000-742-0039/",
  "category": "バッグ",
  "source": "komehyo",
  "shop": "Komehyo",
  "scrapedAt": "2026-08-10T10:00:00Z"
}
```

## Use Cases

- 직구/되팔기: 저가 상품 발견 → 마진 확보
- 시세 조사: 특정 모델의 시장 가격 추이 추적
- 재고 모니터링: 매장 재고 변화 감시

## Pricing

이벤트당 과금 — $0.00005/실행 + **$0.002/건**

## Data Source

공개 상품 정보(명칭, 가격, 브랜드, 재고 상태)만 수집합니다.
