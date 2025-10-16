WEIGHTS = {'vt':0.35,'otx':0.25,'greynoise':0.2,'shodan':0.1,'heuristics':0.1}
def score_ioc(enrichments):  # list of {'source':..., 'score':...}
    s = 0.0
    for e in enrichments:
        s += WEIGHTS.get(e['source'], 0) * e.get('score', 0)
    return round(min(s*100, 100), 1)
