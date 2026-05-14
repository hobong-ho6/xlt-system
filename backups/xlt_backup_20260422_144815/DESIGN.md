# Unifi Design System — Look & Feel Guide

> 파생 프로젝트에서 Unifi의 룩&필을 유지하기 위한 디자인 토큰 및 패턴 가이드

---

## Colors

### Brand

| Token | Value | Usage |
|-------|-------|-------|
| `--primary-color` | `#beff80` | 주요 CTA, 강조 |
| `--secondary-color` | `#fd184f` | 보조 강조 (TBD) |

### Semantic

| Token | Value | Usage |
|-------|-------|-------|
| `--text-green-color` / `--shape-green-color` | `#06c755` | 성공, 긍정 |
| `--text-red-color` / `--shape-red-color` | `#fd184f` | 에러, 위험 |
| `--text-blue-color` / `--shape-blue-color` | `#2f75f3` | 정보, 링크 |

### Text (6단계)

| Token | Value | Usage |
|-------|-------|-------|
| `--text-1-color` | `#000` | 제목, 강조 텍스트 |
| `--text-2-color` | `#444649` | 본문 텍스트 |
| `--text-3-color` | `#787c82` | 보조 텍스트 |
| `--text-4-color` | `#94979d` | 비활성 텍스트 |
| `--text-5-color` | `#b5b8be` | 플레이스홀더 |
| `--text-6-color` | `#fff` | 반전 텍스트 |

### Shape (6단계)

| Token | Value | Usage |
|-------|-------|-------|
| `--shape-1-color` | `#202020` | 가장 어두운 배경/버튼 |
| `--shape-2-color` | `#b5b8be` | 비활성 요소 |
| `--shape-3-color` | `#d1d5dc` | 구분선, 보더 |
| `--shape-4-color` | `#f1f2f6` | 약한 배경 (muted 버튼) |
| `--shape-5-color` | `#f6f7fa` | 카드/박스 기본 배경 |
| `--shape-6-color` | `#fff` | 흰색 배경 |
| `--shape-line-color` | `#efefef` | 라인/디바이더 |

### Base

| Token | Value | Usage |
|-------|-------|-------|
| `--text-color` | `#000` | 기본 텍스트 |
| `--bg-color` | `#fff` | 기본 배경 |

---

## Typography

### Font Family

```css
font-family: -apple-system, BlinkMacSystemFont, 'Malgun Gothic', '맑은 고딕', helvetica,
  'Apple SD Gothic Neo', sans-serif;
```

### Font Size Scale

| Size | Pixel | Usage |
|------|-------|-------|
| xs | 10px | 하단 네비게이션 라벨 |
| sm | 11px | 캡션, 보조 정보 |
| body-sm | 12px | 작은 버튼, 태그, 뱃지 |
| body | 13px | 중간 버튼, 기본 본문 |
| body-lg | 14px | **가장 많이 사용**, 리스트 항목, 설명 |
| md | 15px | 강조 본문 |
| lg | 16px | 큰 버튼, 중제목 |
| xl | 18px | 헤더 타이틀 |
| 2xl | 20px | 섹션 제목 |
| 3xl | 22px | 페이지 제목 |
| 4xl | 26px | 대형 제목 |
| 5xl | 28~32px | 히어로, 금액 표시 |

### Font Weight

| Weight | Value | Usage |
|--------|-------|-------|
| regular | 400 | 본문, 설명 |
| medium | 500 | 약간 강조 (드물게 사용) |
| semibold | 600 | 중간 강조 (드물게 사용) |
| bold | 700 | **가장 많이 사용**, 제목, 버튼, 강조 |
| extrabold | 800 | 특수 강조 |

### Line Height

```css
line-height: 1.2; /* 기본 (body에 설정) */
```

---

## Spacing

### Base Unit: 4px

코드 분석 기반 주요 간격 값:

| Token | Value | Usage |
|-------|-------|-------|
| space-1 | 2px | 미세 간격 |
| space-2 | 3px | 아이콘-텍스트 간격 |
| space-3 | 4px | 인라인 요소 간격 |
| space-4 | 6px | 작은 내부 간격 |
| space-5 | 8px | 요소 간 기본 간격 |
| space-6 | 10px | 섹션 내 간격 |
| space-7 | 12px | **가장 많이 사용**, 카드 내부, 리스트 간격 |
| space-8 | 16px | 섹션 간 간격 |
| space-9 | 20px | **페이지 좌우 패딩 표준** |
| space-10 | 24px | 큰 섹션 패딩 |

### Page Layout

```css
padding: 0 20px;  /* 페이지 좌우 기본 패딩 */
padding: 20px;    /* 카드/섹션 내부 패딩 */
gap: 12px;        /* 리스트 항목 간격 (가장 빈번) */
```

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| radius-xs | 4px | 태그, 뱃지 |
| radius-sm | 8px | 작은 카드, 입력 필드 |
| radius-md | 10px | xsmall 박스 |
| radius-base | 12px | **버튼 기본**, small 박스 |
| radius-lg | 14px | 중간 카드 |
| radius-xl | 16px | **medium/large 박스** |
| radius-2xl | 20px | xlarge 박스 |
| radius-full | 999px | **가장 많이 사용**, 필(pill) 버튼, 칩 |

---

## Z-Index

| Token | Value | Usage |
|-------|-------|-------|
| `--component-layer-z-index` | 10 | 컴포넌트 내부 레이어 |
| `--page-layer-z-index` | 100 | 페이지 레벨 오버레이 |
| `--app-layer-z-index` | 1000 | 앱 레벨 (모달, 바텀시트) |
| `--external-layer-z-index` | 2000 | 외부 레이어 (토스트) |

---

## Component Patterns

### Button

**Sizes:**

| Size | Height | Padding | Font Size |
|------|--------|---------|-----------|
| xsmall | 24px | 3px 8px | 12px |
| small | 32px | 9px 14px | 12px |
| medium | 42px | 10px 24px | 13px |
| large | 50px | 12px 30px | 16px |
| xlarge | 52px | 15px 40px | 16px |

**Colors:** default, primary(`#beff80`), secondary(`#fd184f`), muted, transparent, red, green, blue, white

**Variants:** contained(기본), outlined, text

**Round:** `border-radius: 999px` (pill 형태)

**Disabled:** opacity 0.333 적용 (`rgb(from ... r g b / 0.333)`)

### Box

**Sizes:**

| Size | Padding | Border Radius |
|------|---------|---------------|
| xsmall | 11px 18px | 10px |
| small | 12px 20px | 12px |
| medium | 15px 20px | 16px |
| large | 22px | 16px |
| xlarge | — | 20px |

**Colors:** default(`--shape-5-color`), primary, red, blue, green, white, black

**Variants:** contained, outlined

---

## Safe Area

```css
--safe-area-inset-top: var(--android-safe-area-inset-top, env(safe-area-inset-top, 0px));
--safe-area-inset-bottom: var(--android-safe-area-inset-bottom, env(safe-area-inset-bottom, 0px));
```

모바일 웹 환경에서 노치/홈바 영역 대응.

---

## Quick Reference (CSS Variables)

파생 프로젝트에서 아래 변수를 `:root`에 복사하면 Unifi 룩&필 적용 가능:

```css
:root {
  /* Brand */
  --primary-color: #beff80;
  --secondary-color: #fd184f;

  /* Text (6-step) */
  --text-color: #000;
  --text-1-color: #000;
  --text-2-color: #444649;
  --text-3-color: #787c82;
  --text-4-color: #94979d;
  --text-5-color: #b5b8be;
  --text-6-color: #fff;

  /* Semantic */
  --text-green-color: #06c755;
  --text-red-color: #fd184f;
  --text-blue-color: #2f75f3;

  /* Shape (6-step) */
  --shape-1-color: #202020;
  --shape-2-color: #b5b8be;
  --shape-3-color: #d1d5dc;
  --shape-4-color: #f1f2f6;
  --shape-5-color: #f6f7fa;
  --shape-6-color: #fff;
  --shape-line-color: #efefef;
  --shape-green-color: #06c755;
  --shape-red-color: #fd184f;
  --shape-blue-color: #2f75f3;

  /* Background */
  --bg-color: #fff;

  /* Z-Index */
  --component-layer-z-index: 10;
  --page-layer-z-index: 100;
  --app-layer-z-index: 1000;
  --external-layer-z-index: 2000;
}
```
