import React from "react";
import SyntaxHighlighter from "react-syntax-highlighter/dist/cjs/prism-light";
import python from "react-syntax-highlighter/dist/cjs/languages/prism/python";
import java from "react-syntax-highlighter/dist/cjs/languages/prism/java";
import diff from "react-syntax-highlighter/dist/cjs/languages/prism/diff";
import vscDarkPlus from "react-syntax-highlighter/dist/cjs/styles/prism/vsc-dark-plus";

SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("java", java);
SyntaxHighlighter.registerLanguage("diff", diff);

function CodeBlockComponent({ code, language = "python", isStreaming = false }) {
  if (isStreaming) {
    return (
      <div className="syntax-wrap">
        <pre className="code-raw streaming-code" style={{ margin: 0, padding: 16, minHeight: 120 }}>
          {code || ""}
          <span className="pulseDot" style={{ display: "inline-block", marginLeft: 4, verticalAlign: "middle" }} />
        </pre>
      </div>
    );
  }

  return (
    <div className="syntax-wrap">
      <SyntaxHighlighter language={language} style={vscDarkPlus} wrapLongLines>
        {code || ""}
      </SyntaxHighlighter>
    </div>
  );
}

export default React.memo(CodeBlockComponent);
