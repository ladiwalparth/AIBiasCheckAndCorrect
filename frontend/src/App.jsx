import { useState } from "react";

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultType, setResultType] = useState("");

  const backend = "http://127.0.0.1:8000"; // Adjust if needed

  async function handleRequest(type) {
    if (!url && type !== "analyzeEnhanced") {
      return alert("Please enter a URL first!");
    }

    setLoading(true);
    setResult(null);
    setResultType(type);

    try {
      let response;

      // ----------------------------------------------------------
      // 1. PARSE TEXT
      // ----------------------------------------------------------
      if (type === "parse") {
        response = await fetch(`${backend}/ParsedText`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ uri: url, use_selenium: false }),
        });

        const text = await response.text();
        setResult(text);
        window.lastParsed = text;
      }

      // ----------------------------------------------------------
      // 2. ANALYZE BIAS (first model)
      // ----------------------------------------------------------
      if (type === "analyze") {
        response = await fetch(`${backend}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ uri: url, use_selenium: false }),
        });

        const data = await response.json();
        setResult(data.result);

        window.lastAnalyzed = data;
      }

      // ----------------------------------------------------------
      // 3. ENHANCED TEXT (using enhanced.jinja)
      // ----------------------------------------------------------
      if (type === "enhance") {
        // Step 1 → analyze first
        const analyzeFirst = await fetch(`${backend}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ uri: url, use_selenium: false }),
        });

        const analyzed = await analyzeFirst.json();

        // Step 2 → enhance
        response = await fetch(`${backend}/EnhancedText`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(analyzed),
        });

        const enhancedText = await response.text();
        setResult(enhancedText);

        window.lastEnhanced = enhancedText; // Save enhanced result
      }

      // ----------------------------------------------------------
      // 4. ANALYZE ENHANCED TEXT (second model)
      // ----------------------------------------------------------
      if (type === "analyzeEnhanced") {
        if (!window.lastEnhanced) {
          return alert("Please generate 'Enhanced Text' first!");
        }

        response = await fetch(`${backend}/analyzeEnhancedUsingModel2`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: window.lastEnhanced }),
        });

        const data = await response.json();
        setResult(data);
      }
    } catch (err) {
      console.error(err);
      alert("Something went wrong!");
    }

    setLoading(false);
  }

  const buttons = [
    { name: "Parse Text", id: "parse", color: "bg-blue-500" },
    { name: "Analyze Bias", id: "analyze", color: "bg-green-500" },
    { name: "Enhanced Text", id: "enhance", color: "bg-purple-500" },
    { name: "Analyze Enhanced", id: "analyzeEnhanced", color: "bg-red-500" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6 flex flex-col items-center">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">AI Bias Analyzer</h1>

      <div className="w-full max-w-2xl bg-white shadow-lg rounded-xl p-6">
        <input
          type="text"
          placeholder="Enter webpage URL..."
          className="w-full border p-3 rounded-lg text-gray-700 mb-4"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        {/* Buttons */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {buttons.map((btn) => (
            <button
              key={btn.id}
              onClick={() => handleRequest(btn.id)}
              className={`text-white font-semibold py-2 rounded-lg ${btn.color} hover:opacity-90`}
              disabled={loading}
            >
              {btn.name}
            </button>
          ))}
        </div>

        {/* Output Section */}
        {loading && (
          <p className="text-center text-gray-600 animate-pulse">Loading...</p>
        )}

        {result && (
          <div className="mt-6 p-5 bg-gray-100 rounded-xl shadow-inner">
            <h2 className="text-xl font-semibold mb-3 text-gray-800">
              Result: {resultType.toUpperCase()}
            </h2>

            {/* TEXT OUTPUT */}
            {typeof result === "string" && (
              <p className="whitespace-pre-wrap leading-relaxed text-gray-700">
                {result}
              </p>
            )}

            {/* ANALYSIS OUTPUT */}
            {typeof result === "object" && (
              <div className="space-y-3">
                <p>
                  <strong>Summary:</strong> {result.summary}
                </p>
                <p>
                  <strong>Overall Score:</strong> {result.overall_score}
                </p>

                <div className="border-t pt-3 mt-3">
                  <h3 className="font-semibold">Detailed Feedback</h3>
                  <p><strong>Stereotyping:</strong> {result.stereotyping_feedback}</p>
                  <p><strong>Representation:</strong> {result.representation_feedback}</p>
                  <p><strong>Language:</strong> {result.language_feedback}</p>
                  <p><strong>Framing:</strong> {result.framing_feedback}</p>
                </div>

                {/* Sentiment & Readability */}
                <div className="border-t pt-3 mt-3">
                  <h3 className="font-semibold">Sentiment</h3>
                  <p><strong>Label:</strong> {result.sentiment_label}</p>
                  <p><strong>Score:</strong> {result.sentiment_score}</p>

                  <h3 className="font-semibold mt-3">Readability</h3>
                  <p><strong>Ease Score:</strong> {result.readability_score}</p>
                  <p><strong>Level:</strong> {result.readability_level}</p>
                  <p><strong>Notes:</strong> {result.readability_comment}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
