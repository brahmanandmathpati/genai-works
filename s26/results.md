# Session 26 - my migration results

Target: Qdrant server at http://localhost:6333

## Same results? (YOUR overlap_at_k, top 3)

| question | overlap |
|---|---|
| how long do refunds take | 1.00 |
| my parcel arrived broken | 1.00 |
| can I pay cash on delivery | 1.00 |
| change my delivery address | 1.00 |
| is there a warranty on headphones | 1.00 |

## Multi-tenancy (YOUR tenant_filter)

Asha's search returned: ['CUST-1001', 'CUST-1001', 'CUST-1001'] -> SAFE

## My store choices

- **hospital_onprem**: pgvector - Patient data must stay in-house and the IT team already runs PostgreSQL, so pgvector adds no new system to secure.
- **startup_no_ops**: pinecone - With no ops engineer, a fully managed service with pay-as-you-grow pricing means nobody has to run or patch servers.
- **ecommerce_scale**: qdrant - At 50 million vectors with heavy brand and price filtering, Qdrant's payload filtering and quantization suit a team that runs its own servers.
