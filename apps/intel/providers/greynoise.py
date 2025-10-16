NAME = "greynoise"
def enrich(value, ioc_type):
    # TODO: call GreyNoise with API key from env
    data = {"example":"replace_with_greynoise_response"}
    score = 0.7  # 0..1
    return data, score
