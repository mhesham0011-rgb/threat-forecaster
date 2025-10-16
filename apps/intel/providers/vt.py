NAME = "vt"
def enrich(value, ioc_type):
    # TODO: call VirusTotal with API key from env
    data = {"example":"replace_with_vt_response"}
    score = 0.7  # 0..1
    return data, score
