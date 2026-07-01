# AI Cultural Recommender — End-to-End Execution Plan

A professional, executable blueprint for building, deploying, and operating the Egypt Cultural Recommender system: from your existing dataset to a live, bookable product.

---

## 1. Project scope and success criteria

**What the system does:** given a user's interests, available time, budget, and crowd tolerance, it recommends a ranked, time-sequenced itinerary of Egyptian cultural and historical sites, generates narrative content for each stop, estimates how crowded each site will be at the planned visit time, and books entry tickets through a conversational agent.

**Definition of done for v1:**
- A user can complete the full loop — input preferences, get a ranked itinerary with stories, see a crowd estimate, and confirm a mock or real booking — in under 60 seconds end to end.
- The system runs as a deployed web app with a working API, not just a local script.
- All recommendations are grounded in your actual dataset (1,258 places, 166 priced sites), not hallucinated by the LLM.

---

## 2. Data layer (you already have this)

| Asset | Rows | Role in pipeline |
|---|---|---|
| `egypt_places_{ar,en}.csv` | 1,258 | Source of truth for what places exist, where, and what they are |
| `ticket_prices_{ar,en}.csv` | 166 | Source of truth for entry cost by visitor type |

**What's still needed before build starts:**

1. **Load into a real database**, not CSVs in memory. Flat files don't scale past a demo and can't support concurrent users or filtering at query time.
2. **Generate embeddings for every place** — a 384–1024 dimension vector per place computed from its name + description + category, used for semantic retrieval ("ancient sites with dramatic stories" should match Abu Simbel even if the user never types "Abu Simbel").
3. **Join the two datasets** on a normalized site name so each place row optionally carries its 4-tier pricing inline — this removes a runtime lookup and keeps the Booking Agent fast.
4. **Add a `crowd_profile` field per place** — even a simple static structure (default crowd level, peak hours, peak season) is enough to start; this is what the Crowd Estimator reads and adjusts.

---

## 3. The agent pipeline — model choice per stage (demo build, zero LLM cost)

Since this is a demo, not a production deployment, every model in the pipeline runs on Hugging Face's free tier — no Anthropic API spend at all. This trades some reliability and writing polish for being genuinely free end to end, which is the right call for a graduation defense you fully control.

| Stage | Task | Model | Why this model |
|---|---|---|---|
| Preference Agent | Parse free-text or form input into structured filters | **Qwen2.5-7B-Instruct** (HF Inference API free tier, or a free HF Space) | Strong instruction-following at 7B, handles both Arabic and English input well, structured extraction is forgiving of small model imperfections |
| Retrieval | Find candidate places matching filters | **No LLM** — embedding similarity search (vector DB) + SQL filters | Retrieval should be deterministic and fast regardless of model budget |
| Crowd Estimator | Score predicted crowd level per candidate | **No LLM** — rule engine | Free by construction, no model needed at all |
| Recommender Agent | Rank and select the final itinerary from candidates | **Qwen2.5-7B-Instruct** or **Llama-3.1-8B-Instruct** | Reasoning over a 15-20 item shortlist with explicit JSON output — well within a 7-8B model's ability when you give it a tight, structured prompt |
| Story Generator | Write the narrative for each selected place | **Qwen2.5-14B-Instruct** if your free Space/Inference quota allows it, otherwise **Qwen2.5-7B-Instruct** | This is the most quality-sensitive stage — push to the largest free model you can reliably run here, since narrative writing is where smaller models show the most weakness |
| Booking Agent | Confirm slots, collect visitor details, finalize ticket | **Qwen2.5-7B-Instruct** with manual JSON-schema prompting (not native tool-calling) | Open-source 7B models are noticeably less reliable at native function-calling than Claude; sidestep this by prompting for a strict JSON response and validating/retrying in code rather than relying on a tool-use API |

### Why Qwen over Llama as the primary choice

Both are free and self-hostable, but **Qwen2.5** has meaningfully stronger Arabic generation quality out of the box, which matters across nearly every stage of your pipeline given the bilingual dataset — Llama's Arabic is noticeably weaker unless you find an Arabic-finetuned variant. Use Qwen2.5 as your default and only reach for Llama-3.1-8B as a fallback or comparison point if you want to show evaluation of multiple open models in your thesis (which is actually a nice thing to include — "we benchmarked Qwen2.5 vs Llama-3.1 on Arabic story quality and picked Qwen" is a strong, defensible methodology section).

### Handling the known weak points of free open-source models

1. **JSON reliability.** Open 7B models occasionally emit malformed JSON or wrap it in extra text. Always parse defensively: strip markdown fences, use a JSON-repair library (`json_repair` on PyPI is free and handles most malformed LLM output), and retry once with a "fix this JSON" follow-up prompt if parsing fails.
2. **No native tool-calling.** Instead of relying on function-calling APIs (which Qwen/Llama support inconsistently depending on the serving backend), prompt for a structured JSON action object — e.g. `{"action": "check_availability", "site": "...", "date": "..."}` — and dispatch it yourself in Python. More code, but fully reliable and free.
3. **Inference speed on free tiers.** HF's free Inference API and free Spaces (CPU, or ZeroGPU with queueing) are slower than a paid API — expect a few seconds to 20+ seconds per call depending on model size and current load. For a demo, this is manageable if you set expectations (a visible "thinking" state in the UI) and pre-warm the Space a few minutes before presenting, since cold starts on free Spaces are the main risk.
4. **Caching everything during development.** Cache every prompt → response pair locally while building, so repeated test runs don't re-hit the free Space and risk rate limits right before your defense.

### Serving the models — two free options

- **HF Inference API (serverless, free tier):** simplest to call from your FastAPI backend with the `huggingface_hub` Python client, no infrastructure to manage, but rate-limited and can be slow/cold under free tier.
- **Your own HF Space running a small inference server (e.g. `text-generation-inference` or a simple FastAPI + `transformers` wrapper) on the free CPU or ZeroGPU tier:** more setup work, but gives you a stable endpoint you control and can pre-warm before a live demo — recommended if you want predictable latency during your defense rather than relying on the shared public Inference API queue.

---

## 4. Crowd estimation — concrete approach

Building on what we discussed earlier, ship this in two phases:

**Phase 1 (v1, no ML):** a deterministic scoring function combining:
- Static base crowd level per site (you assign this once per place — major sites like Giza or Karnak default to "high", smaller museums default to "low")
- Time-of-day multiplier (early morning and late afternoon reduce the score; midday increases it)
- Day-of-week multiplier (Friday/Saturday increase it for tourist-heavy sites)
- Season multiplier (Oct–Apr tourist season increases it; summer decreases it for outdoor desert sites, increases it for coastal sites)

This requires no training data and is fully explainable — important for a graduation defense, since you can show the exact formula.

**Phase 2 (post-v1, if time allows):** once the app has real usage, log actual visit confirmations with timestamps and train a small regression or gradient-boosted model (XGBoost/LightGBM) to predict crowd level from time + day + season + site, replacing the hand-tuned multipliers with learned weights. This is a strong "future work" section for your thesis even if you don't fully implement it.

---

## 5. Tech stack — 100% free tools, including the LLM layer

Every component below is free for a demo at this scale. Unlike the earlier version of this plan, there is **no paid line item at all** — the LLM layer now runs entirely on Hugging Face's free tier instead of the Anthropic API.

| Layer | Choice | Why it's free |
|---|---|---|
| Backend API | **FastAPI** (Python) | Open-source, self-hosted |
| Agent orchestration | **LangGraph** (or a hand-rolled state machine) | Open-source Python library |
| Relational DB | **PostgreSQL** | Open-source, self-hosted; or Supabase/Neon free tier |
| Vector DB | **pgvector** extension on the same Postgres instance | Open-source extension, no paid vector DB |
| Cache | **Redis** | Open-source, self-hosted; or Upstash free tier |
| Task queue | **Celery + Redis as broker** | Both open-source |
| Embeddings model | **`intfloat/multilingual-e5-base`** run locally or via a free HF Space | Free, unlimited, strong Arabic/English cross-lingual quality — run once offline on your 1,258 places |
| LLM (all agent stages) | **Qwen2.5-7B-Instruct** (and Qwen2.5-14B for story generation if quota allows), served via free HF Inference API or a self-hosted free HF Space | Zero cost — no API key billing, no Anthropic dependency for the demo build |
| Frontend | React or your existing HTML/JS prototype | Free to write |
| Payments | Simulated "Confirm Booking" step writing to your own bookings table | No real gateway needed for a demo |
| Notifications | Console/log output, or Gmail SMTP free quota / Resend free tier if you want real emails | No paid notification service |

### A note on mixing in Claude later

This plan is fully open-source for the demo phase. If you later want a "production" appendix in your thesis — common for graduation projects to include a brief "how this would scale" section — you can describe swapping the Story Generator specifically to Claude Sonnet as a quality upgrade path, without needing to actually pay for or implement it now. That gives you a strong discussion point in your defense ("we chose open models for cost control during development, and identified Claude as the upgrade path for production-grade narrative quality") without spending anything today.

### Free hosting (replaces the earlier Railway/AWS suggestion)

| Need | Free option |
|---|---|
| Backend + workers | **Render free tier** (spins down when idle, fine for a demo) or **Fly.io free allowance** |
| Postgres + pgvector | **Supabase free tier** (has pgvector built in) or **Neon free tier** |
| Redis | **Upstash free tier** |
| Frontend | **Vercel** or **Netlify** free tier |
| CI/CD | **GitHub Actions** — free for public repos and generous free minutes for private ones |
| Error tracking | **Sentry free tier** (5,000 errors/month, plenty for a project this size) |
| Uptime monitoring | **UptimeRobot free tier** |

---

## 6. Full pipeline, step by step

1. **User submits preferences** (interests, hours, budget, crowd tolerance, location) through the frontend.
2. **API gateway** authenticates the request and routes it to the orchestration layer.
3. **Preference Agent** (Qwen2.5-7B) normalizes the input into a structured filter object: `{interests: [...], max_budget, available_hours, crowd_tolerance, city}`.
4. **Retrieval step** queries pgvector for the top ~30 semantically relevant places, then filters by city, budget, and category using SQL — pure retrieval, no LLM.
5. **Crowd Estimator** scores each of the 30 candidates against the requested visit time using the rule engine, attaching a `predicted_crowd` field to each.
6. **Recommender Agent** (Qwen2.5-7B) receives the 30 scored candidates and selects + orders the final 3-5 stops, balancing interest match, budget, time, and crowd — returns structured JSON, parsed with `json_repair` to handle any malformed output.
7. **Story Generator** (Qwen2.5-14B, falling back to 7B if quota is tight) runs in parallel (via the task queue) for each selected place, generating the narrative. The frontend can show a loading state per card and stream stories in as they complete rather than blocking on all of them.
8. **Pricing lookup** joins each selected place against the ticket price table by visitor type (already solved in your dataset).
9. **Response returned** to the frontend: ranked itinerary, with story, price, and predicted crowd per stop.
10. **User initiates booking** for a stop — this opens a session handled by the **Booking Agent** (Qwen2.5-7B, prompted for structured JSON actions rather than native tool-calling), which checks slot availability (mocked against your own bookings table), collects visitor name and count, and confirms.
11. **Booking confirmed** → written to the bookings table → confirmation sent via email/WhatsApp → optional payment step through Paymob if you want real transactions for the demo.

---

## 7. Deployment plan

**Containerization:** package the FastAPI app and Celery workers as separate Docker containers defined in a single `docker-compose.yml` for local development. Docker itself is free and this also makes "how do I run this" trivial for your defense — `docker compose up` and it works.

**Hosting — entirely free tier:**
- **Render** (free web service tier, spins down after inactivity and wakes on the next request — acceptable for a defense demo, just mention this so a 10-15 second cold start during a live demo doesn't surprise anyone) or **Fly.io** (free allowance covers small always-on apps).
- **Supabase** for Postgres with pgvector pre-installed — free tier gives you 500MB which is far more than 1,258 rows of data needs.
- **Upstash** for Redis, free tier.
- **Vercel** or **Netlify** for the frontend — free, instant, no cold start issue since it's static.

**CI/CD:** GitHub Actions — free for the scope of a student project. On every push to `main`, run tests and trigger a deploy via Render/Vercel's GitHub integration. This is a strong thing to demo live during your defense and costs nothing.

**Domain:** you don't need a custom paid domain for a graduation defense — the free subdomains Render/Vercel provide (e.g. `yourproject.onrender.com`, `yourproject.vercel.app`) are completely fine to present.

**Environment separation:** even on free tiers, you can run a second free Render/Vercel deployment as "staging" at no cost — this still demonstrates the practice without needing paid infrastructure.

---

## 8. Evaluation and monitoring

This matters a lot for a graduation project defense — you need to be able to demonstrate the system works, not just show it running once.

| What to measure | How |
|---|---|
| Recommendation relevance | Manual evaluation set: 20-30 test queries with expected place categories, check overlap |
| Story quality | Rubric-based human evaluation (factual accuracy, engagement, length) on a sample of generated stories |
| Latency per pipeline stage | Log timestamps at each agent boundary; report p50/p95 end-to-end response time |
| LLM latency and reliability | Log response time and JSON-parse success rate per HF model call; report average and failure rate — this matters more than cost tracking now since speed/reliability is the actual constraint of the free tier |
| Crowd estimate sanity | Compare your rule-based predictions against publicly known peak times (e.g. everyone agrees Giza is worse at 10am Saturday than 7am Tuesday) as a qualitative check |
| System reliability | **Sentry free tier** (5,000 errors/month) for error tracking, **UptimeRobot free tier** for uptime checks |

Logging all Claude API calls (prompt, response, latency, token count) to a simple table gives you an evaluation dataset for your thesis and lets you show real numbers in your defense slides instead of just "it works."

---

## 9. Suggested build order (phased, executable)

**Phase 1 — Data and core retrieval (1-2 weeks)**
Stand up Postgres + pgvector, load both datasets, generate and store embeddings, build the retrieval query (semantic search + SQL filters) as a standalone, testable function before any agent wraps it.

**Phase 2 — Agent pipeline without booking (1-2 weeks)**
Implement Preference Agent → Retrieval → Crowd Estimator → Recommender Agent → Story Generator as a single API endpoint. Get this working end to end and fast before adding booking complexity.

**Phase 3 — Booking flow (1 week)**
Add the Booking Agent, bookings table, and mock ticket confirmation. Real payment integration can come after the core flow is solid.

**Phase 4 — Frontend polish + deployment (1 week)**
Port your existing prototype UI into the real API, deploy to Railway/Render + Vercel, set up CI/CD.

**Phase 5 — Evaluation + thesis writeup (ongoing)**
Build the evaluation set, log metrics, and write the methodology chapter in parallel with the last two phases rather than after — this is the part most students leave too late.

---

## 10. What this plan deliberately avoids (and why)

- **No fine-tuning.** Your dataset is too small (1,258 rows) to fine-tune anything meaningfully, and prompting + retrieval grounding solves the accuracy problem better for a system this size — also avoids GPU training costs entirely.
- **No separate vector database service.** pgvector on the same free Supabase/Postgres instance is simpler to deploy, debug, explain in a defense, and costs nothing extra, versus a dedicated paid vector DB.
- **No real third-party ticketing API integration in v1.** Egypt's Ministry of Tourism doesn't expose a public booking API — the Booking Agent should be built against your own mock/internal booking table first, with a clear note in your writeup that real ticketing integration is future work pending partnership access.
- **No paid payment gateway integration.** Paymob/Fawry require business verification and charge transaction fees; simulating the booking confirmation against your own database is the right call for a graduation defense and avoids any business onboarding overhead.
- **No WhatsApp Business API.** It requires a paid Meta business account; free email (Gmail SMTP or Resend's free tier) covers the same "send a confirmation" need without cost.
- **No always-on paid hosting.** Free-tier hosting (Render/Fly.io) with a cold-start delay is a completely acceptable tradeoff for a project whose purpose is demonstration, not production traffic.
- **No paid LLM API.** Qwen2.5 on free HF Inference API / Spaces replaces Claude entirely for this build. This means accepting weaker JSON reliability and somewhat less polished Arabic/English storytelling than a frontier model would produce — addressed with defensive parsing and pre-warmed Spaces (see Section 3) — but it makes the entire pipeline genuinely free, which is the actual goal of this demo build.
