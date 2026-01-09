# Trial-11T Blocker Report — OKX history-trades does not provide 2021–2022 trades — 2026-01-09

Source: programmer report (Quant).

## Observed facts

- OKX `history-trades` endpoint returns only **recent** trades.
- When requesting BTC 2021–2022, returned trades have timestamps around 2025-06-08, so all are filtered out by the 2022 window filter.
- Conclusion: OKX does not provide the required long-horizon historical trades via this endpoint (at least not beyond recent days/weeks).

## Implication

Trial-11T (trade-derived quotes for BTC 2021–2022 replay) is **NOT_MEASURABLE** under the current data availability constraints.

