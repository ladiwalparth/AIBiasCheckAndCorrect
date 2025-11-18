from jinja2 import Environment, PackageLoader, select_autoescape
from pydantic_core import from_json
from vertexai.generative_models import ChatSession

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat

from .gemini import GeminiClient
from .model import AnalyzeResult


class BiasAnalyzer:

    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        
        # Load templates from backend/templates/
        self.env = Environment(
            loader=PackageLoader('backend'),
            autoescape=select_autoescape()
        )

        # New dependencies
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    # ------------------------------------------------------------
    # GENDER BIAS SCORING (UNCHANGED)
    # ------------------------------------------------------------
    @staticmethod
    def _calculate_score(analyze_result: AnalyzeResult) -> int:
        stereotyping_score = analyze_result.stereotyping_score
        representation_score = analyze_result.representation_score
        language_score = analyze_result.language_score
        framing_score = analyze_result.framing_score

        base_score = (stereotyping_score + representation_score + language_score + framing_score) / 4

        male_to_female_mention_ratio = analyze_result.male_to_female_mention_ratio
        gender_neutral_language_percentage = analyze_result.gender_neutral_language_percentage

        ratio_boost = 0
        if male_to_female_mention_ratio > 0:
            ratio_difference = abs(1 - male_to_female_mention_ratio)
            ratio_boost = max(0, 30 * (1 - ratio_difference))

        neutral_language_boost = (gender_neutral_language_percentage / 100) * 10

        boosted_score = base_score * (1 + ratio_boost / 100 + neutral_language_boost / 100)

        final_score = int(round(max(1, min(100, boosted_score))))
        return final_score

    # ------------------------------------------------------------
    # TEMPLATE RENDERER — DO NOT TOUCH
    # ------------------------------------------------------------
    def _render_custom_template(self, template_name: str, **kwargs):
        import os
        from jinja2 import Environment, FileSystemLoader

        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(base_dir, "templates")

        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        return template.render(**kwargs)

    # ------------------------------------------------------------
    # NEW 1: Sentiment Analysis
    # ------------------------------------------------------------
    def _compute_sentiment(self, text: str) -> tuple[int, str]:
        score_raw = self.sentiment_analyzer.polarity_scores(text)["compound"]

        # Convert -1..1 → 0..100
        score_0_100 = round((score_raw + 1) * 50)

        # Label
        if score_raw >= 0.35:
            label = "Positive"
        elif score_raw <= -0.35:
            label = "Negative"
        else:
            label = "Neutral"

        return score_0_100, label

    # ------------------------------------------------------------
    # NEW 2: Readability Analysis
    # ------------------------------------------------------------
    def _compute_readability(self, text: str) -> tuple[float, str, str]:
        try:
            score = textstat.flesch_reading_ease(text)
        except:
            score = 50  # fallback mid-value

        if score < 0:
            score = 0
        if score > 100:
            score = 100

        # Assign human-readable category + comment
        if score >= 70:
            level = "Easy"
            comment = "The content is easy to read and suitable for most audiences."
        elif score >= 50:
            level = "Medium"
            comment = "The content has moderate complexity and may require focus."
        else:
            level = "Hard"
            comment = "The content is difficult to read and may need simplification."

        return round(score, 2), level, comment

    # ------------------------------------------------------------
    # MAIN: GENDER BIAS + NEW METRICS ANALYSIS
    # ------------------------------------------------------------
    def analyze(self, text: str) -> AnalyzeResult:
        prompt = self._render_custom_template("analyze.jinja", text=text)

        chat: ChatSession = self.gemini_client.start_chat()
        chat_response: str = self.gemini_client.get_chat_response(chat, prompt)

        analyze_result = AnalyzeResult.model_validate(from_json(chat_response))

        # GENDER BIAS FINAL SCORE
        analyze_result.overall_score = self._calculate_score(analyze_result)

        # SENTIMENT
        s_score, s_label = self._compute_sentiment(text)
        analyze_result.sentiment_score = s_score
        analyze_result.sentiment_label = s_label

        # READABILITY
        r_score, r_level, r_comment = self._compute_readability(text)
        analyze_result.readability_score = r_score
        analyze_result.readability_level = r_level
        analyze_result.readability_comment = r_comment

        return analyze_result

    # ------------------------------------------------------------
    # ENHANCEMENT (UNCHANGED)
    # ------------------------------------------------------------
    def enhance(self, text: str, analyzedResult: AnalyzeResult) -> str:
        prompt = self._render_custom_template("enhance.jinja", text=text, analyzedResult=analyzedResult)
        chat: ChatSession = self.gemini_client.start_chat()
        chat_response: str = self.gemini_client.get_chat_response(chat, prompt)
        return chat_response
    
