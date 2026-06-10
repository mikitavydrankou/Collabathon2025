# docs/img

Screenshots referenced by the root README.

## grafana-overview.png — capture it

With the kind cluster up:

```bash
bash deploy/cluster.sh pf        # port-forwards Grafana to http://localhost:3001
bash deploy/cluster.sh creds     # prints login (admin / admin)
```

Open <http://localhost:3001>, go to **Dashboards → EasyFocus — Overview**
(uid `easyfocus-overview`), set the range to a window with traffic
(`bash deploy/loadtest.sh` generates some), then save a screenshot here as
`grafana-overview.png`.

Finally uncomment the image line in the root `README.md` (Observability section).
```
