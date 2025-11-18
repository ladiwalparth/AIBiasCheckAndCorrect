from fastapi import FastAPI
import logging
from functools import lru_cache
from cachetools import TTLCache
from .config import Settings
from .gemini import GeminiClient
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials

from .bias import BiasAnalyzer
from .parse import WebParser

import logging
from functools import lru_cache

from fastapi import HTTPException, status

from .model import AnalyzeRequest, AnalyzeResponse, AnalyzeResult


#setting up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('main.log')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)



@lru_cache
def get_settings() -> Settings:
    return Settings()

settings: Settings = get_settings()

credentials: Credentials = service_account.Credentials.from_service_account_file(settings.gcp_service_account_file)

gemini_client: GeminiClient = GeminiClient(
    settings.gcp_project_id,
    settings.gcp_location,
    credentials,
    settings.gcp_gemini_model
)

gemini_client2: GeminiClient = GeminiClient(
    settings.gcp_project_id,
    settings.gcp_location,
    credentials,
    settings.gcp_gemini_model2
)

bias_analyzer: BiasAnalyzer = BiasAnalyzer(gemini_client)
bias_analyzer2: BiasAnalyzer = BiasAnalyzer(gemini_client2)

web_parser: WebParser = WebParser(settings.parse_max_content_length, settings.parse_chunk_size, use_selenium=False)


app: FastAPI = FastAPI()

result_cache: TTLCache = TTLCache(maxsize=settings.cache_size, ttl=settings.cache_ttl)
enhanced_result_cache: TTLCache = TTLCache(maxsize=settings.cache_size, ttl=settings.cache_ttl)
pro_version_analysis: TTLCache = TTLCache(maxsize=settings.cache_size, ttl=settings.cache_ttl)

@app.post('/analyze')
def analyze(analyze_request: AnalyzeRequest) -> AnalyzeResponse:
    # try to use cached result
    cached_result = result_cache.get(analyze_request.uri)

    # --- FIX OLD CACHE ITEMS THAT DO NOT HAVE NEW FIELDS ---
    if cached_result:
        result = cached_result.result
        if (
            not hasattr(result, "sentiment_score")
            or not hasattr(result, "readability_score")
            or not hasattr(result, "readability_level")
        ):
            logger.info("Old cached item detected — ignoring cache for %s", analyze_request.uri)
            cached_result = None

    # If still valid, return cached result
    if cached_result:
        logger.info('Returning cached result for %s', analyze_request.uri)
        return cached_result



    logger.info('Analyzing %s', analyze_request.uri)
    text = web_parser.parse(analyze_request.uri)

    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Could not parse page')

    try:
        result = bias_analyzer2.analyze(text)
        response = AnalyzeResponse(uri=analyze_request.uri, result=result)
        result_cache[analyze_request.uri] = response
        return response
    
    except Exception as e:
        logger.exception("Failed to analyze %s: %s", analyze_request.uri, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Could not analyze page')

@app.post('/ParsedText')
def scrape(analyze_request: AnalyzeRequest) -> str:
    logger.info(f"Analyzing {analyze_request.uri}")

    # If user wants to use selenium, override the flag
    web_parser.use_selenium = analyze_request.use_selenium

    # Call the updated parse() method
    text = web_parser.parse(analyze_request.uri)

    if not text:
        logger.warning(f"Failed to extract text from {analyze_request.uri}")
        return "No text could be extracted from the given URL."

    return text

@app.post('/EnhancedText')
def enhance(analyze_response: AnalyzeResponse) -> str:
     # try to use cached result
    enhanced_cached_result = enhanced_result_cache.get(analyze_response.uri)

    if enhanced_cached_result:
        logger.info('Returning enhanced_cached result for %s', analyze_response.uri)
        return enhanced_cached_result


    logger.info('Enhancing %s', analyze_response.uri)
    text = web_parser.parse(analyze_response.uri)

    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Could not parse page')

    try:
        # logger.info(text)
        # logger.info(analyze_response.result)
        result = bias_analyzer2.enhance(text,analyze_response.result)
        enhanced_result_cache[analyze_response.uri] = result
        return result
    
    except Exception as e:
        logger.exception("Failed to analyze %s: %s", analyze_response.uri, str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Could not analyze page')

@app.post('/analyzeEnhancedUsingModel2')
def analyze(text: str) -> AnalyzeResult:
    # try to use cached result
    stored_output = pro_version_analysis.get(text)

    if stored_output:
        logger.info('Returning cached result for the Query')
        return stored_output


    logger.info('Analyzing the Enhanced text version using a Pro Model')

    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter text to analyze')

    try:
        result = bias_analyzer.analyze(text)
        pro_version_analysis[text] = result
        return result
    
    except Exception as e:
        logger.exception("Failed to analyze.... %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Could not analyze page')
