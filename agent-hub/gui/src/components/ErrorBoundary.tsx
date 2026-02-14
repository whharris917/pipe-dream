import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary] Uncaught error:", error, info.componentStack);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            background: "#1a1a2e",
            color: "#e0e0e0",
            fontFamily: "monospace",
            padding: "2rem",
          }}
        >
          <h1 style={{ color: "#ff6b6b", marginBottom: "1rem" }}>
            Something went wrong
          </h1>
          <pre
            style={{
              background: "#16213e",
              padding: "1rem",
              borderRadius: "4px",
              maxWidth: "600px",
              overflow: "auto",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              marginBottom: "1.5rem",
            }}
          >
            {this.state.error?.message || "Unknown error"}
          </pre>
          <button
            onClick={this.handleReload}
            style={{
              background: "#0f3460",
              color: "#e0e0e0",
              border: "1px solid #533483",
              padding: "0.5rem 1.5rem",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "1rem",
              fontFamily: "monospace",
            }}
          >
            Reload
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
