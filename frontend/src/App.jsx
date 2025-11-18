import { useState } from "react";

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultType, setResultType] = useState("");
  const [useSelenium, setUseSelenium] = useState(false); // NEW

  const backend = "http://127.0.0.1:8000";

  async function handleRequest(type) {
    if (!url) return alert("Please enter a URL first!");

    setLoading(true);
    setResult(null);
    setResultType(type);

    try {
      let response;

      const bodyData = JSON.stringify({
        uri: url,
        use_selenium: useSelenium,
      });

      if (type === "parse") {
        response = await fetch(`${backend}/ParsedText`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: bodyData,
        });
        const text = await response.text();
        setResult(text);
      }

      if (type === "analyze") {
        response = await fetch(`${backend}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: bodyData,
        });
        const data = await response.json();
        setResult(data.result);
      }

      if (type === "enhance") {
        const analyzeFirst = await fetch(`${backend}/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: bodyData,
        });

        const analyzed = await analyzeFirst.json();

        response = await fetch(`${backend}/EnhancedText`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(analyzed),
        });

        const enhancedText = await response.text();
        setResult(enhancedText);
      }

      if (type === "analyzeEnhanced") {
        const parseEnhanced = await fetch(`${backend}/analyzeEnhancedUsingModel2`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: url }),
        });

        const data = await parseEnhanced.json();
        setResult(data);
      }
    } catch (err) {
      console.log(err);
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
    <div
      className="min-h-screen p-6 flex flex-col justify-center items-center
                 bg-gradient-to-br from-black via-slate-900 to-blue-900"
    >
      <h1 className="text-4xl font-extrabold mb-6 
                     bg-gradient-to-r from-gray-300 via-gray-100 to-white
                     text-transparent bg-clip-text">
        Bias • Sentiment • Readability AI
      </h1>

      <div className="w-full max-w-2xl bg-white/10 backdrop-blur-lg shadow-xl rounded-xl p-6 border border-gray-700">
        
        {/* URL INPUT */}
        <input
          type="text"
          placeholder="Enter webpage URL..."
          className="w-full p-3 rounded-lg 
             bg-gray-300 text-gray-900 placeholder-gray-500
             shadow-inner border border-gray-300
             focus:bg-white focus:ring-2 focus:ring-blue-400 transition mb-4"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        {/* SELENIUM TOGGLE */}
        <div className="flex items-center mb-5">
          <label className="text-gray-200 mr-3 font-semibold">
            Use Selenium
          </label>
          <input
            type="checkbox"
            checked={useSelenium}
            onChange={() => setUseSelenium(!useSelenium)}
            className="w-5 h-5 accent-blue-500"
          />
        </div>

        {/* BUTTONS */}
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

        {loading && (
          <p className="text-center text-gray-300 animate-pulse">Loading...</p>
        )}

        {/* RESULT VIEW */}
        {result && (
          <div className="mt-6 p-5 bg-white/20 backdrop-blur-md rounded-xl shadow-inner text-gray-100">
            <h2 className="text-xl font-bold mb-3 text-gray-50">
              Result: {resultType.toUpperCase()}
            </h2>

            {typeof result === "string" && (
              <p className="whitespace-pre-wrap leading-relaxed">{result}</p>
            )}

            {typeof result === "object" && (
              <div className="space-y-6">

                <div className="p-5 bg-white/20 rounded-xl shadow-md border border-gray-600">
                  <h3 className="text-xl font-bold text-blue-200 mb-2">Summary</h3>
                  <p>{result.summary}</p>
                  <p className="mt-2"><strong>Overall Score:</strong> {result.overall_score}</p>
                </div>

                <div className="p-5 bg-white/10 rounded-xl shadow-md border border-gray-600">
                  <h3 className="text-lg font-semibold text-purple-300 mb-2">Stereotyping</h3>
                  <p><strong>Feedback:</strong> {result.stereotyping_feedback}</p>
                  <p><strong>Score:</strong> {result.stereotyping_score}</p>
                  <p><strong>Example:</strong> {result.stereotyping_example}</p>
                </div>

                <div className="p-5 bg-white/10 rounded-xl shadow-md border border-gray-600">
                  <h3 className="text-lg font-semibold text-purple-300 mb-2">Representation</h3>
                  <p><strong>Feedback:</strong> {result.representation_feedback}</p>
                  <p><strong>Score:</strong> {result.representation_score}</p>
                  <p><strong>Example:</strong> {result.representation_example}</p>
                </div>

                <div className="p-5 bg-white/10 rounded-xl shadow-md border border-gray-600">
                  <h3 className="text-lg font-semibold text-purple-300 mb-2">Language</h3>
                  <p><strong>Feedback:</strong> {result.language_feedback}</p>
                  <p><strong>Score:</strong> {result.language_score}</p>
                  <p><strong>Example:</strong> {result.language_example}</p>
                </div>

                <div className="p-5 bg-white/10 rounded-xl shadow-md border border-gray-600">
                  <h3 className="text-lg font-semibold text-purple-300 mb-2">Framing</h3>
                  <p><strong>Feedback:</strong> {result.framing_feedback}</p>
                  <p><strong>Score:</strong> {result.framing_score}</p>
                  <p><strong>Example:</strong> {result.framing_example}</p>
                </div>

                <div className="p-5 bg-white/10 rounded-xl shadow-md border border-gray-600">
                  <h3 className="text-lg font-semibold text-yellow-300 mb-2">Sentiment Analysis</h3>
                  <p><strong>Sentiment Score:</strong> {result.sentiment_score}</p>
                  <p><strong>Label:</strong> {result.sentiment_label}</p>
                </div>

                <div className="p-5 bg-white/10 rounded-xl shadow-md border border-gray-600">
                  <h3 className="text-lg font-semibold text-green-300 mb-2">Readability</h3>
                  <p><strong>Ease Score:</strong> {result.readability_score}</p>
                  <p><strong>Level:</strong> {result.readability_level}</p>
                  <p><strong>Comment:</strong> {result.readability_comment}</p>
                </div>

              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
