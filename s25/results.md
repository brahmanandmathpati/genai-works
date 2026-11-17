# Session 25 - my vector database results

## Filtered search (YOUR build_where)

| question | filter | top results | all match the filter? |
|---|---|---|---|
| how long do refunds take | `{'category': 'payments'}` | refunds (20260618), refunds (20260618), payments (20260930) | yes |
| change my delivery address | `{'updated': {'$gte': 20260101}}` | account-and-addresses (20260215), account-and-addresses (20260215), account-and-addresses (20260215) | yes |
| my parcel arrived broken | `{'$and': [{'category': 'returns'}, {'updated': {'$gte': 20260601}}]}` | damaged-items (20260709), damaged-items (20260709), damaged-items (20260709) | yes |
| will my money come back to my card if I return something | `{'$and': [{'category': 'returns'}, {'updated': {'$gte': 20260101}}]}` | returns (20261001), returns (20261001), returns (20261001) | yes |
| is there a fee when I pay with a card | `{'category': 'payments'}` | payments (20260930), payments (20260930), payments (20260930) | yes |

## Speed vs accuracy (YOUR recall_at_k)

| setting | recall@10 | ms/query |
|---|---|---|
| fast | 0.78 | 0.16 |
| default | 1.00 | 0.36 |
| accurate | 1.00 | 1.54 |
