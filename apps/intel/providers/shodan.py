NAME = "shodan"
def enrich(value, ioc_type):
    # TODO: call Shodan with API key from env
    data = {"example":"replace_with_shodan_response"}
    score = 0.7  # 0..1
    return data, score
