// TCG Coach — official Gundam Card Game scraper (facts + tags only).
// Run in a browser tab on https://www.gundam-gcg.com/en/ (same origin).
// Stores NO effect text: only card facts, structured tags derived by fixed
// patterns, FAQ question numbers, and a SHA-256 fingerprint of the effect text.
// Usage (console):  gcgScrape.start();  gcgScrape.progress();  gcgScrape.chunk(0, 150);  gcgScrape.clear()
// Progress is saved in localStorage (key tcgcoach_scrape_v1), so a closed tab resumes where it stopped.
(() => {
  const BASE = '/en/cards/';
  const PACKAGES = {
    '616101': 'GD01', '616102': 'GD02', '616103': 'GD03', '616104': 'GD04', '616105': 'GD05', '616106': 'GD06',
    '616001': 'ST01', '616002': 'ST02', '616003': 'ST03', '616004': 'ST04', '616005': 'ST05', '616006': 'ST06',
    '616007': 'ST07', '616008': 'ST08', '616009': 'ST09', '616010': 'ST10', '616011': 'ST11', '616012': 'ST12',
    '616013': 'ST13', '616014': 'ST14', '616201': 'EB01', '616301': 'SC01', '616701': 'OTHER',
    '616000': 'BETA', '616801': 'BASIC', '616901': 'PROMO',
  };
  const DELAY_MS = 1000; // throttle: about 1 request per second

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const parse = (html) => new DOMParser().parseFromString(html, 'text/html');
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const toNum = (s) => (/^-?\d+$/.test(clean(s)) ? parseInt(clean(s), 10) : null);

  async function sha256(text) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
  }

  // Fixed-pattern tags. Heuristic: an action tag means the phrase appears somewhere in the effect.
  const ACTIONS = [
    ['draw', /\bdraws? \d+|\bdraw \d+/i],
    ['destroy', /\bdestroy/i],
    ['bounce', /to (its|their) owner'?s hand/i],
    ['rest-enemy', /\brest (it|them|\d+ enemy|.{0,40}enemy)/i],
    ['set-active', /set (it|them|.{0,30}) as active/i],
    ['recover-hp', /recovers? \d+ hp/i],
    ['damage', /deals? \d+ damage/i],
    ['ap-up', /gets? \+\d+ ?ap|ap\s?\+\d+/i],
    ['hp-up', /gets? \+\d+ ?hp|hp\s?\+\d+/i],
    ['ap-down', /gets? -\d+ ?ap|ap\s?-\d+/i],
    ['search-deck', /look at the top|search your deck|reveal .{0,30}deck/i],
    ['add-to-hand', /add .{0,60} to your hand/i],
    ['discard', /\bdiscard/i],
    ['exile', /\bexile/i],
    ['from-trash', /from your trash/i],
    ['token', /\btoken/i],
    ['shield', /\bshield/i],
    ['resource', /\bresource/i],
    ['deploy-other', /\bdeploy (it|1|a|that)|\bdeploy .{0,30} from/i],
    ['pair-link', /\bpair|\blink/i],
    ['cant-attack-block', /can'?t (attack|block|choose)/i],
    ['self-mill', /(top|place) .{0,40} (into|in) your trash/i],
  ];

  function tagsFrom(text) {
    const triggers = [...new Set([...text.matchAll(/【([^】]+)】/g)].map((m) => clean(m[1])))];
    const keywords = [...new Set([...text.matchAll(/<([^<>]{2,30})>/g)].map((m) => clean(m[1])))];
    const actions = ACTIONS.filter(([, re]) => re.test(text)).map(([t]) => t);
    return { triggers, keywords, actions };
  }

  async function listIds(pkg) {
    const html = await fetch(`${BASE}index.php?search=true&package=${pkg}`).then((r) => r.text());
    return [...new Set([...html.matchAll(/detailSearch=([^"&]+)/g)].map((m) => m[1]))];
  }

  async function detail(id) {
    const d = parse(await fetch(`${BASE}detail.php?detailSearch=${encodeURIComponent(id)}`).then((r) => r.text()));
    const fields = {};
    d.querySelectorAll('dl.dataBox').forEach((dl) => {
      const k = clean(dl.querySelector('.dataTit')?.textContent);
      if (k) fields[k] = clean(dl.querySelector('.dataTxt')?.textContent);
    });
    const effEl = d.querySelector('.cardDataRow.overview .dataTxt');
    // textContent decodes entities, so <Keyword> markers survive; the text itself is never stored.
    const effectText = effEl ? clean(effEl.textContent) : '';
    const faq = [...d.querySelectorAll('.qaCol')].map((q) => ({
      q: clean(q.querySelector('.qaColNum')?.textContent),
      date: clean(q.querySelector('.qaColDate span')?.textContent),
    }));
    const split = (s, re) => (s ? s.match(re) || [] : []).map((x) => clean(x));
    return {
      no: clean(d.querySelector('.cardNo')?.textContent) || id,
      name: clean(d.querySelector('.cardName')?.textContent),
      rarity: clean(d.querySelector('.rarity')?.textContent),
      block: toNum(d.querySelector('.blockIcon')?.textContent),
      type: fields['TYPE'] || null,
      color: fields['COLOR'] && fields['COLOR'] !== '-' ? fields['COLOR'] : null,
      lv: toNum(fields['Lv.']),
      cost: toNum(fields['COST']),
      ap: toNum(fields['AP']),
      hp: toNum(fields['HP']),
      zone: fields['Zone'] && fields['Zone'] !== '-' ? fields['Zone'].split(' ') : [],
      traits: split(fields['Trait'], /\(([^)]+)\)/g).map((t) => t.replace(/[()]/g, '')),
      link: split(fields['Link'], /\[([^\]]+)\]/g).map((t) => t.replace(/[[\]]/g, '')),
      source_title: fields['Source Title'] || null,
      where: fields['Where to get it'] || null,
      has_effect: effectText.length > 0 && effectText !== '-',
      ...tagsFrom(effectText),
      text_hash: effectText ? await sha256(effectText) : null,
      faq,
      url: `https://www.gundam-gcg.com/en/cards/detail.php?detailSearch=${encodeURIComponent(id)}`,
    };
  }

  const STORE = 'tcgcoach_scrape_v1';
  const WORKERS = 2; // two requests in flight, each followed by DELAY_MS: about 1-2 requests per second
  const saved = (() => { try { return JSON.parse(localStorage.getItem(STORE) || '{}'); } catch (e) { return {}; } })();
  const state = { running: false, done: 0, total: 0, errors: [], cards: saved.cards || {}, started: null };
  const persist = () => { try { localStorage.setItem(STORE, JSON.stringify({ cards: state.cards })); } catch (e) { /* storage full or blocked */ } };

  async function run() {
    const membership = {}; // base no -> {groups:Set, prints:Set}
    state.phase = 'lists';
    for (const [pkg, code] of Object.entries(PACKAGES)) {
      for (const id of await listIds(pkg)) {
        const baseNo = id.replace(/_p\d+$/i, '');
        membership[baseNo] ??= { groups: new Set(), prints: new Set() };
        membership[baseNo].groups.add(code);
        membership[baseNo].prints.add(id);
      }
      await sleep(DELAY_MS);
    }
    const ids = Object.keys(membership);
    state.total = ids.length;
    state.phase = 'details';
    const queue = ids.filter((no) => !state.cards[no]);
    state.done = ids.length - queue.length;
    const worker = async () => {
      while (queue.length) {
        const no = queue.shift();
        try {
          const c = await detail(no);
          c.no = no;
          c.groups = [...membership[no].groups];
          c.prints = [...membership[no].prints];
          state.cards[no] = c;
        } catch (e) {
          state.errors.push(`${no}: ${e.message}`);
          const tries = state.errors.filter((x) => x.startsWith(`${no}:`)).length;
          if (tries < 3) queue.push(no); // retry later, at most 3 attempts
          await sleep(5000);
        }
        state.done = Object.keys(state.cards).length;
        if (state.done % 25 === 0) persist();
        await sleep(DELAY_MS);
      }
    };
    await Promise.all(Array.from({ length: WORKERS }, worker));
    persist();
    state.phase = 'finished';
    state.running = false;
    state.finished = new Date().toISOString();
  }

  function start() {
    if (state.running) return 'already running';
    state.running = true; state.started = new Date().toISOString();
    run().catch((e) => { state.errors.push(`run: ${e.message}`); state.running = false; });
    return 'started';
  }

  const progress = () => ({ phase: state.phase, running: state.running, done: state.done, total: state.total, errors: state.errors.length, started: state.started, finished: state.finished || null });
  // insertion order is stable, so chunks can be pulled while the scrape runs
  const chunk = (from, n) => JSON.stringify(Object.values(state.cards).slice(from, from + n));
  const clear = () => { localStorage.removeItem(STORE); return 'cleared'; };

  window.gcgScrape = { start, progress, chunk, detail, clear, state };
})();
